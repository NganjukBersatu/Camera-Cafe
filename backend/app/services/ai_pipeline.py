import cv2
import numpy as np
from ultralytics import YOLO
from insightface.app import FaceAnalysis
import threading

class AIPipeline:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        print("Loading YOLOv8n...")
        self.yolo = YOLO('yolov8n.pt')
        print("Loading InsightFace...")
        self.face_app = FaceAnalysis(
            name='buffalo_sc',
            providers=['CPUExecutionProvider']
        )
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        print("AI Pipeline ready!")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def detect_people(self, frame: np.ndarray) -> bool:
        results = self.yolo(frame, classes=[0], verbose=False)
        return len(results[0].boxes) > 0

    def get_faces(self, frame: np.ndarray) -> list:
        return self.face_app.get(frame)

    def process_frame(self, frame: np.ndarray) -> list[dict]:
        # Layer 1 — ada orang?
        if not self.detect_people(frame):
            return []

        # Layer 2+3 — deteksi wajah + embedding
        faces = self.get_faces(frame)
        results = []
        for face in faces:
            results.append({
                "bbox": face.bbox.tolist(),
                "det_score": float(face.det_score),
                "embedding": face.embedding.tolist(),
            })
        return results
