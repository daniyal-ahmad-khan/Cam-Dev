# camera_manager.py
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import cv2
import logging
import threading

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
        camera_indices = [0, 2, 4]  # Update as needed
        for idx in camera_indices:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                self.workers[idx] = cap
                logging.info(f"Camera {idx} initialized.")
            else:
                logging.warning(f"Failed to initialize camera {idx}.")
                self.workers[idx] = None


