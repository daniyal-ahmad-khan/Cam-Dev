# video_display_widget.py
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QMessageBox
from single_camera_canvas import SingleCameraCanvas
from video_sync_manager import VideoSyncManager
import logging
from PyQt5.QtCore import Qt
import cv2

class VideoDisplayWidget(QWidget):
    def __init__(self, num_cameras):
        super().__init__()
        self.num_cameras = num_cameras
        self.all_cameras = self.detect_available_cameras()
        self.changing_cameras = False
        self.init_ui()

    def detect_available_cameras(self, max_cameras=10):
        available_cameras = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
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
            grid_rows = (self.num_cameras + grid_columns - 1) // grid_columns

            for idx in range(self.num_cameras):
                camera_canvas = SingleCameraCanvas(
                    camera_index=idx,
                    canvas_index=idx,
                    all_cameras=self.all_cameras,
                )
                camera_canvas.camera_selection_changed.connect(self.on_camera_selection_changed)
                row = idx // grid_columns
                col = idx % grid_columns
                self.layout.addWidget(camera_canvas, row, col)
                self.cameras.append(camera_canvas)

            self.change_cameras_button = QPushButton("Change Cameras")
            self.change_cameras_button.clicked.connect(self.on_change_cameras)
            self.layout.addWidget(
                self.change_cameras_button, grid_rows, 0, 1, grid_columns, alignment=Qt.AlignCenter
            )

            self.setLayout(self.layout)
            self.sync_manager = VideoSyncManager(self.cameras)
        except Exception as e:
            logging.error("Error initializing VideoDisplayWidget.", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to initialize video display: {str(e)}")

    def on_change_cameras(self):
        if not self.changing_cameras:
            # Start changing cameras
            self.changing_cameras = True
            self.change_cameras_button.setText("Set Cameras")
            for canvas in self.cameras:
                canvas.release_camera()
                canvas.enable_dropdown()
            self.update_dropdown_options()
        else:
            # Finish changing cameras
            self.changing_cameras = False
            self.change_cameras_button.setText("Change Cameras")
            for canvas in self.cameras:
                canvas.disable_dropdown()
                canvas.change_camera()

    def on_camera_selection_changed(self, canvas_index, selected_camera):
        if self.changing_cameras:
            self.update_dropdown_options()

    def update_dropdown_options(self):
        all_cameras = self.all_cameras
        if self.changing_cameras:
            # When changing cameras, show all cameras in dropdowns
            for canvas in self.cameras:
                previous_selection = canvas.camera_dropdown.currentText()
                canvas.camera_dropdown.blockSignals(True)
                canvas.camera_dropdown.clear()
                canvas.camera_dropdown.addItems(all_cameras)
                if previous_selection in all_cameras:
                    canvas.camera_dropdown.setCurrentText(previous_selection)
                else:
                    if all_cameras:
                        canvas.camera_dropdown.setCurrentIndex(0)
                    else:
                        canvas.camera_dropdown.setCurrentText("")
                canvas.camera_dropdown.blockSignals(False)
        else:
            # When not changing cameras, prevent duplicate selections
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
                if previous_selection in available_cameras:
                    canvas.camera_dropdown.setCurrentText(previous_selection)
                else:
                    if available_cameras:
                        canvas.camera_dropdown.setCurrentIndex(0)
                    else:
                        canvas.camera_dropdown.setCurrentText("")
                canvas.camera_dropdown.blockSignals(False)
