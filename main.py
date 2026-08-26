# main.py
import cv2
import time
import threading
import logging
import argparse

from config import config
from database.db_manager import DatabaseManager
from camera.rtsp_handler import MultiCameraManager
from core.face_detector import FaceDetector
from core.face_recognizer import FaceRecognizer
from core.anti_spoof import AntiSpoofDetector
from core.emotion_detector import EmotionDetector
from core.engagement_tracker import EngagementTracker
from core.proxy_detector import ProxyDetector
from enrollment.student_register import StudentRegistration

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SmartAttendance")

class SmartAttendanceApp:
    def __init__(self):
        logger.info("🚀 AI Smart Attendance System Starting...")
        self.db = DatabaseManager()
        self.cameras = MultiCameraManager(config.CAMERAS)
        self.detector = FaceDetector(config)
        self.recognizer = FaceRecognizer(config, self.db)
        self.anti_spoof = AntiSpoofDetector(config)
        self.emotion = EmotionDetector(config)
        self.engagement = EngagementTracker(config)
        self.proxy = ProxyDetector(config, self.db)
        self.running = False

    def run(self):
        self.cameras.start_all()
        self.running = True
        logger.info("📹 Cameras started! Press 'Q' inside the camera window to Quit.")
        
        while self.running:
            for cam_id in config.CAMERAS:
                cid = cam_id['id']
                frame = self.cameras.get_frame(cid)
                if frame is None:
                    continue

                detections = self.detector.detect_faces(frame)

                for det in detections:
                    x1, y1, x2, y2 = det['bbox']
                    sid, name, conf = self.recognizer.recognize(det.get('embedding'))
                    
                    color = (0, 0, 255) # Red for Unknown
                    label = f"{name} ({conf:.2f})"

                    if sid is not None:
                        color = (0, 255, 0) # Green for Recognized
                        # 1. Anti Spoof
                        liveness = self.anti_spoof.check_liveness(frame, det['bbox'])
                        # 2. Emotion
                        emo = self.emotion.detect_emotion(frame, det['bbox'])
                        # 3. Engagement
                        eng = self.engagement.track_engagement(frame, det['bbox'], sid)

                        if liveness['is_live']:
                            self.db.mark_attendance(sid, cid, conf, liveness['liveness_score'])
                            label += f" | {emo['emotion']} | Eng:{eng['score']}%"
                        else:
                            color = (0, 165, 255) # Orange for Spoof
                            label += " | ⚠️ SPOOF"

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label, (x1, max(20, y1 - 10)), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

                cv2.imshow(f"Smart Attendance - {cid}", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                break

        self.cameras.stop_all()
        cv2.destroyAllWindows()
        logger.info("🛑 System Stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['run', 'register'], default='run')
    args = parser.parse_args()

    if args.mode == 'register':
        db = DatabaseManager()
        detector = FaceDetector(config)
        registrar = StudentRegistration(config, detector, db)

        roll = input("Enter Roll Number: ")
        name = input("Enter Student Full Name: ")
        dept = input("Enter Department (e.g. CSE): ")
        sem = int(input("Enter Semester (e.g. 4): ") or 1)

        registrar.register_from_camera(roll, name, camera_source=0, department=dept, semester=sem)

    elif args.mode == 'run':
        app = SmartAttendanceApp()
        app.run()