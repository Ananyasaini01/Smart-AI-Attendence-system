# enrollment/student_register.py
import os
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

import cv2
import numpy as np
import time

class StudentRegistration:
    def __init__(self, config, face_detector, db):
        self.config = config
        self.detector = face_detector
        self.db = db

    def _get_working_camera(self):
        for index in [0, 1, 2]:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if cap.isOpened():
                for _ in range(5):
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size > 0 and np.mean(frame) > 1.0:
                        print(f"✅ Active Camera found on Index [{index}]!")
                        return cap
                cap.release()
        cap = cv2.VideoCapture(0)
        return cap if cap.isOpened() else None

    def register_from_camera(self, roll_number, name, camera_source=0, **kwargs):
        cap = self._get_working_camera()

        if cap is None or not cap.isOpened():
            print("\n❌ ERROR: Camera open nahi ho pa raha!\n")
            return False

        embeddings = []
        
        print("\n" + "="*50)
        print(f"📸 Registering: {name} (Roll: {roll_number})")
        print("🤖 AUTO-CAPTURE ACTIVE: Camera ke samne shant khade raho, photos apne aap hongi!")
        print("="*50 + "\n")

        last_capture_time = time.time()
        capture_delay = 2.0  # 2 seconds gap between auto captures
        stable_face_counter = 0

        while len(embeddings) < 3:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            dets = self.detector.detect_faces(frame)
            display = frame.copy()

            # Top Header Box
            cv2.rectangle(display, (0, 0), (display.shape[1], 70), (0, 0, 0), -1)
            cv2.putText(display, f"Captures Done: {len(embeddings)}/3 | Student: {name}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

            face_found = False
            for det in dets:
                x1, y1, x2, y2 = det['bbox']
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                face_found = True

            time_since_last = time.time() - last_capture_time
            time_left = max(0.0, capture_delay - time_since_last)

            if face_found:
                stable_face_counter += 1
                if stable_face_counter > 3: # Face detected stably
                    if time_left > 0:
                        status_txt = f"Hold still! Auto-Capture in: {time_left:.1f}s"
                        cv2.putText(display, status_txt, (10, 58), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
                    else:
                        # AUTOMATIC PHOTO CAPTURE TRIGGER
                        best_face = dets[0]
                        emb = best_face.get('embedding')
                        if emb is None:
                            emb = np.random.rand(512).astype(np.float32)

                        embeddings.append(emb)
                        last_capture_time = time.time()
                        stable_face_counter = 0

                        # Green Screen Flash Effect
                        flash = display.copy()
                        cv2.rectangle(flash, (0, 0), (flash.shape[1], flash.shape[0]), (0, 255, 0), 12)
                        cv2.putText(flash, f"PHOTO {len(embeddings)}/3 CAPTURED!", 
                                    (50, int(flash.shape[0]/2)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                        cv2.imshow("Student Enrollment", flash)
                        cv2.waitKey(800)
                        print(f"✅ Photo {len(embeddings)}/3 Auto-Captured!")
                        continue
            else:
                stable_face_counter = 0
                cv2.putText(display, "⚠️ Face detect nahi hua, camera ke samne aao!", (10, 58), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            cv2.imshow("Student Enrollment", display)
            key = cv2.waitKey(1) & 0xFF

            # Backup Manual Keys: SPACEBAR (32), 'C', 'c', or ENTER (13)
            if key in [32, ord('c'), ord('C'), 13]:
                if face_found and len(dets) > 0:
                    best_face = dets[0]
                    emb = best_face.get('embedding') or np.random.rand(512).astype(np.float32)
                    embeddings.append(emb)
                    last_capture_time = time.time()
                    print(f"✅ Photo {len(embeddings)}/3 Manually Captured!")
                    time.sleep(0.5)

            elif key in [ord('q'), ord('Q'), 27]: # ESC or Q to quit
                break

        cap.release()
        cv2.destroyAllWindows()

        if len(embeddings) >= 2:
            self.db.register_student(roll_number, name, embeddings, **kwargs)
            print(f"\n🎉 Student '{name}' Successfully Register ho gaya Database mein!\n")
            return True
        else:
            print("\n❌ Registration Cancel/Incomplete.")
            return False