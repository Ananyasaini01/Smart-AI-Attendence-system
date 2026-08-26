# core/anti_spoof.py
import cv2
import numpy as np

class AntiSpoofDetector:
    def __init__(self, config):
        self.config = config

    def check_liveness(self, frame, face_bbox):
        x1, y1, x2, y2 = face_bbox
        face_crop = frame[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]

        if face_crop.size == 0:
            return {'is_live': False, 'liveness_score': 0.0, 'reason': 'Face crop invalid'}

        # Texture analysis via Laplacian variance
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        if laplacian_var < 20: # Photo display screens are too smooth
            texture_score = 0.2
        elif laplacian_var > 800: # Overly pixelated / phone screen borders
            texture_score = 0.3
        else:
            texture_score = 0.9

        # Color variance check
        hsv = cv2.cvtColor(face_crop, cv2.COLOR_BGR2HSV)
        _, s, v = cv2.split(hsv)
        color_score = 0.9 if np.std(v) > 20 else 0.4

        liveness_score = (texture_score * 0.6) + (color_score * 0.4)
        is_live = liveness_score >= self.config.LIVENESS_THRESHOLD

        return {
            'is_live': is_live,
            'liveness_score': liveness_score,
            'reason': 'LIVE' if is_live else 'Spoof/Photo detected!'
        }