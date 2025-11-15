# AI-CLAIMS-Orchestrator 🤖🏥

An intelligent claims processing system using Agentic AI for automated insurance claim analysis, fraud detection, and decision-making.

## 🎯 Project Overview

This AI-powered system orchestrates the end-to-end insurance claims processing workflow using:
- **Multi-Agent AI Architecture** with LangChain
- **Gemini LLM** for intelligent decision making
- **Qdrant Vector DB** for semantic search and claim matching
- **Opus Workflow Engine** for orchestration
- **FastAPI** backend for high-performance APIs
- **React** frontend for intuitive user experience

## 🏗️ Architecture

```
┌─────────────┐
│   React UI  │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│         FastAPI Backend                      │
├──────────────────────────────────────────────┤
│  ┌────────────────────────────────────────┐  │
│  │     LangChain Agent Orchestrator       │  │
│  ├────────────────────────────────────────┤  │
│  │  • Claim Validator Agent               │  │
│  │  • Fraud Detection Agent               │  │
│  │  • Policy Verification Agent           │  │
│  │  • Document Analyzer Agent             │  │
│  │  • Decision Maker Agent                │  │
│  └────────────────────────────────────────┘  │
└──────┬───────────────────────┬───────────────┘
       │                       │
┌──────▼──────┐        ┌──────▼──────┐
│   Gemini    │        │   Qdrant    │
│     LLM     │        │  Vector DB  │
└─────────────┘        └─────────────┘
       │
┌──────▼──────────┐
│  Opus Workflow  │
│  Orchestration  │
└─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- Gemini API Key

### Installation

1. **Clone and Setup Environment**
```bash
cd ai-claims-orchestrator
```

2. **Configure Environment Variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Start Qdrant Vector Database**
```bash
cd qdrant
docker-compose up -d
```

4. **Install Backend Dependencies**
```bash
cd ../backend
pip install -r requirements.txt
```

5. **Seed Sample Claims Data**
```bash
cd ../qdrant
python seeds_claims.py
```

6. **Start Backend Server**
```bash
cd ../backend
uvicorn main:app --reload --port 8000
```

7. **Install Frontend Dependencies**
```bash
cd ../frontend
npm install
```

8. **Start Frontend**
```bash
npm start
```

9. **Access Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
ai-claims-orchestrator/
├── backend/                    # FastAPI Backend
│   ├── main.py                # API endpoints
│   ├── orchestrator.py        # LangChain agent orchestration
│   ├── agents/                # Individual AI agents
│   │   ├── validator.py       # Claim validation agent
│   │   ├── fraud_detector.py  # Fraud detection agent
│   │   ├── policy_checker.py  # Policy verification agent
│   │   ├── document_analyzer.py # Document analysis agent
│   │   └── decision_maker.py  # Final decision agent
│   ├── models/                # Data models
│   │   └── schemas.py         # Pydantic models
│   ├── config.py              # Configuration
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React Frontend
│   ├── public/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── ClaimForm.jsx  # Claim submission form
│   │   │   ├── Dashboard.jsx  # Claims dashboard
│   │   │   ├── ClaimStatus.jsx # Status tracking
│   │   │   └── Results.jsx    # Analysis results
│   │   ├── services/          # API services
│   │   │   └── api.js         # API client
│   │   ├── App.jsx            # Main app component
│   │   └── index.js           # Entry point
│   └── package.json           # Node dependencies
│
├── qdrant/                     # Vector Database
│   ├── docker-compose.yml     # Qdrant setup
│   └── seeds_claims.py        # Sample data seeder
│
├── opus/                       # Workflow Orchestration
│   └── workflow.yaml          # Claims processing workflow
│
├── docs/                       # Documentation
│   ├── api-reference.md       # API documentation
│   └── demo-script.md         # Hackathon demo script
│
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🤖 AI Agents

### 1. Claim Validator Agent
- Validates claim completeness
- Checks required fields
- Verifies data formats

### 2. Fraud Detection Agent
- Analyzes claim patterns
- Detects anomalies
- Risk scoring

### 3. Policy Verification Agent
- Validates policy coverage
- Checks claim eligibility
- Verifies policy status

### 4. Document Analyzer Agent
- Extracts information from documents
- **Uses Gemini Vision API for OCR**
- Validates supporting documents
- Cross-verifies extracted text with claim details
- Checks for date, amount, and name consistency

### 5. Decision Maker Agent
- Aggregates agent findings
- Makes final decision
- Generates recommendations

## 🔄 Claims Processing Workflow

1. **Claim Submission** → User submits claim via React UI
2. **Validation** → Claim Validator checks completeness
3. **Fraud Check** → Fraud Detection analyzes patterns
3. **Policy Check** → Policy Verification validates coverage
4. **Document Analysis** → Document Analyzer processes attachments with **OCR**
5. **Decision Making** → Decision Maker provides final verdict
7. **Result Display** → Results shown to user

## 🛠️ API Endpoints

- `POST /api/claims/submit` - Submit new claim
- `GET /api/claims/{claim_id}` - Get claim status
- `GET /api/claims` - List all claims
- `POST /api/claims/{claim_id}/analyze` - Trigger AI analysis
- `GET /api/claims/{claim_id}/results` - Get analysis results

## 🎨 Features

- ✅ Real-time claim processing
- ✅ Multi-agent AI analysis
- ✅ Fraud detection
- ✅ Policy verification
- ✅ Document analysis
- ✅ Semantic search in claims history
- ✅ Interactive dashboard
- ✅ Status tracking
- ✅ Detailed explanations for decisions

## 🔐 Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key
QDRANT_HOST=localhost
QDRANT_PORT=6333
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

## 📊 Demo Scenarios

See `docs/demo-script.md` for detailed hackathon demo scenarios.

## 🤝 Contributing

This is a hackathon prototype. For improvements, please create an issue first.

## 📄 License

MIT License - See LICENSE file for details

## 👥 Team

Built for AI Hackathon Competition

---

**Note**: This is a prototype for demonstration purposes. For production use, additional security, error handling, and testing should be implemented.
