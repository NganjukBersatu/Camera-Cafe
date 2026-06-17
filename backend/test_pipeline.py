import cv2
import numpy as np
from ultralytics import YOLO
import insightface
from insightface.app import FaceAnalysis

print("Loading YOLOv8n...")
model = YOLO('yolov8n.pt')

print("Loading InsightFace...")
face_app = FaceAnalysis(name='buffalo_sc', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))
print("Semua model loaded!")

cap = cv2.VideoCapture(0)
print("Webcam dibuka. Tekan 'q' untuk keluar.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Layer 1 — deteksi orang
    results = model(frame, classes=[0], verbose=False)
    num_people = len(results[0].boxes)

    if num_people > 0:
        # Layer 2+3 — deteksi wajah + embedding
        faces = face_app.get(frame)

        for face in faces:
            box = face.bbox.astype(int)
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
            cv2.putText(frame, f'Wajah ({face.det_score:.2f})',
                       (box[0], box[1]-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.putText(frame, f'Orang: {num_people}',
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    else:
        cv2.putText(frame, 'Tidak ada orang',
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow('Camera Cafe CRM - Full Pipeline', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Selesai.")