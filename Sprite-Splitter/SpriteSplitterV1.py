# Author: Mosberg
# Github: https://github.com/Mosberg

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QComboBox, QSpinBox, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
import math

class SpriteSplitterThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, image_path, tile_size, output_dir):
        super().__init__()
        self.image_path = image_path
        self.tile_size = tile_size
        self.output_dir = output_dir

    def run(self):
        try:
            # Load image with PIL for better sprite splitting
            img = Image.open(self.image_path)
            width, height = img.size
            
            # Calculate grid dimensions
            cols = math.ceil(width / self.tile_size)
            rows = math.ceil(height / self.tile_size)
            
            total_sprites = cols * rows
            processed = 0
            
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Extract sprites
            base_name = os.path.splitext(os.path.basename(self.image_path))[0]
            
            for row in range(rows):
                for col in range(cols):
                    # Define sprite bounds
                    left = col * self.tile_size
                    top = row * self.tile_size
                    right = min(left + self.tile_size, width)
                    bottom = min(top + self.tile_size, height)
                    
                    # Extract sprite
                    sprite = img.crop((left, top, right, bottom))
                    
                    # Pad to exact size if needed
                    if sprite.size != (self.tile_size, self.tile_size):
                        padded = Image.new('RGBA', (self.tile_size, self.tile_size), (0, 0, 0, 0))
                        padded.paste(sprite, (0, 0))
                        sprite = padded
                    
                    # Save sprite
                    sprite_name = f"{base_name}_sprite_{row:03d}_{col:03d}.png"
                    sprite_path = os.path.join(self.output_dir, sprite_name)
                    sprite.save(sprite_path)
                    
                    processed += 1
                    progress_pct = int((processed / total_sprites) * 100)
                    self.progress.emit(progress_pct)
            
            self.finished.emit(f"Split {total_sprites} sprites into {self.output_dir}")
            
        except Exception as e:
            self.error.emit(str(e))

class SpriteSplitterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sprite Sheet Splitter")
        self.setGeometry(100, 100, 800, 600)
        
        self.image_path = None
        self.current_image = None
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Image display
        self.image_label = QLabel("Load a sprite sheet to begin")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(400)
        self.image_label.setStyleSheet("border: 2px dashed #ccc; background: #f9f9f9;")
        layout.addWidget(self.image_label)
        
        # Controls
        controls = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Sprite Sheet")
        self.load_btn.clicked.connect(self.load_image)
        controls.addWidget(self.load_btn)
        
        controls.addWidget(QLabel("Tile Size:"))
        
        self.size_combo = QComboBox()
        self.size_combo.addItems(["16x16", "32x32", "64x64", "128x128", "256x256"])
        self.size_combo.currentTextChanged.connect(self.update_preview)
        controls.addWidget(self.size_combo)
        
        self.output_btn = QPushButton("Choose Output Folder")
        self.output_btn.clicked.connect(self.choose_output)
        controls.addWidget(self.output_btn)
        
        self.split_btn = QPushButton("Split Sprites")
        self.split_btn.clicked.connect(self.split_sprites)
        self.split_btn.setEnabled(False)
        controls.addWidget(self.split_btn)
        
        self.output_label = QLabel("Output: Not selected")
        controls.addWidget(self.output_label)
        
        layout.addLayout(controls)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
    
    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Sprite Sheet", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        )
        if file_path:
            self.image_path = file_path
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setStyleSheet("")
            self.split_btn.setEnabled(True)
            self.update_preview()
    
    def get_tile_size(self):
        size_text = self.size_combo.currentText()
        return int(size_text.split('x')[0])
    
    def update_preview(self):
        if not self.image_path:
            return
        
        tile_size = self.get_tile_size()
        img = Image.open(self.image_path)
        width, height = img.size
        
        cols = width // tile_size
        rows = height // tile_size
        
        preview_text = f"Preview: {cols}×{rows} grid = {cols*rows} sprites"
        self.status_label.setText(preview_text)
    
    def choose_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Output Folder")
        if folder:
            self.output_dir = folder
            self.output_label.setText(f"Output: {folder}")
            self.split_btn.setEnabled(bool(self.image_path))
    
    def split_sprites(self):
        if not hasattr(self, 'output_dir') or not self.image_path:
            QMessageBox.warning(self, "Error", "Please load an image and choose output folder")
            return
        
        self.split_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        tile_size = self.get_tile_size()
        self.worker = SpriteSplitterThread(self.image_path, tile_size, self.output_dir)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_split_finished)
        self.worker.error.connect(self.on_split_error)
        self.worker.start()
    
    def on_split_finished(self, message):
        self.progress_bar.setVisible(False)
        self.split_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.status_label.setText(message)
        QMessageBox.information(self, "Success", message)
    
    def on_split_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.split_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to split sprites:\n{error_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpriteSplitterApp()
    window.show()
    sys.exit(app.exec())
