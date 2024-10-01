# video_sync_manager.py
from PyQt5.QtCore import QTimer

class VideoSyncManager:
    def __init__(self, camera_canvases):
        self.camera_canvases = camera_canvases
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)  # Update frames every 30ms

    def update_frames(self):
        for canvas in self.camera_canvases:
            canvas.update_frame()