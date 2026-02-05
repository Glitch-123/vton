import cv2, os, time

os.makedirs("data/captured", exist_ok=True)

cap = cv2.VideoCapture(0)
print("📸 Camera ON | Press 'c' to capture | 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Camera", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('c'):
        path = f"data/captured/capture_{int(time.time())}.jpg"
        cv2.imwrite(path, frame)
        print(f"✅ Saved: {path}")
        break

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
