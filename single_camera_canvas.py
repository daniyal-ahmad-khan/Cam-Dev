# single_camera_canvas.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QMessageBox
import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSignal, QObject, Qt
import logging

class SingleCameraCanvas(QWidget):
    def __init__(self, camera_index=0):
        super().__init__()
        self.capture = None
        self.init_ui()
        self.camera_dropdown.setCurrentIndex(camera_index)
        self.change_camera()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.camera_dropdown = QComboBox()
        self.camera_dropdown.setFixedWidth(200)
        
        self.populate_cameras()
        self.camera_dropdown.currentIndexChanged.connect(self.change_camera)

        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.layout.addWidget(self.camera_dropdown, alignment=Qt.AlignHCenter)
        self.layout.addWidget(self.video_label)
        self.setLayout(self.layout)

    def populate_cameras(self):
        try:
            # camera_list = [f"/dev/video{i}" for i in range(6)]
            camera_list = ["output0x.mp4", "output1x.mp4", "output2x.mp4"]
            self.camera_dropdown.addItems(camera_list)
        except Exception as e:
            logging.error("Error populating camera list.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to populate camera list: {str(e)}")

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

            if not self.capture.isOpened():
                logging.warning(f"Failed to open camera/video: {camera_device_index}. Using dummy video as fallback.")
                # Use a dummy video if the camera is unavailable
                # Replace 'dummy_video.mp4' with an actual dummy video path or handle accordingly
                self.capture = cv2.VideoCapture('output0x.mp4')  # Replace with an actual dummy video path
                if not self.capture.isOpened():
                    logging.error("Failed to open dummy video.")
                    QMessageBox.critical(self, "Error", "Failed to open both the selected camera/video and the dummy video.")
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
                    # Restart the dummy video when it ends
                    self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        except Exception as e:
            logging.error("Error updating camera frame.", exc_info=True)
            QMessageBox.warning(self, "Warning", f"Failed to update camera frame: {str(e)}")
