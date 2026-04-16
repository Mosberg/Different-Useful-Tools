# Author: Mosberg
# Github: https://github.com/Mosberg

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                              QVBoxLayout, QHBoxLayout, QFileDialog, QLabel,
                              QSpinBox, QScrollArea, QGridLayout, QMessageBox)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PIL import Image


class SpriteSheetGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.loaded_images = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Spritesheet Generator V1')
        self.setGeometry(100, 100, 900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Control panel
        control_layout = QHBoxLayout()

        self.select_btn = QPushButton('Select PNG Images')
        self.select_btn.clicked.connect(self.select_images)
        control_layout.addWidget(self.select_btn)

        control_layout.addWidget(QLabel('Columns:'))
        self.columns_spinbox = QSpinBox()
        self.columns_spinbox.setMinimum(1)
        self.columns_spinbox.setMaximum(20)
        self.columns_spinbox.setValue(4)
        self.columns_spinbox.valueChanged.connect(self.update_preview)
        control_layout.addWidget(self.columns_spinbox)

        self.generate_btn = QPushButton('Generate Preview')
        self.generate_btn.clicked.connect(self.update_preview)
        self.generate_btn.setEnabled(False)
        control_layout.addWidget(self.generate_btn)

        self.save_btn = QPushButton('Save Spritesheet')
        self.save_btn.clicked.connect(self.save_spritesheet)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)

        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # Info label
        self.info_label = QLabel('No images selected')
        main_layout.addWidget(self.info_label)

        # Preview area
        preview_label = QLabel('Preview:')
        preview_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        main_layout.addWidget(preview_label)

        # Scroll area for preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)

        self.preview_widget = QLabel()
        self.preview_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_widget.setText('Preview will appear here')
        self.preview_widget.setStyleSheet('background-color: #f0f0f0; border: 2px dashed #999;')

        scroll_area.setWidget(self.preview_widget)
        main_layout.addWidget(scroll_area)

    def select_images(self):
        file_filter = 'PNG Images (*.png)'
        files, _ = QFileDialog.getOpenFileNames(
            self,
            'Select PNG Images',
            os.getcwd(),
            file_filter
        )

        if files:
            self.image_paths = files
            self.info_label.setText(f'Selected {len(files)} image(s)')
            self.generate_btn.setEnabled(True)
            self.update_preview()

    def update_preview(self):
        if not self.image_paths:
            return

        try:
            # Load images with PIL
            self.loaded_images = [Image.open(path).convert('RGBA') for path in self.image_paths]

            # Get max dimensions
            max_width = max(img.width for img in self.loaded_images)
            max_height = max(img.height for img in self.loaded_images)

            # Calculate spritesheet dimensions
            columns = self.columns_spinbox.value()
            rows = (len(self.loaded_images) + columns - 1) // columns

            spritesheet_width = max_width * columns
            spritesheet_height = max_height * rows

            # Create spritesheet
            spritesheet = Image.new('RGBA', (spritesheet_width, spritesheet_height), (0, 0, 0, 0))

            # Paste images
            for idx, img in enumerate(self.loaded_images):
                col = idx % columns
                row = idx // columns
                x = col * max_width
                y = row * max_height
                spritesheet.paste(img, (x, y))

            # Convert PIL Image to QPixmap for preview
            self.current_spritesheet = spritesheet
            spritesheet_bytes = spritesheet.tobytes('raw', 'RGBA')
            qimage = QImage(spritesheet_bytes, spritesheet_width, spritesheet_height,
                           spritesheet_width * 4, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)

            # Scale preview if too large
            if pixmap.width() > 800 or pixmap.height() > 600:
                pixmap = pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)

            self.preview_widget.setPixmap(pixmap)
            self.preview_widget.setText('')
            self.save_btn.setEnabled(True)

            self.info_label.setText(
                f'Loaded {len(self.loaded_images)} images | '
                f'Spritesheet size: {spritesheet_width}x{spritesheet_height}px | '
                f'Grid: {columns}x{rows}'
            )

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to generate preview:\n{str(e)}')

    def save_spritesheet(self):
        if not hasattr(self, 'current_spritesheet'):
            return

        file_filter = 'PNG Image (*.png);;All Files (*)'
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Spritesheet',
            'spritesheet.png',
            file_filter
        )

        if file_path:
            try:
                self.current_spritesheet.save(file_path)
                QMessageBox.information(self, 'Success', f'Spritesheet saved to:\n{file_path}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save spritesheet:\n{str(e)}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = SpritesheetGenerator()
    window.show()
    sys.exit(app.exec())
