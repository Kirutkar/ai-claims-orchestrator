from dotenv import load_dotenv
import os

# Load root .env manually
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env")

print("Loading env from:", ENV_PATH)
load_dotenv(ENV_PATH)

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")


# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "insurance_claims")
VECTOR_SIZE = int(os.getenv("EMBEDDING_DIMENSION", 768))

# Debug print
print("CONFIG LOADED:")
print("QDRANT_URL:", QDRANT_URL)
print("QDRANT_API_KEY found:", QDRANT_API_KEY is not None)
print("EMBEDDING_MODEL:", EMBEDDING_MODEL)
print("VECTOR_SIZE:", VECTOR_SIZE)
