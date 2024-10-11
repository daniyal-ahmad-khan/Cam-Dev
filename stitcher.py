# stitcher.py
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import cv2
import numpy as np
from frame_stitcher import FrameStitcher
import logging
import traceback

# Configure logging
logging.basicConfig(
    filename='video_stitcher.log',
    level=logging.ERROR,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

class VideoStitcher(QThread):
    frame_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)  # Signal to emit error messages

    def __init__(self, camera_feeds, settings):
        super(VideoStitcher, self).__init__()
        self.camera_feeds = camera_feeds
        self.settings = settings
        self.is_running = True
        self.stitcher = None
        try:
            frames = []
            for cap in self.camera_feeds:
                if cap and cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        frames.append(frame)
                    else:
                        logging.warning("Failed to read frame from a camera feed. Using black frame as fallback.")
                        frames.append(np.zeros((480, 640, 3), dtype=np.uint8))  # Black frame
                else:
                    logging.warning("Camera feed is not opened. Using black frame as fallback.")
                    frames.append(np.zeros((480, 640, 3), dtype=np.uint8))  # Black frame
            # print("settings", settings)
            self.stitcher = FrameStitcher(frames, **settings)
        except Exception as e:
            logging.error("Error during VideoStitcher initialization.", exc_info=True)
            self.error_occurred.emit(f"Initialization error: {str(e)}")
            self.stitcher = None  # Ensure stitcher is set to None to avoid further errors

    def run(self):
        # while self.is_running:
        if not self.is_running:
            return  # Avoid running the loop if the stitcher is stopped 
        
        
        try:
            frames = []
            for cap in self.camera_feeds:
                if cap and cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        frames.append(frame)
                    else:
                        logging.warning("Failed to read frame from a camera feed. Using black frame as fallback.")
                        frames.append(np.zeros((480, 640, 3), dtype=np.uint8))  # Black frame
                else:
                    logging.warning("Camera feed is not opened. Using black frame as fallback.")
                    frames.append(np.zeros((480, 640, 3), dtype=np.uint8))  # Black frame

            if frames and self.stitcher:
                try:
                    stitched_frame = self.stitcher.stitch_frames(frames)
                    if stitched_frame is not None:
                        self.frame_ready.emit(stitched_frame)
                    else:
                        logging.error("Stitcher returned None.")
                        # self.error_occurred.emit("Stitcher returned an invalid frame.")
                except Exception as e:
                    logging.error("Error during frame stitching.", exc_info=True)
                    # self.error_occurred.emit(f"Stitching error: {str(e)}")
            else:
                logging.error("No frames to stitch or stitcher not initialized.")
                # self.error_occurred.emit("No frames to stitch or stitcher not initialized.")
        except Exception as e:
            logging.error("Unexpected error in VideoStitcher run loop.", exc_info=True)
            # self.error_occurred.emit(f"Unexpected error: {str(e)}")
            # Depending on the severity, you might choose to stop the thread
            # self.is_running = False

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()
        # Release all camera feeds
        # for cap in self.camera_feeds:
        #     if cap and cap.isOpened():
        #         cap.release()
