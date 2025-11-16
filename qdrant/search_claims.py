import sys
from gemini_embedder import embed_text
from qdrant_client_cloud import search
from config import *

if len(sys.argv) < 2:
    print("Usage: python search_claims.py \"your query text\"")
    sys.exit(1)

query = sys.argv[1]

print("Loading env from:", ENV_PATH)
print("CONFIG LOADED:")
print("QDRANT_URL:", QDRANT_URL)
print("QDRANT_API_KEY found:", QDRANT_API_KEY is not None)
print("EMBEDDING_MODEL:", EMBEDDING_MODEL)
print("VECTOR_SIZE:", VECTOR_SIZE)

# Create vector
vector = embed_text(query)

# Perform search
results = search(vector, k=5)

# Print output properly
print("\nTop results:\n")
for r in results:
    print(f"ID: {r['id']}")
    print(f"Score: {r['score']}")
    print("Payload:", r["payload"])
    print("-" * 50)
