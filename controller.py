# controller.py
from stitcher import VideoStitcher
from PyQt5.QtCore import pyqtSlot, QObject, QTimer
from PyQt5.QtWidgets import QMessageBox
import logging

class MainController(QObject):
    def __init__(self, main_window):
        super(MainController, self).__init__()
        self.main_window = main_window
        self.stitcher = None
        logging.info("Controller initialized")

    def connect_signals(self):
        logging.info("Connecting signals")
        self.main_window.stitch_button.clicked.connect(lambda: self.start_stitching())

    @pyqtSlot()
    def start_stitching(self):
        try:
            # Retrieve camera feeds and settings
            camera_feeds = [canvas.capture for canvas in self.main_window.video_display_widget.cameras]
            settings = self.main_window.stitching_settings_panel.get_settings()

            # Stop existing stitcher if running
            if self.stitcher and self.stitcher.is_running:
                self.stitcher.stop()
                self.stitcher = None
                

            # Initialize and start the stitcher thread
            self.stitcher = VideoStitcher(camera_feeds, settings)
            # Connect the frame_ready signal to update_stitched_video
            self.stitcher.frame_ready.connect(self.update_stitched_video)
            self.timer = QTimer()
            self.timer.timeout.connect(self.stitcher.run)
            self.stitcher.error_occurred.connect(self.handle_stitcher_error)
            self.timer.start(30)
            # logging.info("VideoStitcher thread started")
            # self.stitcher.run()
        except Exception as e:
            logging.error("Error in start_stitching.", exc_info=True)
            QMessageBox.critical(self.main_window, "Error", f"Failed to start stitching: {str(e)}")

    @pyqtSlot(object)
    def update_stitched_video(self, frame):
        self.main_window.stitched_video_viewer.display_video(frame)

    @pyqtSlot(str)
    def handle_stitcher_error(self, error_message):
        logging.error(f"Stitcher Error: {error_message}")
        QMessageBox.critical(self.main_window, "Stitcher Error", error_message)
        # Optionally, stop the stitcher if a critical error occurred
        if self.stitcher and self.stitcher.isRunning():
            self.stitcher.stop()
