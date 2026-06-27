from app.worker import celery_app
from app.services.ai_pipeline import AIPipeline
from app.vector.qdrant import get_client, ensure_collection, search_face
from app.database import get_db
from app.models.customer import Customer
from app.models.visit import Visit
from app.models.recognition import RecognitionEvent
from app.config import settings

from datetime import datetime, timezone

import cv2
import numpy as np
import uuid
import base64
import redis
import json


@celery_app.task(name="app.tasks.ai_tasks.process_frame_task")
def process_frame_task(frame_b64: str, camera_id: str = "webcam-kasir"):

    db = next(get_db())
    r = redis.from_url(settings.redis_url)

    try:
        # Decode frame
        frame_bytes = base64.b64decode(frame_b64)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"success": False, "message": "Frame tidak valid"}

        # AI Pipeline
        pipeline = AIPipeline.get_instance()
        faces = pipeline.process_frame(frame)

        if not faces:
            return {"success": False, "message": "Tidak ada wajah terdeteksi"}

        # Qdrant
        qdrant = get_client()
        ensure_collection(qdrant)

        detections = []  # untuk overlay stream
        results = []

        # Loop semua wajah
        for face in faces:
            embedding = face["embedding"]
            bbox = face["bbox"]
            matches = search_face(qdrant, embedding, threshold=0.35)

            # Tidak dikenali
            if not matches:
                db.add(RecognitionEvent(
                    id=str(uuid.uuid4()),
                    camera_id=camera_id,
                    customer_id=None,
                    similarity=0.0,
                    matched=False,
                ))
                detections.append({
                    "customer_name": "Unknown",
                    "matched": False,
                    "bbox": bbox
                })
                unknown_cooldown = r.get("cooldown:unknown")
                if not unknown_cooldown:
                    r.setex("cooldown:unknown", 30, "1")
                    r.publish("recognition_events", json.dumps({
                        "event_type": "unknown_detected",
                        "camera_id": camera_id,
                        "detected_at": datetime.now(timezone.utc).isoformat(),
                    }))
                results.append({"success": False, "message": "Wajah tidak dikenali"})
                continue

            # Ambil customer
            customer_id = matches[0].payload["customer_id"]
            customer = db.get(Customer, customer_id)

            if not customer:
                detections.append({
                    "customer_name": "Unknown",
                    "matched": False,
                    "bbox": bbox
                })
                continue

            if not customer.is_active:
                detections.append({
                    "customer_name": customer.name,
                    "similarity": matches[0].score,
                    "matched": True,
                    "bbox": bbox
                })
                continue

            # Simpan deteksi untuk overlay
            detections.append({
                "customer_name": customer.name,
                "similarity": matches[0].score,
                "matched": True,
                "bbox": bbox
            })

            # Cek cooldown per customer
            cooldown_key = f"cooldown:{customer_id}"
            already_notified = r.get(cooldown_key)

            if already_notified:
                print(f"Cooldown aktif untuk {customer.name} — skip notif")
                results.append({
                    "success": True,
                    "customer_name": customer.name,
                    "message": "cooldown aktif"
                })
                continue

            # Set cooldown 30 menit
            r.setex(cooldown_key, 60, "1")

            # Ambil statistik
            total_visits = db.query(Visit).filter(Visit.customer_id == customer_id).count()
            last_visit_obj = (
                db.query(Visit)
                .filter(Visit.customer_id == customer_id)
                .order_by(Visit.visited_at.desc())
                .first()
            )
            last_visit = last_visit_obj.visited_at.isoformat() if last_visit_obj else None

            # Simpan recognition event
            db.add(RecognitionEvent(
                id=str(uuid.uuid4()),
                camera_id=camera_id,
                customer_id=customer_id,
                similarity=matches[0].score,
                matched=True,
            ))

            # Publish notif ke dashboard
            payload = {
                "event_type": "customer_detected",
                "camera_id": camera_id,
                "customer_id": customer_id,
                "customer_name": customer.name,
                "similarity": matches[0].score,
                "preferences": customer.preferences,
                "notes": customer.notes,
                "total_visits": total_visits + 1,
                "last_visit": last_visit,
                "detected_at": datetime.now(timezone.utc).isoformat(),
            }

            print(f"Broadcast notifikasi: {customer.name}")
            r.publish("recognition_events", json.dumps(payload))

            results.append({
                "success": True,
                "customer_id": customer_id,
                "customer_name": customer.name,
                "similarity": matches[0].score,
            })

        db.commit()

        # Simpan semua deteksi untuk overlay stream
        r.set("latest_detection", json.dumps(detections), ex=10)

        return {"success": True, "faces_detected": len(faces), "results": results}

    except Exception as e:
        return {"success": False, "message": str(e)}

    finally:
        db.close()