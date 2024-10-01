# single_camera_canvas.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QMessageBox, QApplication
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from camera_manager import CameraManager
import logging
import cv2

class SingleCameraCanvas(QWidget):
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.init_ui()
        self.camera_manager = CameraManager()
        self.frame_generator = self.camera_manager.workers[self.camera_index].frames()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fetch_frame)
        self.timer.start(30)  # Adjust interval as needed for framerate
        self.setWindowTitle(f"Camera {self.camera_index}")
        logging.info(f"SingleCameraCanvas initialized for camera {self.camera_index}")

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.camera_dropdown = QComboBox()
        self.camera_dropdown.setFixedWidth(200)
        self.populate_cameras()
        self.camera_dropdown.setCurrentIndex(self.camera_index)
        self.camera_dropdown.currentIndexChanged.connect(self.change_camera)
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.layout.addWidget(self.camera_dropdown, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.video_label)
        self.setLayout(self.layout)

    def populate_cameras(self):
        try:
            # Populate with available camera indices
            camera_list = [str(i) for i in self.camera_manager.find_available_cameras(max_index=35)]
            self.camera_dropdown.addItems(camera_list)
        except Exception as e:
            logging.error("Error populating camera list.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to populate camera list: {str(e)}")

    def change_camera(self):
        selected_index = int(self.camera_dropdown.currentText())
        if selected_index == self.camera_index:
            return  # No change

        logging.info(f"Switching from camera {self.camera_index} to {selected_index}")
        self.camera_index = selected_index
        self.frame_generator = self.camera_manager.workers[self.camera_index].frames()
        self.timer.start(30)

    @pyqtSlot(int, object)
    def receive_frame(self, camera_index, frame):
        try:
            frame = next(self.frame_generator)
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                self.video_label.setPixmap(QPixmap.fromImage(image))
        except StopIteration:
            logging.warning("No more frames to fetch.")
            self.timer.stop()
        except Exception as e:
            logging.error("Error fetching or displaying frame.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to process frame: {str(e)}")