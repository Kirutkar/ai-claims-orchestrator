# 📘 Qdrant Vector Engine — Data Science Module  
AI Claims Orchestration System (Vector Store + Embeddings Layer)

This folder contains the **Data Scientist deliverables** for the Claims AI Hackathon project.  
It provides the complete **Vector Similarity Engine** using:

- **Google Gemini Embeddings**
- **Qdrant Cloud Vector Database**

This module will be consumed by the backend team and should not be modified by frontend or orchestration teams.

---

# 🎯 Purpose of This Module

This module is responsible for:

### ✔ 1. Generating text embeddings  
Using **Google Gemini Embedding Model (`text-embedding-004`)**

### ✔ 2. Storing vectors in Qdrant  
Creating & managing the `insurance_claims` collection.

### ✔ 3. Seeding historical insurance claims  
Used for similarity search and fraud pattern detection.

### ✔ 4. Retrieving top-N similar claims  
Supports fraud detection and claim decision recommendations.

---

# 📂 Folder Structure

qdrant/
│
├── config.py # Load environment variables
├── gemini_embedder.py # Gemini text embedding module
├── qdrant_client_cloud.py # Qdrant Cloud client + search helpers
├── seed_claims.py # Script to seed sample claim data
├── search_claims.py # Script to test similarity search
├── requirements.txt # Python dependencies
└── README.md # Documentation (this file)

yaml
Copy code

---

# ⚙️ Setup Instructions

## 1️⃣ Install dependencies
pip install -r requirements.txt

bash
Copy code

## 2️⃣ Create a `.env` file
Create a file named `.env` in this folder:

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
QDRANT_URL=https://YOUR-CLUSTER.cloud.qdrant.io
QDRANT_API_KEY=YOUR_QDRANT_API_KEY

yaml
Copy code

### Where to get keys?
- **Gemini API Key** → https://aistudio.google.com  
- **Qdrant Cloud URL + API Key** → https://cloud.qdrant.io

---

# 🧠 How It Works (Simple Explanation)

This module builds a pipeline:

Text input → Gemini Embedding → 768-dim vector → Qdrant Cloud → Similar claims out

yaml
Copy code

### Why vectors?
Vectors allow comparing claims such as:

- “Rear-end accident on highway”
- “Bumper damage in traffic”
- “Hit from behind at signal”

These are **semantically similar**, even if the text is different.

Qdrant returns claims with **closest vectors**, used for:
- Fraud detection  
- Claim amount recommendations  
- Similar case reasoning  

---

# 🌱 Step 1 — Seed Qdrant With Sample Claims

Run:

python seed_claims.py

yaml
Copy code

What this script does:
- Connects to Qdrant Cloud  
- Recreates the `insurance_claims` collection  
- Generates embeddings for each sample claim  
- Uploads vectors + metadata  
- Prints statistics  

After running, Qdrant Cloud will contain initial insurance claim data.

---

# 🔍 Step 2 — Test Similarity Search

Run:

python search_claims.py "rear bumper damage on highway"

sql
Copy code

This script:
1. Creates an embedding from your query  
2. Searches Qdrant for top-5 similar claims  
3. Prints matched claims with similarity scores  

Result format:
ID: SEED-001, Score: 0.89
{'description': 'Rear-end collision...', 'amount': 4500, ...}

yaml
Copy code

---

# 🧩 Integration Guide for Backend Team

Backend engineers will **import your functions** (not rewrite them).

### Example (backend usage):

```python
from gemini_embedder import embed_text
from qdrant_client_cloud import search

# Step 1: Create embedding from claim text
vector = embed_text("damaged bumper from rear-end accident")

# Step 2: Fetch similar claims from Qdrant Cloud
results = search(vector, k=5)
Backend Responsibilities (API Layer)
Receive input from React app

Handle image/video extraction (Gemini Vision / Video)

Pass extracted description to your embedder

Query Qdrant using your search()

Pass results to LLM decision module

Your Deliverable is Complete After Providing:
✔ Embedding module
✔ Qdrant storage module
✔ Search module
✔ Documentation (this file)

🛠 Architecture Diagram
scss
Copy code
                         (Your Module)
                 ┌─────────────────────────┐
                 │  Gemini Embeddings      │
User Claim Text →│  embed_text()           │→ Vector (768 dims)
                 └─────────────────────────┘
                               │
                               ▼
                 ┌─────────────────────────┐
                 │   Qdrant Cloud          │
                 │ upsert(), search()      │
                 └─────────────────────────┘
                               │
                               ▼
                    Similar Historical Claims
Backend → LLM → Business Logic → Final Decision
are separate from this module.