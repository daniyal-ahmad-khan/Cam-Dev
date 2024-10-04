from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
import cv2
import logging

class StitchedVideoViewer(QWidget):
    # Define a custom signal
    fullscreen_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_fullscreen = False
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        # self.video_label.setFixedSize(640, 480)
        self.fullscreen_button = QPushButton("Full Screen")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.layout.addWidget(self.video_label)
        self.layout.addWidget(self.fullscreen_button)
        self.setLayout(self.layout)

    def display_video(self, frame):
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))
        except Exception as e:
            logging.error("Error displaying stitched video frame.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to display stitched video: {str(e)}")

    def toggle_fullscreen(self):
        try:
            # Emit the custom signal instead of trying to toggle fullscreen here
            self.fullscreen_requested.emit()
        except Exception as e:
            logging.error("Error toggling fullscreen.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to toggle fullscreen: {str(e)}")
