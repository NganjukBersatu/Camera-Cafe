from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.customer import Customer, CustomerFace
from app.models.visit import Visit
from app.models.recognition import RecognitionEvent
from app.vector.qdrant import get_client, ensure_collection, upsert_face, search_face
from app.services.ai_pipeline import AIPipeline
from datetime import datetime, timezone
import cv2
import numpy as np
import uuid

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


@router.post("/{customer_id}/enroll")
async def enroll_face(
    customer_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer tidak ditemukan")

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Gambar tidak valid")

    pipeline = AIPipeline.get_instance()
    raw_faces = pipeline.get_faces(frame)
    faces = [{"bbox": f.bbox.tolist(), "det_score": float(f.det_score), "embedding": f.embedding.tolist()} for f in raw_faces]

    if not faces:
        raise HTTPException(status_code=400, detail="Tidak ada wajah terdeteksi")

    face = faces[0]
    embedding = face["embedding"]

    face_id = str(uuid.uuid4())
    customer_face = CustomerFace(
        id=face_id,
        customer_id=customer_id,
    )
    db.add(customer_face)
    db.commit()

    qdrant = get_client()
    ensure_collection(qdrant)
    upsert_face(qdrant, face_id, customer_id, embedding)

    return {
        "message": "Wajah berhasil didaftarkan",
        "face_id": face_id,
        "det_score": face["det_score"],
        "customer_id": customer_id,
        "customer_name": customer.name,
    }


@router.post("/recognize")
async def recognize_face(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Gambar tidak valid")

    pipeline = AIPipeline.get_instance()
    faces = pipeline.process_frame(frame)

    if not faces:
        return {"recognized": False, "message": "Tidak ada wajah terdeteksi"}

    qdrant = get_client()
    ensure_collection(qdrant)
    embedding = faces[0]["embedding"]
    matches = search_face(qdrant, embedding, threshold=0.6)

    if not matches:
        # Catat recognition event yang tidak match
        rec_event = RecognitionEvent(
            id=str(uuid.uuid4()),
            camera_id="webcam-kasir",
            customer_id=None,
            similarity=0.0,
            matched=False,
        )
        db.add(rec_event)
        db.commit()
        return {"recognized": False, "message": "Wajah tidak dikenali"}

    customer_id = matches[0].payload["customer_id"]
    customer = db.get(Customer, customer_id)

    if not customer:
        return {"recognized": False, "message": "Customer tidak ditemukan di database"}

    # Catat kunjungan otomatis
    visit = Visit(
        id=str(uuid.uuid4()),
        customer_id=customer_id,
        source="camera",
    )
    db.add(visit)
    db.commit()

    # Catat recognition event yang berhasil
    rec_event = RecognitionEvent(
        id=str(uuid.uuid4()),
        camera_id="webcam-kasir",
        customer_id=customer_id,
        similarity=matches[0].score,
        matched=True,
    )
    db.add(rec_event)
    db.commit()

    # Broadcast ke dashboard via WebSocket
    try:
        await request.app.state.manager.broadcast({
            "event_type": "customer_detected",
            "camera_id": "webcam-kasir",
            "customer_id": customer_id,
            "customer_name": customer.name,
            "similarity": matches[0].score,
            "preferences": customer.preferences,
            "last_visit": None,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        print(f"WebSocket broadcast gagal: {e}")

    return {
        "recognized": True,
        "customer_id": customer_id,
        "customer_name": customer.name,
        "confidence": matches[0].score,
        "notes": customer.notes,
        "preferences": customer.preferences,
    }