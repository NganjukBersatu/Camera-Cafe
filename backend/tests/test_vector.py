import uuid
import random
from app.vector.qdrant import get_client, ensure_collection, upsert_face, search_face, delete_face


def _dummy_embedding() -> list[float]:
    return [random.uniform(-1, 1) for _ in range(512)]


def test_qdrant_collection():
    client = get_client()
    ensure_collection(client)
    collections = {c.name for c in client.get_collections().collections}
    assert "face_embeddings" in collections


def test_upsert_and_search():
    client = get_client()
    ensure_collection(client)

    face_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())
    embedding = _dummy_embedding()

    upsert_face(client, face_id, customer_id, embedding)

    results = search_face(client, embedding, threshold=0.99)
    assert len(results) > 0
    assert results[0].payload is not None
    assert results[0].payload["customer_id"] == customer_id


def test_delete_face():
    client = get_client()
    ensure_collection(client)

    face_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())
    embedding = _dummy_embedding()

    upsert_face(client, face_id, customer_id, embedding)
    delete_face(client, face_id)

    results = search_face(client, embedding, threshold=0.99)
    if results:
        assert all(r.payload is not None and r.payload.get("face_id") != face_id for r in results)
