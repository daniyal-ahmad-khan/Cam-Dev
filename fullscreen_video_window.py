# fullscreen_video_window.py

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt
import logging

class FullscreenVideoWindow(QMainWindow):
    def __init__(self, stitched_video_viewer, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fullscreen Stitched Video")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.stitched_video_viewer = stitched_video_viewer
        self.setCentralWidget(self.stitched_video_viewer)
        
        # Connect the fullscreen request signal to exit fullscreen
        self.stitched_video_viewer.fullscreen_requested.connect(self.close_fullscreen)
        
        self.showFullScreen()

    def close_fullscreen(self):
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        try:
            # Optional: Emit a signal or perform actions upon closing fullscreen
            logging.info("Exiting fullscreen mode.")
            event.accept()
        except Exception as e:
            logging.error("Error during fullscreen window close.", exc_info=True)
            event.accept()
