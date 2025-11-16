# qdrant_client_cloud.py
import uuid
from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from qdrant_client.http import models as qmodels
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME, VECTOR_SIZE

# Create a Qdrant client for Cloud usage
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

def create_collection(recreate: bool = True) -> None:
    """
    Create (or recreate) the collection with VECTOR_SIZE and COSINE distance.
    """
    if recreate:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    else:
        # If you want to create only when absent, use create_collection (but qdrant client may vary)
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    print(f"Collection '{COLLECTION_NAME}' created (recreate={recreate}).")

def _ensure_valid_point_id(point_id: Optional[str]) -> str:
    """
    Return a valid UUID string. If point_id looks like a UUID, return it.
    Otherwise generate a new UUID4 string.
    """
    if not point_id:
        return str(uuid.uuid4())
    # Accept only valid UUIDs (v4 or any), otherwise generate new
    try:
        _ = uuid.UUID(point_id)
        return point_id
    except Exception:
        return str(uuid.uuid4())

def upsert_claim(id: Optional[str], vector: List[float], payload: Dict[str, Any]) -> str:
    """
    Upsert a single claim. If id is not a valid UUID (or None), a UUID will be generated.
    Returns the final point id (UUID string).
    """
    final_id = _ensure_valid_point_id(id)
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[{
            "id": final_id,
            "vector": vector,
            "payload": payload
        }]
    )
    return final_id

def upsert_claims_batch(items: List[Dict[str, Any]], batch_size: int = 64) -> List[str]:
    """
    Upsert many points. Each item must be dict with keys: optional 'id', 'vector', 'payload'.
    Returns list of final ids inserted.
    """
    final_ids = []
    batch = []
    for item in items:
        pid = _ensure_valid_point_id(item.get("id"))
        batch.append({
            "id": pid,
            "vector": item["vector"],
            "payload": item.get("payload", {})
        })
        final_ids.append(pid)

        if len(batch) >= batch_size:
            client.upsert(collection_name=COLLECTION_NAME, points=batch)
            batch = []

    # remaining
    if batch:
        client.upsert(collection_name=COLLECTION_NAME, points=batch)

    return final_ids

def search(vector: List[float], k: int = 5, with_payload: bool = True) -> List[Dict[str, Any]]:
    """
    Search top-k similar points and return a list of dicts:
      [{ 'id': <uuid>, 'score': <float>, 'payload': {...} }, ...]
    """
    hits = client.search(collection_name=COLLECTION_NAME, query_vector=vector, limit=k)
    results = []
    for h in hits:
        results.append({
            "id": h.id,
            "score": h.score,
            "payload": h.payload if with_payload else None
        })
    return results
