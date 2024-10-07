# main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton, QDockWidget,
    QAction, QMessageBox
)
from PyQt5.QtCore import Qt
from camera_selection_dialog import CameraSelectionDialog
from video_display_widget import VideoDisplayWidget
from stitching_settings_panel import StitchingSettingsPanel
from stitched_video_viewer import StitchedVideoViewer
from fullscreen_video_window import FullscreenVideoWindow  # Import the new class
from controller import MainController
import logging

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Stitcher")
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.fullscreen_window = None  # Reference to the fullscreen window
        self.fullscreen_viewer = None
        self.init_ui()
        
        logging.info("MainWindow initialized")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setMinimumSize(800, 600)
        
        # Layouts
        self.layout = QVBoxLayout()
        central_widget.setLayout(self.layout)

        # Stitch Button
        self.stitch_button = QPushButton("Start Stitching")
        self.layout.addWidget(self.stitch_button)

        # Initialize components
        self.video_display_widget = None
        self.stitching_settings_panel = StitchingSettingsPanel()
        self.stitched_video_viewer = StitchedVideoViewer()
        self.controller = MainController(self)

        # Connect the fullscreen request signal to the handler
        self.stitched_video_viewer.fullscreen_requested.connect(self.open_fullscreen)

        # Add stitching settings panel as a dockable widget
        self.settings_dock = QDockWidget("Stitching Settings", self)
        self.settings_dock.setWidget(self.stitching_settings_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.settings_dock)

        # Add action to toggle the settings drawer
        self.toggle_settings_action = QAction("Toggle Settings", self)
        self.toggle_settings_action.triggered.connect(self.toggle_settings_drawer)
        self.menuBar().addAction(self.toggle_settings_action)

        # Start camera selection
        self.start_camera_selection()

    def start_camera_selection(self):
        try:
            camera_dialog = CameraSelectionDialog()
            if camera_dialog.exec_() == camera_dialog.Accepted:
                num_cameras = camera_dialog.get_num_cameras()
                self.video_display_widget = VideoDisplayWidget(num_cameras)
                self.layout.insertWidget(0, self.video_display_widget)
                self.layout.addWidget(self.stitched_video_viewer)
                self.controller.connect_signals()
                logging.info(f"Camera selection successful with {num_cameras} cameras.")
            else:
                logging.info("Camera selection canceled by user.")
                self.close()
        except Exception as e:
            logging.error("Error during camera selection.", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to select cameras: {str(e)}")
            self.close()

    def toggle_settings_drawer(self):
        try:
            visible = self.settings_dock.isVisible()
            self.settings_dock.setVisible(not visible)
        except Exception as e:
            logging.error("Error toggling settings drawer.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to toggle settings drawer: {str(e)}")

    def open_fullscreen(self):
        if not self.fullscreen_window or not self.fullscreen_window.isVisible():
            logging.info("Opening fullscreen window.")
            if not self.fullscreen_viewer:
                self.fullscreen_viewer = StitchedVideoViewer()

            # Ensure connection is active to display videos
            self.controller.connect_fullscreen_viewer(self.fullscreen_viewer)

            if not self.fullscreen_window:
                self.fullscreen_window = FullscreenVideoWindow(self.fullscreen_viewer)
                self.fullscreen_window.destroyed.connect(self.on_fullscreen_closed)
            else:
                # Reset the central widget to handle any state inconsistencies
                self.fullscreen_window.setCentralWidget(self.fullscreen_viewer)
                self.fullscreen_window.showFullScreen()
        else:
            logging.warning("Fullscreen window is already open or visible.")


    def on_fullscreen_closed(self):
        logging.info("Fullscreen window closed.")
        if self.fullscreen_viewer:
            self.controller.disconnect_fullscreen_viewer(self.fullscreen_viewer)
            self.fullscreen_viewer = None
        self.fullscreen_window = None

    def closeEvent(self, event):
        try:
            # Ensure that the stitcher thread is stopped
            if self.controller.stitcher and self.controller.stitcher.isRunning():
                self.controller.stitcher.stop()
            logging.info("Application closed gracefully.")
            event.accept()
        except Exception as e:
            logging.error("Error during application close.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Error during close: {str(e)}")
            event.accept()
