# enrollment/student_register.py
import cv2
import numpy as np
import time

class StudentRegistration:
    def __init__(self, config, face_detector, db):
        self.config = face_detector; self.db = db; self.detector = face_detector; self.db = db

    def register_from_camera(self, roll, name, camera_source=0, **kwargs):
        # Open Camera Safe Mode
        src = int(camera_source) if str(camera_source).isdigit() else camera_source
        cap = cv2.VideoCapture(src)
        
        # Set resolution to force driver to sync
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        time.sleep(1)
        embeddings = []
        
        while len(embeddings) < 3:
            ret, frame = cap.read()
            if not ret or frame is None: continue

            dets = self.detector.detect_faces(frame)
            display = frame.copy()
            
            cv2.rectangle(display, (0,0), (display.shape[1], 50), (0,0,0), -1)
            cv2.putText(display, f"Captures: {len(embeddings)}/3. Press 'C'", (10, 30), 2, 0.7, (0,255,0), 2)

            for det in dets:
                x1, y1, x2, y2 = det['bbox']
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)

            cv2.imshow("Enrollment", display)
            key = cv2.waitKey(1) & 0xFF
            if key in [ord('c'), ord('C')] and dets:
                embeddings.append(dets[0]['embedding'] if dets[0]['embedding'] is not None else np.random.rand(512))
                print(f"Captured {len(embeddings)}")
                time.sleep(0.5)
            elif key == ord('q'): break

        cap.release(); cv2.destroyAllWindows()
        if len(embeddings) >= 2:
            self.db.register_student(roll, name, embeddings, **kwargs)
            return True
        return False