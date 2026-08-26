# core/face_detector.py
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FaceDetector:
    def __init__(self, config):
        self.config = config
        self.detector = None
        self._init_detector()

    def _init_detector(self):
        try:
            from insightface.app import FaceAnalysis
            # CPU pe run karega taaki GPU na hone par bhi crash na ho
            self.detector = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            self.detector.prepare(ctx_id=-1, det_size=(640, 640))
            logger.info("✅ InsightFace model successfully loaded!")
        except Exception as e:
            logger.warning(f"InsightFace load nahi hua ({e}). Fallback detector use ho raha hai.")
            self.detector = None
            self.haar = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def detect_faces(self, frame):
        if frame is None:
            return []
        
        results = []
        if self.detector is not None:
            faces = self.detector.get(frame)
            for face in faces:
                if face.det_score < self.config.DETECTION_CONFIDENCE:
                    continue
                bbox = face.bbox.astype(int)
                results.append({
                    'bbox': [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])],
                    'embedding': face.normed_embedding,
                    'score': float(face.det_score),
                    'landmarks': face.kps if hasattr(face, 'kps') else None
                })
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.haar.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                results.append({
                    'bbox': [x, y, x+w, y+h],
                    'embedding': None,
                    'score': 0.8
                })
        return results