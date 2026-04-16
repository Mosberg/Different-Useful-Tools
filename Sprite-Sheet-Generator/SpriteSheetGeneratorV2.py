# Author: Mosberg
# Github: https://github.com/Mosberg

import sys
import os
import json
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                              QVBoxLayout, QHBoxLayout, QFileDialog, QLabel,
                              QSpinBox, QScrollArea, QMessageBox, QListWidget,
                              QGroupBox, QCheckBox, QComboBox, QSlider,
                              QSplitter, QLineEdit, QProgressBar, QMenuBar,
                              QMenu, QTabWidget, QDoubleSpinBox)
from PyQt6.QtGui import QPixmap, QImage, QAction, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QMimeData
from PIL import Image, ImageDraw, ImageFont


class SpritesheetWorker(QThread):
    """Worker thread for generating spritesheet to prevent UI freezing"""
    finished = pyqtSignal(object, int, int)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, image_paths, config):
        super().__init__()
        self.image_paths = image_paths
        self.config = config

    def run(self):
        try:
            images = []
            total = len(self.image_paths)

            # Load images
            for idx, path in enumerate(self.image_paths):
                img = Image.open(path).convert('RGBA')

                # Resize if needed
                if self.config['resize_enabled']:
                    img = img.resize(
                        (self.config['sprite_width'], self.config['sprite_height']),
                        Image.Resampling.LANCZOS
                    )

                images.append(img)
                self.progress.emit(int((idx + 1) / total * 50))

            # Calculate dimensions
            if self.config['uniform_size']:
                max_width = self.config['sprite_width'] if self.config['resize_enabled'] else max(img.width for img in images)
                max_height = self.config['sprite_height'] if self.config['resize_enabled'] else max(img.height for img in images)
            else:
                max_width = max(img.width for img in images)
                max_height = max(img.height for img in images)

            columns = self.config['columns']
            rows = (len(images) + columns - 1) // columns

            # Add padding
            padding = self.config['padding']
            sprite_padding = self.config['sprite_padding']

            cell_width = max_width + sprite_padding * 2
            cell_height = max_height + sprite_padding * 2

            spritesheet_width = cell_width * columns + padding * 2
            spritesheet_height = cell_height * rows + padding * 2

            # Create spritesheet with background
            bg_color = self.config['bg_color']
            spritesheet = Image.new('RGBA', (spritesheet_width, spritesheet_height), bg_color)

            # Add grid lines if enabled
            if self.config['show_grid']:
                draw = ImageDraw.Draw(spritesheet)
                grid_color = self.config['grid_color']
                for i in range(columns + 1):
                    x = padding + i * cell_width
                    draw.line([(x, 0), (x, spritesheet_height)], fill=grid_color, width=1)
                for i in range(rows + 1):
                    y = padding + i * cell_height
                    draw.line([(0, y), (spritesheet_width, y)], fill=grid_color, width=1)

            # Paste images
            for idx, img in enumerate(images):
                col = idx % columns
                row = idx // columns

                # Center image in cell
                x = padding + col * cell_width + sprite_padding
                y = padding + row * cell_height + sprite_padding

                if self.config['center_sprites']:
                    x += (max_width - img.width) // 2
                    y += (max_height - img.height) // 2

                spritesheet.paste(img, (x, y), img if img.mode == 'RGBA' else None)

                # Add index labels
                if self.config['show_indices']:
                    draw = ImageDraw.Draw(spritesheet)
                    try:
                        font = ImageFont.truetype("arial.ttf", 12)
                    except:
                        font = ImageFont.load_default()
                    draw.text((x + 2, y + 2), str(idx), fill=(255, 255, 0, 255), font=font)

                self.progress.emit(50 + int((idx + 1) / total * 50))

            self.finished.emit(spritesheet, spritesheet_width, spritesheet_height)

        except Exception as e:
            self.error.emit(str(e))


class SpritesheetGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.current_spritesheet = None
        self.worker = None

        # Settings
        self.settings = QSettings('SpritesheetGenerator', 'Config')

        self.initUI()
        self.load_settings()

    def initUI(self):
        self.setWindowTitle('Advanced Spritesheet Generator V2')
        self.setGeometry(100, 100, 1200, 800)

        # Menu Bar
        self.create_menu_bar()

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Panel - Controls
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)

        # Right Panel - Preview
        right_panel = self.create_preview_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('&File')

        open_action = QAction('&Open Images...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.select_images)
        file_menu.addAction(open_action)

        save_action = QAction('&Save Spritesheet...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_spritesheet)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        export_config_action = QAction('Export &Configuration...', self)
        export_config_action.triggered.connect(self.export_config)
        file_menu.addAction(export_config_action)

        import_config_action = QAction('&Import Configuration...', self)
        import_config_action.triggered.connect(self.import_config)
        file_menu.addAction(import_config_action)

        file_menu.addSeparator()

        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu('&Edit')

        clear_action = QAction('&Clear All Images', self)
        clear_action.triggered.connect(self.clear_images)
        edit_menu.addAction(clear_action)

        remove_action = QAction('&Remove Selected', self)
        remove_action.setShortcut('Delete')
        remove_action.triggered.connect(self.remove_selected_images)
        edit_menu.addAction(remove_action)

        # Help Menu
        help_menu = menubar.addMenu('&Help')

        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_control_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # File Selection Group
        file_group = QGroupBox("Image Selection")
        file_layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.select_btn = QPushButton('Select Images')
        self.select_btn.clicked.connect(self.select_images)
        btn_layout.addWidget(self.select_btn)

        self.clear_btn = QPushButton('Clear')
        self.clear_btn.clicked.connect(self.clear_images)
        btn_layout.addWidget(self.clear_btn)

        file_layout.addLayout(btn_layout)

        drop_label = QLabel('or drag and drop PNG files here')
        drop_label.setStyleSheet('color: #666; font-style: italic;')
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_layout.addWidget(drop_label)

        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        file_layout.addWidget(self.image_list)

        self.info_label = QLabel('No images loaded')
        file_layout.addWidget(self.info_label)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Settings Tabs
        tabs = QTabWidget()

        # Layout Tab
        layout_tab = QWidget()
        layout_form = QVBoxLayout(layout_tab)

        grid_layout = QHBoxLayout()
        grid_layout.addWidget(QLabel('Columns:'))
        self.columns_spinbox = QSpinBox()
        self.columns_spinbox.setMinimum(1)
        self.columns_spinbox.setMaximum(50)
        self.columns_spinbox.setValue(4)
        grid_layout.addWidget(self.columns_spinbox)
        layout_form.addLayout(grid_layout)

        self.auto_columns_check = QCheckBox('Auto-calculate optimal columns')
        layout_form.addWidget(self.auto_columns_check)

        padding_layout = QHBoxLayout()
        padding_layout.addWidget(QLabel('Border Padding:'))
        self.padding_spinbox = QSpinBox()
        self.padding_spinbox.setMinimum(0)
        self.padding_spinbox.setMaximum(100)
        self.padding_spinbox.setValue(0)
        padding_layout.addWidget(self.padding_spinbox)
        layout_form.addLayout(padding_layout)

        sprite_padding_layout = QHBoxLayout()
        sprite_padding_layout.addWidget(QLabel('Sprite Padding:'))
        self.sprite_padding_spinbox = QSpinBox()
        self.sprite_padding_spinbox.setMinimum(0)
        self.sprite_padding_spinbox.setMaximum(100)
        self.sprite_padding_spinbox.setValue(2)
        sprite_padding_layout.addWidget(self.sprite_padding_spinbox)
        layout_form.addLayout(sprite_padding_layout)

        self.center_sprites_check = QCheckBox('Center sprites in cells')
        self.center_sprites_check.setChecked(True)
        layout_form.addWidget(self.center_sprites_check)

        self.uniform_size_check = QCheckBox('Use uniform cell size')
        self.uniform_size_check.setChecked(True)
        layout_form.addWidget(self.uniform_size_check)

        layout_form.addStretch()
        tabs.addTab(layout_tab, "Layout")

        # Sprite Tab
        sprite_tab = QWidget()
        sprite_form = QVBoxLayout(sprite_tab)

        self.resize_check = QCheckBox('Resize all sprites')
        self.resize_check.toggled.connect(self.toggle_resize_options)
        sprite_form.addWidget(self.resize_check)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel('Width:'))
        self.sprite_width_spinbox = QSpinBox()
        self.sprite_width_spinbox.setMinimum(1)
        self.sprite_width_spinbox.setMaximum(4096)
        self.sprite_width_spinbox.setValue(64)
        self.sprite_width_spinbox.setEnabled(False)
        size_layout.addWidget(self.sprite_width_spinbox)

        size_layout.addWidget(QLabel('Height:'))
        self.sprite_height_spinbox = QSpinBox()
        self.sprite_height_spinbox.setMinimum(1)
        self.sprite_height_spinbox.setMaximum(4096)
        self.sprite_height_spinbox.setValue(64)
        self.sprite_height_spinbox.setEnabled(False)
        size_layout.addWidget(self.sprite_height_spinbox)
        sprite_form.addLayout(size_layout)

        self.maintain_aspect_check = QCheckBox('Maintain aspect ratio')
        self.maintain_aspect_check.setEnabled(False)
        sprite_form.addWidget(self.maintain_aspect_check)

        sprite_form.addStretch()
        tabs.addTab(sprite_tab, "Sprites")

        # Visual Tab
        visual_tab = QWidget()
        visual_form = QVBoxLayout(visual_tab)

        self.show_grid_check = QCheckBox('Show grid lines')
        visual_form.addWidget(self.show_grid_check)

        self.show_indices_check = QCheckBox('Show sprite indices')
        visual_form.addWidget(self.show_indices_check)

        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel('Background:'))
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(['Transparent', 'White', 'Black', 'Gray'])
        bg_layout.addWidget(self.bg_combo)
        visual_form.addLayout(bg_layout)

        visual_form.addStretch()
        tabs.addTab(visual_tab, "Visual")

        # Export Tab
        export_tab = QWidget()
        export_form = QVBoxLayout(export_tab)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel('Format:'))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['PNG', 'WebP', 'JPEG'])
        format_layout.addWidget(self.format_combo)
        export_form.addLayout(format_layout)

        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel('Quality:'))
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(95)
        quality_layout.addWidget(self.quality_slider)
        self.quality_label = QLabel('95')
        self.quality_slider.valueChanged.connect(lambda v: self.quality_label.setText(str(v)))
        quality_layout.addWidget(self.quality_label)
        export_form.addLayout(quality_layout)

        self.export_metadata_check = QCheckBox('Export metadata JSON')
        self.export_metadata_check.setChecked(True)
        export_form.addWidget(self.export_metadata_check)

        self.optimize_check = QCheckBox('Optimize file size')
        self.optimize_check.setChecked(True)
        export_form.addWidget(self.optimize_check)

        export_form.addStretch()
        tabs.addTab(export_tab, "Export")

        layout.addWidget(tabs)

        # Generate Button
        self.generate_btn = QPushButton('Generate Preview')
        self.generate_btn.clicked.connect(self.update_preview)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setStyleSheet('QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }')
        layout.addWidget(self.generate_btn)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return panel

    def create_preview_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Preview Controls
        control_layout = QHBoxLayout()

        self.zoom_label = QLabel('Zoom: 100%')
        control_layout.addWidget(self.zoom_label)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        control_layout.addWidget(self.zoom_slider)

        control_layout.addStretch()

        self.save_btn = QPushButton('Save Spritesheet')
        self.save_btn.clicked.connect(self.save_spritesheet)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet('QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }')
        control_layout.addWidget(self.save_btn)

        layout.addLayout(control_layout)

        # Preview Info
        self.preview_info_label = QLabel('No preview generated')
        self.preview_info_label.setStyleSheet('font-weight: bold; padding: 5px;')
        layout.addWidget(self.preview_info_label)

        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet('background-color: #2b2b2b;')

        self.preview_widget = QLabel()
        self.preview_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_widget.setText('Preview will appear here\n\nDrag and drop PNG files or click "Select Images"')
        self.preview_widget.setStyleSheet('background-color: #2b2b2b; color: #888; border: 2px dashed #555; font-size: 14px;')
        self.preview_widget.setMinimumSize(400, 400)

        scroll_area.setWidget(self.preview_widget)
        layout.addWidget(scroll_area)

        return panel

    def toggle_resize_options(self, enabled):
        self.sprite_width_spinbox.setEnabled(enabled)
        self.sprite_height_spinbox.setEnabled(enabled)
        self.maintain_aspect_check.setEnabled(enabled)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        png_files = [f for f in files if f.lower().endswith('.png')]

        if png_files:
            # Add to existing list
            self.image_paths.extend(png_files)
            self.image_paths = list(dict.fromkeys(self.image_paths))  # Remove duplicates
            self.update_image_list()
            self.generate_btn.setEnabled(True)
            event.accept()
        else:
            QMessageBox.warning(self, 'Invalid Files', 'Please drop PNG image files.')
            event.ignore()

    def select_images(self):
        file_filter = 'PNG Images (*.png);;All Images (*.png *.jpg *.jpeg *.bmp)'
        files, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Images',
            self.settings.value('last_directory', os.getcwd()),
            file_filter
        )

        if files:
            self.settings.setValue('last_directory', os.path.dirname(files[0]))
            self.image_paths.extend(files)
            self.image_paths = list(dict.fromkeys(self.image_paths))  # Remove duplicates
            self.update_image_list()
            self.generate_btn.setEnabled(True)

    def update_image_list(self):
        self.image_list.clear()
        for path in self.image_paths:
            self.image_list.addItem(os.path.basename(path))
        self.info_label.setText(f'{len(self.image_paths)} image(s) loaded')

    def clear_images(self):
        self.image_paths = []
        self.image_list.clear()
        self.info_label.setText('No images loaded')
        self.generate_btn.setEnabled(False)
        self.save_btn.setEnabled(False)

    def remove_selected_images(self):
        selected_items = self.image_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            index = self.image_list.row(item)
            del self.image_paths[index]

        self.update_image_list()

        if not self.image_paths:
            self.generate_btn.setEnabled(False)
            self.save_btn.setEnabled(False)

    def get_config(self):
        bg_colors = {
            'Transparent': (0, 0, 0, 0),
            'White': (255, 255, 255, 255),
            'Black': (0, 0, 0, 255),
            'Gray': (128, 128, 128, 255)
        }

        columns = self.columns_spinbox.value()
        if self.auto_columns_check.isChecked():
            # Auto-calculate optimal columns (try to make square-ish)
            import math
            columns = math.ceil(math.sqrt(len(self.image_paths)))

        return {
            'columns': columns,
            'padding': self.padding_spinbox.value(),
            'sprite_padding': self.sprite_padding_spinbox.value(),
            'resize_enabled': self.resize_check.isChecked(),
            'sprite_width': self.sprite_width_spinbox.value(),
            'sprite_height': self.sprite_height_spinbox.value(),
            'uniform_size': self.uniform_size_check.isChecked(),
            'center_sprites': self.center_sprites_check.isChecked(),
            'show_grid': self.show_grid_check.isChecked(),
            'show_indices': self.show_indices_check.isChecked(),
            'bg_color': bg_colors[self.bg_combo.currentText()],
            'grid_color': (100, 100, 100, 128)
        }

    def update_preview(self):
        if not self.image_paths:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.generate_btn.setEnabled(False)

        config = self.get_config()

        self.worker = SpritesheetWorker(self.image_paths, config)
        self.worker.finished.connect(self.on_preview_finished)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.error.connect(self.on_preview_error)
        self.worker.start()

    def on_preview_finished(self, spritesheet, width, height):
        self.current_spritesheet = spritesheet

        # Convert to QPixmap
        spritesheet_bytes = spritesheet.tobytes('raw', 'RGBA')
        qimage = QImage(spritesheet_bytes, width, height,
                       width * 4, QImage.Format.Format_RGBA8888)
        self.original_pixmap = QPixmap.fromImage(qimage)

        self.update_zoom()

        self.preview_info_label.setText(
            f'Spritesheet: {width}x{height}px | '
            f'Sprites: {len(self.image_paths)} | '
            f'Grid: {self.get_config()["columns"]}×{(len(self.image_paths) + self.get_config()["columns"] - 1) // self.get_config()["columns"]}'
        )

        self.save_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_preview_error(self, error_msg):
        QMessageBox.critical(self, 'Error', f'Failed to generate preview:\n{error_msg}')
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

    def update_zoom(self):
        if not hasattr(self, 'original_pixmap'):
            return

        zoom = self.zoom_slider.value()
        self.zoom_label.setText(f'Zoom: {zoom}%')

        scaled_pixmap = self.original_pixmap.scaled(
            self.original_pixmap.width() * zoom // 100,
            self.original_pixmap.height() * zoom // 100,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.preview_widget.setPixmap(scaled_pixmap)
        self.preview_widget.setText('')

    def save_spritesheet(self):
        if not self.current_spritesheet:
            return

        format_ext = {
            'PNG': '.png',
            'WebP': '.webp',
            'JPEG': '.jpg'
        }

        ext = format_ext[self.format_combo.currentText()]
        file_filter = f'{self.format_combo.currentText()} Image (*{ext});;All Files (*)'

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Spritesheet',
            self.settings.value('last_save_directory', f'spritesheet{ext}'),
            file_filter
        )

        if file_path:
            try:
                self.settings.setValue('last_save_directory', os.path.dirname(file_path))

                # Save image
                save_kwargs = {}
                if self.format_combo.currentText() in ['WebP', 'JPEG']:
                    save_kwargs['quality'] = self.quality_slider.value()
                if self.optimize_check.isChecked():
                    save_kwargs['optimize'] = True

                if self.format_combo.currentText() == 'JPEG':
                    # Convert to RGB for JPEG
                    rgb_image = Image.new('RGB', self.current_spritesheet.size, (255, 255, 255))
                    rgb_image.paste(self.current_spritesheet, mask=self.current_spritesheet.split()[3])
                    rgb_image.save(file_path, **save_kwargs)
                else:
                    self.current_spritesheet.save(file_path, **save_kwargs)

                # Save metadata
                if self.export_metadata_check.isChecked():
                    self.save_metadata(file_path)

                QMessageBox.information(self, 'Success', f'Spritesheet saved to:\n{file_path}')

            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save spritesheet:\n{str(e)}')

    def save_metadata(self, image_path):
        """Save metadata JSON with sprite positions and dimensions"""
        config = self.get_config()

        # Calculate sprite positions
        images = [Image.open(path) for path in self.image_paths]

        if config['uniform_size']:
            if config['resize_enabled']:
                max_width = config['sprite_width']
                max_height = config['sprite_height']
            else:
                max_width = max(img.width for img in images)
                max_height = max(img.height for img in images)
        else:
            max_width = max(img.width for img in images)
            max_height = max(img.height for img in images)

        padding = config['padding']
        sprite_padding = config['sprite_padding']
        cell_width = max_width + sprite_padding * 2
        cell_height = max_height + sprite_padding * 2
        columns = config['columns']

        metadata = {
            'version': '1.0',
            'spritesheet': {
                'width': self.current_spritesheet.width,
                'height': self.current_spritesheet.height,
                'columns': columns,
                'rows': (len(images) + columns - 1) // columns
            },
            'sprites': []
        }

        for idx, img_path in enumerate(self.image_paths):
            col = idx % columns
            row = idx // columns

            x = padding + col * cell_width + sprite_padding
            y = padding + row * cell_height + sprite_padding

            sprite_info = {
                'index': idx,
                'name': os.path.basename(img_path),
                'x': x,
                'y': y,
                'width': images[idx].width,
                'height': images[idx].height
            }

            metadata['sprites'].append(sprite_info)

        json_path = os.path.splitext(image_path)[0] + '.json'
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def export_config(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Export Configuration',
            'spritesheet_config.json',
            'JSON Files (*.json)'
        )

        if file_path:
            config = self.get_config()
            config['bg_color'] = list(config['bg_color'])  # Convert tuple to list for JSON
            config['grid_color'] = list(config['grid_color'])

            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)

            QMessageBox.information(self, 'Success', 'Configuration exported successfully')

    def import_config(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Import Configuration',
            '',
            'JSON Files (*.json)'
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)

                self.columns_spinbox.setValue(config.get('columns', 4))
                self.padding_spinbox.setValue(config.get('padding', 0))
                self.sprite_padding_spinbox.setValue(config.get('sprite_padding', 2))
                self.resize_check.setChecked(config.get('resize_enabled', False))
                self.sprite_width_spinbox.setValue(config.get('sprite_width', 64))
                self.sprite_height_spinbox.setValue(config.get('sprite_height', 64))

                QMessageBox.information(self, 'Success', 'Configuration imported successfully')

            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to import configuration:\n{str(e)}')

    def show_about(self):
        QMessageBox.about(
            self,
            'About Spritesheet Generator',
            '<h3>Advanced Spritesheet Generator</h3>'
            '<p>Version 2.0</p>'
            '<p>Create professional spritesheets with advanced features:</p>'
            '<ul>'
            '<li>Drag & drop support</li>'
            '<li>Customizable layouts and padding</li>'
            '<li>Grid visualization and sprite indices</li>'
            '<li>Multiple export formats</li>'
            '<li>Metadata JSON export</li>'
            '<li>Configuration import/export</li>'
            '</ul>'
        )

    def save_settings(self):
        """Save application settings"""
        self.settings.setValue('columns', self.columns_spinbox.value())
        self.settings.setValue('padding', self.padding_spinbox.value())
        self.settings.setValue('sprite_padding', self.sprite_padding_spinbox.value())
        self.settings.setValue('format', self.format_combo.currentText())
        self.settings.setValue('quality', self.quality_slider.value())
        self.settings.setValue('export_metadata', self.export_metadata_check.isChecked())
        self.settings.setValue('geometry', self.saveGeometry())

    def load_settings(self):
        """Load application settings"""
        self.columns_spinbox.setValue(int(self.settings.value('columns', 4)))
        self.padding_spinbox.setValue(int(self.settings.value('padding', 0)))
        self.sprite_padding_spinbox.setValue(int(self.settings.value('sprite_padding', 2)))

        format_text = self.settings.value('format', 'PNG')
        index = self.format_combo.findText(format_text)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)

        self.quality_slider.setValue(int(self.settings.value('quality', 95)))
        self.export_metadata_check.setChecked(self.settings.value('export_metadata', True, type=bool))

        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        """Save settings on close"""
        self.save_settings()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName('Spritesheet Generator')
    app.setOrganizationName('SpritesheetGenerator')
    window = SpritesheetGenerator()
    window.show()
    sys.exit(app.exec())
