# video_display_widget.py
from PyQt5.QtWidgets import QWidget, QGridLayout
from single_camera_canvas import SingleCameraCanvas
from camera_manager import CameraManager
import logging

class VideoDisplayWidget(QWidget):
    def __init__(self, num_cameras):
        super().__init__()
        self.num_cameras = num_cameras
        self.init_ui()

    def init_ui(self):
        self.layout = QGridLayout()
        self.cameras = []
        try:
            grid_columns = 3  # Adjust as needed
            grid_rows = (self.num_cameras + grid_columns - 1) // grid_columns

            for idx in range(self.num_cameras):
                # Assuming camera indices are [0,2,4,...]
                camera_index = [0, 2, 4][idx % 3]  # Adjust based on camera_list
                camera_canvas = SingleCameraCanvas(camera_index=camera_index)
                row = idx // grid_columns
                col = idx % grid_columns
                self.layout.addWidget(camera_canvas, row, col)
                self.cameras.append(camera_canvas)

            self.setLayout(self.layout)

            logging.info(f"VideoDisplayWidget initialized with {self.num_cameras} cameras.")
        except Exception as e:
            logging.error("Error initializing VideoDisplayWidget.", exc_info=True)
