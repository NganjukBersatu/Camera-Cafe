import cv2
import time
import base64
import json
import numpy as np
from datetime import datetime

CAPTURE_INTERVAL = 3

def run_camera_worker(camera_index: int = 0):
    from app.tasks.ai_tasks import process_frame_task
    from app.config import settings
    import redis

    print(f"Memulai camera worker...")
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("ERROR: Tidak bisa buka kamera!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    r = redis.from_url(settings.redis_url)
    last_ai_time = 0

    print("Kamera terbuka. Mulai stream + deteksi...")

    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # Ambil hasil deteksi terakhir dari Redis
            detection_raw = r.get("latest_detection")
            if detection_raw:
                detections = json.loads(detection_raw)
                if isinstance(detections, list):
                    for detection in detections:
                        bbox = detection.get("bbox")
                        name = detection.get("customer_name", "Unknown")
                        matched = detection.get("matched", False)

                        if bbox:
                            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                            color = (0, 255, 0) if matched else (0, 0, 255)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            (tw, th), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                            cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 8, y1), color, -1)
                            cv2.putText(frame, name, (x1 + 4, y1 - 5),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Encode frame dengan overlay
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')

            # Simpan ke Redis untuk stream
            r.set("latest_frame", frame_b64, ex=5)

            # Kirim ke AI setiap 3 detik
            now = time.time()
            if now - last_ai_time >= CAPTURE_INTERVAL:
                task = process_frame_task.delay(frame_b64, "webcam-kasir")
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Task AI dikirim: {task.id}")
                last_ai_time = now

        except KeyboardInterrupt:
            print("\nCamera worker dihentikan.")
            break
        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(0.1)

    cap.release()
    print("Kamera ditutup.")

if __name__ == "__main__":
    run_camera_worker(camera_index=0)