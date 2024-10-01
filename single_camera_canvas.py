# single_camera_canvas.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot
from camera_manager import CameraManager
import logging
import cv2
class SingleCameraCanvas(QWidget):
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.init_ui()
        self.camera_manager = CameraManager()
        self.camera_manager.frame_updated.connect(self.receive_frame)
        self.setWindowTitle(f"Camera {self.camera_index}")
        logging.info(f"SingleCameraCanvas initialized for camera {self.camera_index}")

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.camera_dropdown = QComboBox()
        self.camera_dropdown.setFixedWidth(200)

        self.populate_cameras()
        self.camera_dropdown.setCurrentText(str(self.camera_index))
        self.camera_dropdown.currentIndexChanged.connect(self.change_camera)

        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.layout.addWidget(self.camera_dropdown, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.video_label)
        self.setLayout(self.layout)

    def populate_cameras(self):
        try:
            # Assuming camera indices are [0,2,4]
            camera_list = [str(i) for i in [0, 2, 4]]
            self.camera_dropdown.addItems(camera_list)
        except Exception as e:
            logging.error("Error populating camera list.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to populate camera list: {str(e)}")

    def change_camera(self):
        try:
            selected_index = int(self.camera_dropdown.currentText())
            if selected_index == self.camera_index:
                return  # No change

            # Disconnect from the current camera
            logging.info(f"Switching from camera {self.camera_index} to {selected_index}")
            self.camera_manager.frame_updated.disconnect(self.receive_frame)

            # Update to the new camera
            self.camera_index = selected_index
            self.camera_manager = CameraManager()  # Singleton ensures the same manager
            self.camera_manager.frame_updated.connect(self.receive_frame)

        except ValueError:
            logging.error("Invalid camera index selected.")
            QMessageBox.warning(self, "Warning", "Selected camera index is invalid.")
        except Exception as e:
            logging.error("Error changing camera.", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to change camera: {str(e)}")

    @pyqtSlot(int, object)
    def receive_frame(self, camera_index, frame):
        if camera_index != self.camera_index:
            return  # Ignore frames from other cameras

        try:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(
                frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888
            )
            self.video_label.setPixmap(QPixmap.fromImage(image))
        except Exception as e:
            logging.error("Error processing received frame.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to process frame: {str(e)}")