# AI Claims Orchestrator - API Reference

## Base URL
```
http://localhost:8000
```

## Authentication
Current version does not require authentication (demo purposes).

---

## Endpoints

### 1. Root Information
**GET** `/`

Get basic API information and available endpoints.

**Response:**
```json
{
  "name": "AI Claims Orchestrator",
  "version": "1.0.0",
  "status": "operational",
  "endpoints": {
    "submit": "/api/claims/submit",
    "status": "/api/claims/{claim_id}",
    "list": "/api/claims",
    "analyze": "/api/claims/{claim_id}/analyze"
  }
}
```

---

### 2. Health Check
**GET** `/health`

Check the health status of the API and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-15T10:30:00",
  "services": {
    "gemini_llm": "connected",
    "qdrant_db": "connected",
    "agents": "ready"
  }
}
```

---

### 3. Submit Claim
**POST** `/api/claims/submit`

Submit a new insurance claim for processing.

**Request Body:**
```json
{
  "policy_number": "POL-123456",
  "claim_type": "health",
  "claim_amount": 5000.00,
  "incident_date": "2025-11-10",
  "description": "Emergency room visit for broken arm during sports activity. Required X-rays and casting.",
  "claimant_name": "John Doe",
  "claimant_email": "john.doe@example.com",
  "documents": []
}
```

**Field Descriptions:**
- `policy_number` (string, required): Insurance policy number
- `claim_type` (enum, required): Type of claim - "health", "auto", "home", or "life"
- `claim_amount` (float, required): Claimed amount in dollars (must be > 0)
- `incident_date` (string, required): Date of incident (YYYY-MM-DD format)
- `description` (string, required): Detailed description (minimum 20 characters)
- `claimant_name` (string, required): Name of the claimant
- `claimant_email` (string, required): Email address of the claimant
- `documents` (array, optional): List of document URLs/paths

**Response:**
```json
{
  "claim_id": "CLM-A1B2C3D4",
  "status": "submitted",
  "message": "Claim submitted successfully. Your claim ID is CLM-A1B2C3D4",
  "created_at": "2025-11-15T10:35:00"
}
```

**Status Codes:**
- `200`: Success
- `422`: Validation error (invalid data)
- `500`: Server error

---

### 4. Get Claim Status
**GET** `/api/claims/{claim_id}`

Get the current status and progress of a specific claim.

**Path Parameters:**
- `claim_id` (string, required): The unique claim identifier

**Response:**
```json
{
  "claim_id": "CLM-A1B2C3D4",
  "status": "fraud_check",
  "current_step": "Analyzing for fraud indicators",
  "progress_percentage": 40,
  "analysis": null,
  "updated_at": "2025-11-15T10:36:00"
}
```

**Status Values:**
- `submitted`: Claim received and queued
- `validating`: Validating claim information
- `fraud_check`: Analyzing for fraud indicators
- `policy_check`: Verifying policy coverage
- `document_analysis`: Analyzing supporting documents
- `decision_pending`: Making final decision
- `approved`: Claim approved
- `rejected`: Claim rejected
- `needs_info`: Additional information required

**Status Codes:**
- `200`: Success
- `404`: Claim not found
- `500`: Server error

---

### 5. List All Claims
**GET** `/api/claims`

Get a list of all submitted claims with their current status.

**Response:**
```json
[
  {
    "claim_id": "CLM-A1B2C3D4",
    "status": "approved",
    "current_step": "Complete",
    "progress_percentage": 100,
    "analysis": {...},
    "updated_at": "2025-11-15T10:40:00"
  },
  {
    "claim_id": "CLM-E5F6G7H8",
    "status": "submitted",
    "current_step": "Processing",
    "progress_percentage": 50,
    "analysis": null,
    "updated_at": "2025-11-15T10:38:00"
  }
]
```

**Status Codes:**
- `200`: Success
- `500`: Server error

---

### 6. Analyze Claim
**POST** `/api/claims/{claim_id}/analyze`

Trigger AI-powered analysis for a submitted claim.

**Path Parameters:**
- `claim_id` (string, required): The unique claim identifier

**Response:**
```json
{
  "claim_id": "CLM-A1B2C3D4",
  "message": "Claim analysis completed. Status: approved",
  "status": "completed"
}
```

**Status Codes:**
- `200`: Analysis completed
- `404`: Claim not found
- `500`: Analysis failed

---

### 7. Get Analysis Results
**GET** `/api/claims/{claim_id}/results`

Get detailed AI analysis results for a claim.

**Path Parameters:**
- `claim_id` (string, required): The unique claim identifier

**Response:**
```json
{
  "claim_id": "CLM-A1B2C3D4",
  "status": "approved",
  "submission": {
    "policy_number": "POL-123456",
    "claim_type": "health",
    "claim_amount": 5000.00,
    ...
  },
  "analysis": {
    "claim_id": "CLM-A1B2C3D4",
    "validation_result": {
      "agent_name": "Claim Validator",
      "status": "passed",
      "confidence": 0.92,
      "findings": "All required information is complete and properly formatted...",
      "recommendations": ["Proceed with analysis"]
    },
    "fraud_result": {
      "agent_name": "Fraud Detector",
      "status": "passed",
      "confidence": 0.15,
      "findings": "No significant fraud indicators detected...",
      "recommendations": ["Claim appears legitimate"]
    },
    "policy_result": {
      "agent_name": "Policy Checker",
      "status": "passed",
      "confidence": 0.95,
      "findings": "Policy is active and claim is within coverage limits...",
      "recommendations": ["Policy coverage confirmed"]
    },
    "document_result": {
      "agent_name": "Document Analyzer",
      "status": "warning",
      "confidence": 0.65,
      "findings": "Limited documentation provided...",
      "recommendations": ["Request medical records", "Request receipts"]
    },
    "final_decision": {
      "agent_name": "Decision Maker",
      "status": "approved",
      "confidence": 0.85,
      "findings": "Based on comprehensive analysis, this claim is approved...",
      "recommendations": ["Process payment", "Close claim"]
    },
    "overall_status": "approved",
    "processing_time": 12.45
  },
  "created_at": "2025-11-15T10:35:00",
  "updated_at": "2025-11-15T10:40:00"
}
```

**Status Codes:**
- `200`: Success
- `404`: Claim not found
- `500`: Server error

---

## Agent Results Structure

Each agent returns results in the following format:

```json
{
  "agent_name": "string",
  "status": "passed|failed|warning",
  "confidence": 0.0-1.0,
  "findings": "string",
  "recommendations": ["string"],
  "metadata": {}
}
```

**Agent Types:**
1. **Claim Validator** - Validates data completeness and integrity
2. **Fraud Detector** - Analyzes fraud risk (higher confidence = higher risk)
3. **Policy Checker** - Verifies policy coverage and eligibility
4. **Document Analyzer** - Analyzes supporting documentation
5. **Decision Maker** - Makes final approval/rejection decision

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Codes:**
- `400`: Bad Request - Invalid input
- `404`: Not Found - Resource doesn't exist
- `422`: Validation Error - Data validation failed
- `500`: Internal Server Error - Server-side error

---

## Rate Limiting

Current version does not implement rate limiting (demo purposes). In production, implement:
- 60 requests per minute per IP
- 1000 requests per day per user

---

## Workflow Process

1. **Submit Claim** → `POST /api/claims/submit`
2. **Get Claim ID** → Store `claim_id` from response
3. **Trigger Analysis** → `POST /api/claims/{claim_id}/analyze`
4. **Poll Status** → `GET /api/claims/{claim_id}` (every 5 seconds)
5. **Get Results** → `GET /api/claims/{claim_id}/results` when complete

---

## Code Examples

### Python
```python
import requests

# Submit claim
response = requests.post(
    "http://localhost:8000/api/claims/submit",
    json={
        "policy_number": "POL-123456",
        "claim_type": "health",
        "claim_amount": 5000.00,
        "incident_date": "2025-11-10",
        "description": "Emergency room visit...",
        "claimant_name": "John Doe",
        "claimant_email": "john@example.com",
        "documents": []
    }
)
claim_id = response.json()["claim_id"]

# Trigger analysis
requests.post(f"http://localhost:8000/api/claims/{claim_id}/analyze")

# Get results
results = requests.get(f"http://localhost:8000/api/claims/{claim_id}/results")
print(results.json())
```

### JavaScript
```javascript
// Submit claim
const response = await fetch('http://localhost:8000/api/claims/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    policy_number: 'POL-123456',
    claim_type: 'health',
    claim_amount: 5000.00,
    incident_date: '2025-11-10',
    description: 'Emergency room visit...',
    claimant_name: 'John Doe',
    claimant_email: 'john@example.com',
    documents: []
  })
});
const { claim_id } = await response.json();

// Trigger analysis
await fetch(`http://localhost:8000/api/claims/${claim_id}/analyze`, {
  method: 'POST'
});

// Get results
const results = await fetch(`http://localhost:8000/api/claims/${claim_id}/results`);
console.log(await results.json());
```

---

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can test all endpoints directly.
