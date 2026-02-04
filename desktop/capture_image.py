# desktop/capture_image.py

import cv2
import os
import time

SAVE_DIR = "data/captured"

os.makedirs(SAVE_DIR, exist_ok=True)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Camera open nahi ho raha")
    exit()

print("📸 Camera ON")
print("➡ Press 'c' to capture image")
print("➡ Press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    cv2.imshow("Capture Image", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('c'):
        filename = f"capture_{int(time.time())}.jpg"
        path = os.path.join(SAVE_DIR, filename)
        cv2.imwrite(path, frame)
        print(f"✅ Image saved at: {path}")
        break

    elif key == ord('q'):
        print("❌ Capture cancelled")
        break

cap.release()
cv2.destroyAllWindows()
