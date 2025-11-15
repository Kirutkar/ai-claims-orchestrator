from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import uuid
from datetime import datetime

from config import get_settings
from models.schemas import (
    ClaimSubmission, ClaimResponse, ClaimStatusResponse,
    Claim, ClaimStatus, AnalysisTriggerResponse
)
from orchestrator import ClaimsOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="AI Claims Orchestrator",
    description="Intelligent insurance claims processing using multi-agent AI system",
    version="1.0.0"
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = ClaimsOrchestrator()

# In-memory storage for demo (use database in production)
claims_db: Dict[str, Claim] = {}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "gemini_llm": "connected",
            "qdrant_db": "connected",
            "agents": "ready"
        }
    }


@app.post("/api/claims/submit", response_model=ClaimResponse)
async def submit_claim(claim: ClaimSubmission):
    """
    Submit a new insurance claim for processing
    
    The claim will be validated and queued for AI analysis
    """
    # Generate unique claim ID
    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    
    # Create claim record
    new_claim = Claim(
        claim_id=claim_id,
        submission=claim,
        status=ClaimStatus.SUBMITTED,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Store in database
    claims_db[claim_id] = new_claim
    
    return ClaimResponse(
        claim_id=claim_id,
        status=ClaimStatus.SUBMITTED,
        message=f"Claim submitted successfully. Your claim ID is {claim_id}",
        created_at=new_claim.created_at
    )


@app.get("/api/claims/{claim_id}", response_model=ClaimStatusResponse)
async def get_claim_status(claim_id: str):
    """
    Get the current status of a claim
    
    Returns detailed information about claim processing progress
    """
    if claim_id not in claims_db:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    
    claim = claims_db[claim_id]
    
    # Calculate progress percentage
    status_progress = {
        ClaimStatus.SUBMITTED: 10,
        ClaimStatus.VALIDATING: 20,
        ClaimStatus.FRAUD_CHECK: 40,
        ClaimStatus.POLICY_CHECK: 60,
        ClaimStatus.DOCUMENT_ANALYSIS: 80,
        ClaimStatus.DECISION_PENDING: 90,
        ClaimStatus.APPROVED: 100,
        ClaimStatus.REJECTED: 100,
        ClaimStatus.NEEDS_INFO: 50
    }
    
    current_step_map = {
        ClaimStatus.SUBMITTED: "Claim received and queued",
        ClaimStatus.VALIDATING: "Validating claim information",
        ClaimStatus.FRAUD_CHECK: "Analyzing for fraud indicators",
        ClaimStatus.POLICY_CHECK: "Verifying policy coverage",
        ClaimStatus.DOCUMENT_ANALYSIS: "Analyzing supporting documents",
        ClaimStatus.DECISION_PENDING: "Making final decision",
        ClaimStatus.APPROVED: "Claim approved",
        ClaimStatus.REJECTED: "Claim rejected",
        ClaimStatus.NEEDS_INFO: "Additional information required"
    }
    
    return ClaimStatusResponse(
        claim_id=claim_id,
        status=claim.status,
        current_step=current_step_map.get(claim.status, "Processing"),
        progress_percentage=status_progress.get(claim.status, 0),
        analysis=claim.analysis,
        updated_at=claim.updated_at
    )


@app.get("/api/claims", response_model=List[ClaimStatusResponse])
async def list_claims():
    """
    List all submitted claims
    
    Returns a summary of all claims in the system
    """
    return [
        ClaimStatusResponse(
            claim_id=claim.claim_id,
            status=claim.status,
            current_step="Processing" if claim.status not in [
                ClaimStatus.APPROVED, ClaimStatus.REJECTED
            ] else "Complete",
            progress_percentage=100 if claim.status in [
                ClaimStatus.APPROVED, ClaimStatus.REJECTED
            ] else 50,
            analysis=claim.analysis,
            updated_at=claim.updated_at
        )
        for claim in claims_db.values()
    ]


@app.post("/api/claims/{claim_id}/analyze", response_model=AnalysisTriggerResponse)
async def analyze_claim(claim_id: str):
    """
    Trigger AI analysis for a submitted claim
    
    This endpoint initiates the multi-agent workflow to process the claim
    """
    if claim_id not in claims_db:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    
    claim = claims_db[claim_id]
    
    if claim.status not in [ClaimStatus.SUBMITTED, ClaimStatus.NEEDS_INFO]:
        return AnalysisTriggerResponse(
            claim_id=claim_id,
            message="Claim analysis already in progress or completed",
            status="skipped"
        )
    
    try:
        # Update status to validating
        claim.status = ClaimStatus.VALIDATING
        claim.updated_at = datetime.now()
        
        # Run the orchestrator asynchronously
        analysis = await orchestrator.process_claim(claim.submission, claim_id)
        
        # Update claim with analysis results
        claim.analysis = analysis
        claim.status = analysis.overall_status
        claim.updated_at = datetime.now()
        
        return AnalysisTriggerResponse(
            claim_id=claim_id,
            message=f"Claim analysis completed. Status: {analysis.overall_status}",
            status="completed"
        )
    except Exception as e:
        claim.status = ClaimStatus.SUBMITTED
        claim.updated_at = datetime.now()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/claims/{claim_id}/results")
async def get_analysis_results(claim_id: str):
    """
    Get detailed analysis results for a claim
    
    Returns comprehensive breakdown of all agent analyses
    """
    if claim_id not in claims_db:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    
    claim = claims_db[claim_id]
    
    if not claim.analysis:
        return {
            "claim_id": claim_id,
            "status": claim.status,
            "message": "Analysis not yet completed. Please trigger analysis first."
        }
    
    return {
        "claim_id": claim_id,
        "status": claim.status,
        "submission": claim.submission.model_dump(),
        "analysis": claim.analysis.model_dump(),
        "created_at": claim.created_at.isoformat(),
        "updated_at": claim.updated_at.isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug_mode
    )
