# core/engagement_tracker.py
import cv2
import numpy as np
from collections import deque, defaultdict

class EngagementTracker:
    def __init__(self, config):
        self.config = config
        self.data = defaultdict(lambda: {'drowsy_frames': 0, 'score': 85})

    def track_engagement(self, frame, face_bbox, student_id):
        user_data = self.data[student_id]
        x1, y1, x2, y2 = face_bbox
        face_crop = frame[max(0,y1):max(0,y2), max(0,x1):max(0,x2)]

        # Basic engagement check using head position/size
        score = 85
        drowsy = False

        if face_crop.size > 0:
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            # Eyes closed / too dark
            if np.mean(gray) < 40:
                user_data['drowsy_frames'] += 1
                if user_data['drowsy_frames'] > self.config.DROWSINESS_FRAMES:
                    drowsy = True
                    score -= 40
            else:
                user_data['drowsy_frames'] = max(0, user_data['drowsy_frames'] - 1)

        user_data['score'] = score
        return {
            'score': score,
            'drowsy': drowsy,
            'status': '🟢 Attentive' if score >= 70 else '🔴 Distracted/Drowsy'
        }