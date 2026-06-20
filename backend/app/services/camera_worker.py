import cv2
import time
import base64
import numpy as np
from datetime import datetime

CAPTURE_INTERVAL = 3

def run_camera_worker(camera_index: int = 0):
    # Import di sini supaya tidak konflik dengan reload
    from app.tasks.ai_tasks import process_frame_task

    print(f"Memulai camera worker dengan Celery...")
    print(f"Capture interval: {CAPTURE_INTERVAL} detik")
    print(f"Tekan Ctrl+C untuk berhenti")

    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("ERROR: Tidak bisa buka kamera!")
        return

    print("Kamera terbuka. Mulai deteksi...")

    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("ERROR: Tidak bisa baca frame")
                time.sleep(1)
                continue

            # Encode frame ke base64
            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')

            # Kirim ke Celery worker (async)
            timestamp = datetime.now().strftime("%H:%M:%S")
            task = process_frame_task.delay(frame_b64, "webcam-kasir")
            print(f"[{timestamp}] Task dikirim ke Celery: {task.id}")

        except KeyboardInterrupt:
            print("\nCamera worker dihentikan.")
            break
        except Exception as e:
            print(f"ERROR: {e}")

        time.sleep(CAPTURE_INTERVAL)

    cap.release()
    print("Kamera ditutup.")

if __name__ == "__main__":
    run_camera_worker(camera_index=0)