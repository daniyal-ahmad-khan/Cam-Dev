# camera_manager.py
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import cv2
import logging
import threading

class CameraWorker(QThread):
    frame_captured = pyqtSignal(int, object)  # camera_index, frame

    def __init__(self, camera_index):
        super().__init__()
        self.camera_index = camera_index
        self.capture = None
        self.running = False

    def run(self):
        try:
            self.capture = cv2.VideoCapture(self.camera_index)
            if not self.capture.isOpened():
                logging.warning(f"Failed to open camera {self.camera_index}.")
                return

            self.running = True
            while self.running:
                ret, frame = self.capture.read()
                if ret:
                    self.frame_captured.emit(self.camera_index, frame)
                else:
                    logging.warning(f"Camera {self.camera_index} failed to read frame. Reinitializing.")
                    self.capture.release()
                    self.capture = cv2.VideoCapture(self.camera_index)
        except Exception as e:
            logging.error(f"Error in CameraWorker for camera {self.camera_index}: {e}", exc_info=True)
        finally:
            if self.capture and self.capture.isOpened():
                self.capture.release()

    def stop(self):
        self.running = False
        self.wait()


class CameraManager(QObject):
    # Signal to emit frames: camera_index, frame
    frame_updated = pyqtSignal(int, object)

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self.workers = {}
        self.init_cameras()
        self._initialized = True


    def find_available_cameras(max_index=10):
        # List to hold the indices of available cameras
        available_cameras = []

        # Try to open each camera index from 0 to max_index
        for index in range(max_index):
            # Attempt to create a video capture object
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # If the camera is available, add the index to the list
                available_cameras.append(index)
                # Release the camera device
                cap.release()
            else:
                print(f"Camera at index {index} is not available.")

        return available_cameras
    
    
    def init_cameras(self):
        # Initialize workers for desired camera indices
        camera_indices = self.find_available_cameras(max_index=30)  # Update as needed
        for idx in camera_indices:
            self.add_camera(idx)

    def add_camera(self, camera_index):
        if camera_index in self.workers:
            logging.info(f"Camera {camera_index} is already managed.")
            return
        worker = CameraWorker(camera_index)
        worker.frame_captured.connect(self.handle_frame)
        self.workers[camera_index] = worker
        worker.start()
        logging.info(f"Started CameraWorker for camera {camera_index}.")

    def remove_camera(self, camera_index):
        if camera_index in self.workers:
            worker = self.workers.pop(camera_index)
            worker.stop()
            logging.info(f"Stopped CameraWorker for camera {camera_index}.")
        else:
            logging.warning(f"Tried to remove unmanaged camera {camera_index}.")

    @pyqtSlot(int, object)
    def handle_frame(self, camera_index, frame):
        self.frame_updated.emit(camera_index, frame)

    def release_all(self):
        for camera_index in list(self.workers.keys()):
            self.remove_camera(camera_index)
