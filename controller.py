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
        self.viewers = [self.main_window.stitched_video_viewer]  # Initialize with the main viewer
        self.timer = None  # Initialize the timer
        logging.info("Controller initialized")

    def connect_signals(self):
        logging.info("Connecting signals")
        self.main_window.stitch_button.clicked.connect(self.start_stitching)

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

            if self.timer and self.timer.isActive():
                self.timer.stop()
                self.timer = None

            # Initialize and start the stitcher thread
            self.stitcher = VideoStitcher(camera_feeds, settings)

            self.clear_viewers()

            # Connect the frame_ready signal to update_stitched_video
            self.stitcher.frame_ready.connect(self.update_stitched_video)

            # Connect the error_occurred signal to handle_stitcher_error
            self.stitcher.error_occurred.connect(self.handle_stitcher_error)

            # Initialize and start the timer if not already started
            if not self.timer:
                self.timer = QTimer()
                self.timer.timeout.connect(self.stitcher.run)
                self.timer.start(30)  # Adjust the interval as needed

            logging.info("VideoStitcher started")
        except Exception as e:
            logging.error("Error in start_stitching.", exc_info=True)
            QMessageBox.critical(self.main_window, "Error", f"Failed to start stitching: {str(e)}")

    @pyqtSlot(object)
    def update_stitched_video(self, frame):
        """
        Dispatch the stitched frame to all connected viewers.
        """
        for viewer in self.viewers:
            viewer.display_video(frame)

    @pyqtSlot(str)
    def handle_stitcher_error(self, error_message):
        logging.error(f"Stitcher Error: {error_message}")
        QMessageBox.critical(self.main_window, "Stitcher Error", error_message)
        # Optionally, stop the stitcher if a critical error occurred
        if self.stitcher and self.stitcher.is_running:
            self.stitcher.stop()
            self.stitcher = None
        if self.timer and self.timer.isActive():
            self.timer.stop()
            self.timer = None

    def connect_fullscreen_viewer(self, viewer):
        """
        Add a fullscreen viewer to the list of active viewers.
        """
        if viewer not in self.viewers:
            self.viewers.append(viewer)
            logging.info("Fullscreen viewer connected to controller.")

    def disconnect_fullscreen_viewer(self, viewer):
        """
        Remove a fullscreen viewer from the list of active viewers.
        """
        if viewer in self.viewers:
            self.viewers.remove(viewer)
            logging.info("Fullscreen viewer disconnected from controller.")

    def stop(self):
        """
        Stop the stitcher and clean up resources.
        """
        try:
            if self.stitcher and self.stitcher.is_running:
                self.stitcher.stop()
                self.stitcher = None
                logging.info("VideoStitcher stopped.")
            if self.timer and self.timer.isActive():
                self.timer.stop()
                self.timer = None
                logging.info("Timer stopped.")
        except Exception as e:
            logging.error("Error stopping the stitcher.", exc_info=True)

    def clear_viewers(self):
        """
        Clear the video viewers to reset their content.
        """
        for viewer in self.viewers:
            viewer.clear()
