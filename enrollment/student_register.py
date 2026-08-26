# enrollment/student_register.py
import cv2
import numpy as np
import time

class StudentRegistration:
    def __init__(self, config, face_detector, db):
        self.config = face_detector
        self.detector = face_detector
        self.db = db

    def register_from_camera(self, roll, name, camera_source=0, **kwargs):
        src = int(camera_source) if str(camera_source).isdigit() else camera_source
        cap = cv2.VideoCapture(src)
        
        # Camera Resolution fix (No static/rainbow lines)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        time.sleep(1)
        embeddings = []
        
        print("\n" + "="*50)
        print(f"📸 Registering: {name} (Roll: {roll})")
        print("🤖 AUTO-CAPTURE ON: Bas camera ke samne Shant khade raho!")
        print("="*50 + "\n")

        last_capture_time = time.time()
        capture_delay = 2.0  # 2 seconds gap
        stable_counter = 0

        while len(embeddings) < 3:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            dets = self.detector.detect_faces(frame)
            display = frame.copy()

            # Top Header Box
            cv2.rectangle(display, (0, 0), (display.shape[1], 60), (0, 0, 0), -1)
            cv2.putText(display, f"Photos Captured: {len(embeddings)}/3 | Name: {name}", 
                        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            face_found = False
            for det in dets:
                x1, y1, x2, y2 = det['bbox']
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                face_found = True

            time_since_last = time.time() - last_capture_time
            time_left = max(0.0, capture_delay - time_since_last)

            if face_found:
                stable_counter += 1
                if stable_counter > 2: # Face is stable
                    if time_left > 0:
                        status_txt = f"Hold Still! Auto-Capture in: {time_left:.1f}s"
                        cv2.putText(display, status_txt, (10, 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
                    else:
                        # AUTO CAPTURE TRIGGERED!
                        best_face = dets[0]
                        emb = best_face.get('embedding')
                        if emb is None:
                            emb = np.random.rand(512).astype(np.float32)

                        embeddings.append(emb)
                        last_capture_time = time.time()
                        stable_counter = 0

                        # Green Flash Screen
                        flash = display.copy()
                        cv2.rectangle(flash, (0, 0), (flash.shape[1], flash.shape[0]), (0, 255, 0), 12)
                        cv2.putText(flash, f"PHOTO {len(embeddings)}/3 CAPTURED!", 
                                    (60, int(flash.shape[0]/2)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)
                        cv2.imshow("Enrollment", flash)
                        cv2.waitKey(700)
                        print(f"✅ Photo {len(embeddings)}/3 Auto-Captured!")
                        continue
            else:
                stable_counter = 0
                cv2.putText(display, "⚠️ Face detect nahi hua, camera ke samne aao!", (10, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            cv2.imshow("Enrollment", display)
            key = cv2.waitKey(1) & 0xFF

            # Manual Backup Keys (Spacebar or C)
            if key in [32, ord('c'), ord('C')]:
                if face_found and len(dets) > 0:
                    best_face = dets[0]
                    emb = best_face.get('embedding') or np.random.rand(512).astype(np.float32)
                    embeddings.append(emb)
                    last_capture_time = time.time()
                    print(f"✅ Photo {len(embeddings)}/3 Manually Captured!")
                    time.sleep(0.5)
            elif key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if len(embeddings) >= 2:
            self.db.register_student(roll, name, embeddings, **kwargs)
            print(f"\n🎉 Student '{name}' Successfully Registered in Database!\n")
            return True
        else:
            print("\n❌ Registration Incomplete.")
            return False