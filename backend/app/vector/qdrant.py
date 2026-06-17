from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, ScoredPoint, QueryResponse
from app.config import settings

COLLECTION_NAME = "face_embeddings"
VECTOR_SIZE = 512


def get_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection(client: QdrantClient) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def upsert_face(client: QdrantClient, face_id: str, customer_id: str, embedding: list[float]) -> None:
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=_uuid_to_int(face_id),
                vector=embedding,
                payload={"face_id": face_id, "customer_id": customer_id},
            )
        ],
    )


def search_face(client: QdrantClient, embedding: list[float], threshold: float = 0.6, top_k: int = 1) -> list[QueryResponse]:
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        limit=top_k,
        score_threshold=threshold,
        with_payload=True,
    )
    return results.points


def delete_face(client: QdrantClient, face_id: str) -> None:
    from qdrant_client.models import PointIdsList
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=PointIdsList(points=[_uuid_to_int(face_id)]),
    )


def _uuid_to_int(uuid_str: str) -> int:
    import uuid
    return uuid.UUID(uuid_str).int % (2**63)
