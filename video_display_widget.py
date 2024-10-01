# video_display_widget.py

from PyQt5.QtWidgets import QWidget, QGridLayout, QMessageBox
from PyQt5.QtCore import Qt
import cv2
import logging

from single_camera_canvas import SingleCameraCanvas
from video_sync_manager import VideoSyncManager

class VideoDisplayWidget(QWidget):
    def __init__(self, num_cameras):
        super().__init__()
        self.num_cameras = num_cameras
        self.all_cameras = self.detect_available_cameras()
        if len(self.all_cameras) < num_cameras:
            QMessageBox.critical(self, "Error", "Not enough cameras available.")
            self.close()
            return
        self.init_ui()

    def detect_available_cameras(self, max_cameras=10):
        available_cameras = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
            if cap.isOpened():
                available_cameras.append(str(i))
                cap.release()
        if not available_cameras:
            QMessageBox.critical(self, "Error", "No cameras found.")
            self.close()
        return available_cameras

    def init_ui(self):
        self.layout = QGridLayout()
        self.cameras = []
        try:
            grid_columns = 3  # Adjust as needed
            for idx in range(self.num_cameras):
                camera_canvas = SingleCameraCanvas(
                    camera_index=idx % len(self.all_cameras),
                    canvas_index=idx,
                    all_cameras=self.all_cameras,
                )
                camera_canvas.camera_selection_changed.connect(self.on_camera_selection_changed)
                row = idx // grid_columns
                col = idx % grid_columns
                self.layout.addWidget(camera_canvas, row, col)
                self.cameras.append(camera_canvas)

            self.setLayout(self.layout)
            self.sync_manager = VideoSyncManager(self.cameras)
            self.update_dropdown_options()
        except Exception as e:
            logging.error("Error initializing VideoDisplayWidget.", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to initialize video display: {str(e)}")

    def on_camera_selection_changed(self, canvas_index, selected_camera):
        # Release the old camera and open the new one
        self.cameras[canvas_index].release_camera()
        self.cameras[canvas_index].change_camera()
        # Update dropdown options in all canvases
        self.update_dropdown_options()

    def update_dropdown_options(self):
        all_cameras = self.all_cameras
        selected_cameras = [canvas.camera_dropdown.currentText() for canvas in self.cameras]
        for canvas in self.cameras:
            previous_selection = canvas.camera_dropdown.currentText()
            canvas.camera_dropdown.blockSignals(True)
            canvas.camera_dropdown.clear()
            available_cameras = [
                camera
                for camera in all_cameras
                if camera not in selected_cameras or camera == previous_selection
            ]
            canvas.camera_dropdown.addItems(available_cameras)
            canvas.camera_dropdown.setCurrentText(previous_selection)
            canvas.camera_dropdown.blockSignals(False)
