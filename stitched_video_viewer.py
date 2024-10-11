from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
import cv2
import logging

# stitched_video_viewer.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
import cv2
import logging

class StitchedVideoViewer(QWidget):
    fullscreen_requested = pyqtSignal()  # Signal to request fullscreen

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        
        # Video Display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.video_label)
        
        # Fullscreen Button
        self.fullscreen_button = QPushButton("Full Screen")
        self.fullscreen_button.clicked.connect(self.fullscreen_requested.emit)
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

    def clear(self):
        """
        Clears the currently displayed video frame.
        """
        self.video_label.clear()

    # def toggle_fullscreen(self):
    #     if not self.is_fullscreen:
    #         self.original_state = {
    #             'parent': self.parent(),
    #             'geometry': self.geometry(),
    #             'window_flags': self.windowFlags()
    #         }
    #         self.setParent(None)
    #         self.setWindowFlags(Qt.Window)
    #         self.showFullScreen()
    #         self.is_fullscreen = True
    #     else:
    #         self.setParent(self.original_state['parent'])
    #         self.setWindowFlags(self.original_state['window_flags'])
    #         self.setGeometry(self.original_state['geometry'])
    #         self.showNormal()
    #         self.is_fullscreen = False
