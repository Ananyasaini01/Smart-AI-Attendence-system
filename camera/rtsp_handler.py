# camera/rtsp_handler.py
import cv2
import threading
import time
from queue import Queue
import logging

logger = logging.getLogger(__name__)

class RTSPCameraHandler:
    def __init__(self, camera_config):
        self.camera_id = camera_config['id']
        self.rtsp_url = camera_config['rtsp_url']
        self.location = camera_config['location']
        self.cap = None
        self.is_running = False
        self.last_frame = None
        self.fps = 0
        self._frame_count = 0
        self._start_time = time.time()
        self._lock = threading.Lock()
        self._capture_thread = None

    def connect(self):
        try:
            if str(self.rtsp_url).isdigit():
                self.cap = cv2.VideoCapture(int(self.rtsp_url), cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(self.rtsp_url)
            
            if self.cap.isOpened():
                logger.info(f"✅ Camera {self.camera_id} connected!")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Camera error: {e}")
            return False

    def start_capture(self):
        self.is_running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def _capture_loop(self):
        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(1)
                self.connect()
                continue
            
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
            
            self._frame_count += 1
            elapsed = time.time() - self._start_time
            if elapsed >= 1.0:
                self.fps = self._frame_count / elapsed
                self._frame_count = 0
                self._start_time = time.time()
            
            with self._lock:
                self.last_frame = frame.copy()

    def get_frame(self):
        with self._lock:
            return self.last_frame.copy() if self.last_frame is not None else None

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()

class MultiCameraManager:
    def __init__(self, camera_configs):
        self.cameras = {cfg['id']: RTSPCameraHandler(cfg) for cfg in camera_configs}

    def start_all(self):
        for handler in self.cameras.values():
            if handler.connect():
                handler.start_capture()

    def get_frame(self, camera_id):
        return self.cameras[camera_id].get_frame() if camera_id in self.cameras else None

    def stop_all(self):
        for handler in self.cameras.values():
            handler.stop()