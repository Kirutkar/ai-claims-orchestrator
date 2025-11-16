# """
# Seed script to populate Qdrant with sample insurance claims data
# This helps demonstrate the similarity search and fraud detection features
# Uses Google Gemini embeddings for semantic similarity
# """

# from qdrant_client import QdrantClient
# from qdrant_client.models import Distance, VectorParams, PointStruct
# import uuid
# import random
# import os
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Check if we should use real embeddings
# USE_REAL_EMBEDDINGS = os.getenv("GEMINI_API_KEY") is not None

# if USE_REAL_EMBEDDINGS:
#     try:
#         from langchain_google_genai import GoogleGenerativeAIEmbeddings
#         import google.generativeai as genai
        
#         GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#         EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
        
#         genai.configure(api_key=GEMINI_API_KEY)
#         embeddings_model = GoogleGenerativeAIEmbeddings(
#             model=EMBEDDING_MODEL,
#             google_api_key=GEMINI_API_KEY
#         )
#         print("✅ Using real Gemini embeddings")
#     except Exception as e:
#         print(f"⚠️  Could not initialize Gemini embeddings: {e}")
#         print("📝 Falling back to mock embeddings")
#         USE_REAL_EMBEDDINGS = False
# else:
#     print("📝 No GEMINI_API_KEY found, using mock embeddings")

# # Sample claims data for seeding
# SAMPLE_CLAIMS = [
#     {
#         "claim_type": "auto",
#         "description": "Rear-end collision on Highway 101, significant damage to rear bumper and trunk",
#         "amount": 4500,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "auto",
#         "description": "Minor fender bender in parking lot, small dent on driver side door",
#         "amount": 1200,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "auto",
#         "description": "Single vehicle accident, hit a pole, front end damage",
#         "amount": 8900,
#         "status": "rejected",
#         "fraud_indicators": "inconsistent story, late reporting"
#     },
#     {
#         "claim_type": "health",
#         "description": "Emergency room visit for broken arm from sports injury",
#         "amount": 3200,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "health",
#         "description": "Outpatient surgery for knee replacement, includes physical therapy",
#         "amount": 25000,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "health",
#         "description": "Multiple doctor visits and prescriptions for chronic back pain",
#         "amount": 15000,
#         "status": "needs_review",
#         "fraud_indicators": "high frequency of visits"
#     },
#     {
#         "claim_type": "home",
#         "description": "Water damage from burst pipe in kitchen, flooring and cabinet replacement",
#         "amount": 12000,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "home",
#         "description": "Roof damage from recent storm, shingles and underlayment replacement needed",
#         "amount": 8500,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "home",
#         "description": "Fire damage to garage, complete rebuild required",
#         "amount": 45000,
#         "status": "under_investigation",
#         "fraud_indicators": "previous claims history, suspicious timing"
#     },
#     {
#         "claim_type": "auto",
#         "description": "Windshield crack from road debris on interstate",
#         "amount": 350,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "health",
#         "description": "Routine dental work including two fillings and cleaning",
#         "amount": 850,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "auto",
#         "description": "Total loss vehicle from multi-car pileup on foggy morning",
#         "amount": 22000,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "home",
#         "description": "Theft of jewelry and electronics while on vacation",
#         "amount": 18000,
#         "status": "rejected",
#         "fraud_indicators": "no police report, inflated values"
#     },
#     {
#         "claim_type": "health",
#         "description": "Hospital stay for pneumonia treatment, three days",
#         "amount": 12500,
#         "status": "approved",
#         "fraud_indicators": "none"
#     },
#     {
#         "claim_type": "auto",
#         "description": "Side-swipe accident, mirror and door panel damaged",
#         "amount": 2800,
#         "status": "approved",
#         "fraud_indicators": "none"
#     }
# ]


# def create_embedding(text: str, size: int = 768) -> list:
#     """
#     Create embedding vector using Gemini or mock for demonstration
#     """
#     if USE_REAL_EMBEDDINGS:
#         try:
#             # Use real Gemini embeddings
#             return embeddings_model.embed_query(text)
#         except Exception as e:
#             print(f"⚠️  Error generating embedding: {e}")
#             print("📝 Falling back to mock embedding")
    
#     # Mock embedding fallback
#     random.seed(hash(text))
#     return [random.uniform(-1, 1) for _ in range(size)]


# def seed_qdrant_database():
#     """Seed Qdrant database with sample claims"""
    
#     print("🌱 Starting Qdrant database seeding...")
    
#     # Connect to Qdrant
#     try:
#         client = QdrantClient(host="localhost", port=6333)
#         print("✅ Connected to Qdrant")
#     except Exception as e:
#         print(f"❌ Failed to connect to Qdrant: {e}")
#         print("Make sure Qdrant is running: docker-compose up -d")
#         return
    
#     collection_name = "insurance_claims"
    
#     # Create collection if it doesn't exist
#     try:
#         collections = client.get_collections().collections
#         collection_names = [col.name for col in collections]
        
#         if collection_name in collection_names:
#             print(f"🗑️  Deleting existing collection: {collection_name}")
#             client.delete_collection(collection_name)
        
#         print(f"📦 Creating collection: {collection_name}")
#         client.create_collection(
#             collection_name=collection_name,
#             vectors_config=VectorParams(size=768, distance=Distance.COSINE)
#         )
#         print("✅ Collection created successfully")
#     except Exception as e:
#         print(f"❌ Error creating collection: {e}")
#         return
    
#     # Insert sample claims with embeddings
#     points = []
#     print(f"🔄 Generating embeddings for {len(SAMPLE_CLAIMS)} claims...")
    
#     for i, claim in enumerate(SAMPLE_CLAIMS):
#         # Create embedding from claim text
#         claim_text = f"{claim['claim_type']} claim: {claim['description']} Amount: ${claim['amount']}"
#         embedding = create_embedding(claim_text)
        
#         point = PointStruct(
#             id=str(uuid.uuid4()),
#             vector=embedding,
#             payload={
#                 "claim_id": f"CLM-SEED-{i:04d}",
#                 "claim_type": claim["claim_type"],
#                 "description": claim["description"],
#                 "amount": claim["amount"],
#                 "status": claim["status"],
#                 "fraud_indicators": claim["fraud_indicators"]
#             }
#         )
#         points.append(point)
        
#         if (i + 1) % 5 == 0:
#             print(f"   Generated {i + 1}/{len(SAMPLE_CLAIMS)} embeddings...")
    
#     try:
#         client.upsert(collection_name=collection_name, points=points)
#         print(f"✅ Inserted {len(points)} sample claims into Qdrant")
#     except Exception as e:
#         print(f"❌ Error inserting claims: {e}")
#         return
    
#     # Verify insertion
#     try:
#         collection_info = client.get_collection(collection_name)
#         print(f"\n📊 Collection Statistics:")
#         print(f"   - Total points: {collection_info.points_count}")
#         print(f"   - Vector size: {collection_info.config.params.vectors.size}")
#         print(f"   - Distance metric: {collection_info.config.params.vectors.distance}")
#     except Exception as e:
#         print(f"⚠️  Could not retrieve collection info: {e}")
    
#     print("\n🎉 Seeding completed successfully!")
#     print("\n💡 Sample claims by type:")
#     claim_types = {}
#     for claim in SAMPLE_CLAIMS:
#         claim_type = claim["claim_type"]
#         claim_types[claim_type] = claim_types.get(claim_type, 0) + 1
    
#     for claim_type, count in claim_types.items():
#         print(f"   - {claim_type}: {count} claims")


# if __name__ == "__main__":
#     seed_qdrant_database()


import uuid
from gemini_embedder import embed_text
from qdrant_client_cloud import create_collection, upsert_claim
from config import COLLECTION_NAME

sample_claims = [
    {
        "description": "Rear-end collision on highway causing bumper damage",
        "amount": 4500,
        "claim_type": "auto",
        "status": "approved",
        "fraud": False
    },
    {
        "description": "Kitchen flood damage from pipe burst",
        "amount": 12000,
        "claim_type": "home",
        "status": "approved",
        "fraud": False
    },
    {
        "description": "Windshield crack from road debris",
        "amount": 350,
        "claim_type": "auto",
        "status": "approved",
        "fraud": False
    }
]

def seed():
    create_collection()

    for i, claim in enumerate(sample_claims):
        vector = embed_text(claim["description"])
        upsert_claim(
            id=f"SEED-{i+1}",
            vector=vector,
            payload=claim
        )
        print(f"Inserted SEED-{i+1}")

if __name__ == "__main__":
    seed()
