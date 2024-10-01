# single_camera_canvas.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QMessageBox
import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSignal, Qt
import logging

class SingleCameraCanvas(QWidget):
    camera_selection_changed = pyqtSignal(int, str)  # args: canvas index, selected camera

    def __init__(self, camera_index=0, canvas_index=0, all_cameras=[]):
        super().__init__()
        self.canvas_index = canvas_index
        self.all_cameras = all_cameras
        self.capture = None
        self.init_ui()
        self.camera_dropdown.setCurrentIndex(camera_index)
        self.change_camera()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.camera_dropdown = QComboBox()
        self.camera_dropdown.setFixedWidth(200)
        self.populate_cameras()
        self.camera_dropdown.currentIndexChanged.connect(self.on_camera_selection_changed)
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.layout.addWidget(self.camera_dropdown, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.video_label)
        self.setLayout(self.layout)

    def populate_cameras(self):
        try:
            self.camera_dropdown.addItems(self.all_cameras)
        except Exception as e:
            logging.error("Error populating camera list.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to populate camera list: {str(e)}")

    def on_camera_selection_changed(self):
        selected_camera = self.camera_dropdown.currentText()
        self.camera_selection_changed.emit(self.canvas_index, selected_camera)

    def enable_dropdown(self):
        self.camera_dropdown.setEnabled(True)

    def disable_dropdown(self):
        self.camera_dropdown.setEnabled(False)

    def release_camera(self):
        if self.capture:
            self.capture.release()
            self.capture = None

    def change_camera(self):
        try:
            camera_device_index = self.camera_dropdown.currentText()
            if self.capture:
                self.capture.release()
            # Attempt to convert to integer for camera indices, fallback to file path
            try:
                device_index = int(camera_device_index)
                self.capture = cv2.VideoCapture(device_index)
            except ValueError:
                self.capture = cv2.VideoCapture(camera_device_index)
        except Exception as e:
            logging.error("Error changing camera.", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to change camera: {str(e)}")

    def update_frame(self):
        try:
            if self.capture and self.capture.isOpened():
                ret, frame = self.capture.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = QImage(
                        frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888
                    )
                    self.video_label.setPixmap(QPixmap.fromImage(image))
                else:
                    self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                pass  # Keep the last frame displayed
        except Exception as e:
            logging.error("Error updating camera frame.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to update camera frame: {str(e)}")