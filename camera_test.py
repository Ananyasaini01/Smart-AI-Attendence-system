import cv2
import numpy as np
import time

backends = [
    (cv2.CAP_DSHOW, "DSHOW"),
    (cv2.CAP_MSMF, "MSMF"),
    (cv2.CAP_ANY, "ANY")
]

for index in range(5):
    for backend, name in backends:
        print(f"Trying camera index {index} with backend {name}...")

        cap = cv2.VideoCapture(index, backend)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            cap.release()
            continue

        ok = False

        for _ in range(20):
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                mean_value = np.mean(frame)
                print(f"Frame mean: {mean_value}")

                if mean_value > 2:
                    ok = True
                    break

        if ok:
            print(f"\n✅ WORKING CAMERA FOUND!")
            print(f"Index: {index}")
            print(f"Backend: {name}")
            print("Press Q to close test window.\n")

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                cv2.putText(
                    frame,
                    f"WORKING: index={index}, backend={name}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                cv2.imshow("Camera Test", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    cap.release()
                    cv2.destroyAllWindows()
                    exit()

        cap.release()

print("\n❌ No working camera found.")
cv2.destroyAllWindows()