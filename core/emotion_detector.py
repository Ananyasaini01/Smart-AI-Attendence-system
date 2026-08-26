# core/emotion_detector.py
import cv2
import numpy as np

class EmotionDetector:
    def __init__(self, config):
        self.config = config
        try:
            import mediapipe as mp
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=10,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
            self.available = True
        except Exception:
            self.available = False

    def detect_emotion(self, frame, face_bbox):
        if not self.available:
            return {'emotion': 'neutral', 'confidence': 0.8}

        x1, y1, x2, y2 = face_bbox
        face_crop = frame[max(0,y1):max(0,y2), max(0,x1):max(0,x2)]
        if face_crop.size == 0:
            return {'emotion': 'neutral', 'confidence': 0.5}

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.face_mesh.process(rgb)

        if not res.multi_face_landmarks:
            return {'emotion': 'neutral', 'confidence': 0.5}

        h, w, _ = frame.shape
        lm = res.multi_face_landmarks[0].landmark

        # Measure lips distance (Smile / Surprise)
        upper = np.array([lm[13].x * w, lm[13].y * h])
        lower = np.array([lm[14].x * w, lm[14].y * h])
        dist = np.linalg.norm(upper - lower)

        if dist > 18:
            return {'emotion': 'surprise', 'confidence': 0.85}
        elif dist > 8:
            return {'emotion': 'happy', 'confidence': 0.9}
        else:
            return {'emotion': 'neutral', 'confidence': 0.75}