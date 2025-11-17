from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, List
import uuid
from datetime import datetime

from config import get_settings
from models.schemas import (
    ClaimSubmission, ClaimResponse, ClaimStatusResponse,
    Claim, ClaimStatus, AnalysisTriggerResponse,
    ChatMessage, ChatResponse,
    GuidedChatMessage, GuidedChatResponse
)
from orchestrator import ClaimsOrchestrator
from utils.file_storage import file_storage
from pydantic import BaseModel
from agents.adjuster_brief_agent import generate_adjuster_brief

# Initialize FastAPI app
app = FastAPI(
    title="AI Claims Orchestrator",
    description="Intelligent insurance claims processing using multi-agent AI system",
    version="1.0.0"
)

# Get settings
settings = get_settings()

# Add this inside your end-to-end claim analyzer:
def finalize_claim_output(claim_structured):
    # Your decision engine has already produced structured JSON
    adjuster_brief = generate_adjuster_brief(claim_structured)
    claim_structured["adjuster_brief"] = adjuster_brief
    return claim_structured

# Configure CORS - Handle origins properly
def get_cors_origins():
    """Parse CORS origins from config, handling whitespace and empty strings"""
    origins_str = settings.cors_origins or ""
    origins = [origin.strip() for origin in origins_str.split(',') if origin.strip()]
    
    # Add common development origins if not already present
    default_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:3001",  # Additional common port
    ]
    
    # Combine and remove duplicates
    all_origins = list(set(origins + default_origins))
    
    return all_origins

# Configure CORS middleware
# In debug mode, use allow_origin_regex for more flexibility
if settings.debug_mode:
    # Debug mode: Allow all localhost and 127.0.0.1 origins
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,
    )
else:
    # Production mode: Use specific origins only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,
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
            "analyze": "/api/claims/{claim_id}/analyze",
            "chat": "/api/chat/message",
            "chat_guidance": "/api/chat/claim-guidance",
            "guided_submission": "/api/chat/guided-submission"
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


class ClaimData(BaseModel):
    claim_json: dict

@app.post("/generate-adjuster-brief")
def generate_brief(data: ClaimData):
    brief = generate_adjuster_brief(data.claim_json)
    return {"adjuster_brief": brief}


@app.post("/api/claims/submit", response_model=ClaimResponse)
async def submit_claim(claim: ClaimSubmission):
    """
    Submit a new insurance claim for processing
    
    The claim will be validated and queued for AI analysis
    
    Args:
        claim: Claim submission data (includes temp_claim_id if files were uploaded before submission)
    """
    # Generate unique claim ID
    claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    
    # If temp_claim_id provided and files exist, migrate them to the new claim ID
    temp_claim_id = claim.temp_claim_id
    if temp_claim_id:
        try:
            migrated_files = file_storage.migrate_claim_files(temp_claim_id, claim_id)
            # Update claim documents with migrated file paths
            if migrated_files:
                if not claim.documents:
                    claim.documents = migrated_files
                else:
                    # Merge with existing documents (avoid duplicates)
                    existing_paths = set(claim.documents)
                    new_paths = [p for p in migrated_files if p not in existing_paths]
                    claim.documents = list(claim.documents) + new_paths
        except Exception as e:
            print(f"Warning: Could not migrate files from {temp_claim_id}: {e}")
    
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


@app.post("/api/claims/{claim_id}/documents")
async def upload_claim_document(claim_id: str, file: UploadFile = File(...)):
    """
    Upload a document for a claim
    
    Documents are stored in claims/{claim_id}/documents/ folder
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Save file
        file_path = file_storage.save_file(claim_id, file_content, file.filename)
        
        return {
            "claim_id": claim_id,
            "filename": file.filename,
            "saved_path": file_path,
            "message": "Document uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.get("/api/claims/{claim_id}/documents")
async def list_claim_documents(claim_id: str):
    """
    List all documents for a claim
    """
    try:
        documents = file_storage.get_claim_documents(claim_id)
        return {
            "claim_id": claim_id,
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.get("/api/claims/{claim_id}/documents/{filename}")
async def get_claim_document(claim_id: str, filename: str):
    """
    Download a specific document for a claim
    """
    try:
        from pathlib import Path
        claim_dir = file_storage.get_claim_dir(claim_id)
        file_path = claim_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")


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
        # Define status update callback to update claim status in real-time
        def update_claim_status(new_status: ClaimStatus):
            claim.status = new_status
            claim.updated_at = datetime.now()
            print(f"[{claim_id}] Status updated to: {new_status}")
        
        # Update status to validating
        claim.status = ClaimStatus.VALIDATING
        claim.updated_at = datetime.now()
        
        # Run the orchestrator asynchronously with status update callback
        analysis = await orchestrator.process_claim(
            claim.submission, 
            claim_id,
            status_update_callback=update_claim_status
        )
        
        # Update claim with analysis results and final status
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


# Chat endpoints
@app.post("/api/chat/message", response_model=ChatResponse)
async def chat_message(chat_request: ChatMessage):
    """
    Send a message to the AI chat assistant
    
    The assistant can help with:
    - Claim submission guidance
    - Claim status questions
    - Policy questions
    - General insurance questions
    """
    try:
        # Build context from request
        context = chat_request.context or {}
        
        # If claim_id is provided in context, fetch claim data
        if context.get("claim_id"):
            claim_id = context["claim_id"]
            if claim_id in claims_db:
                claim = claims_db[claim_id]
                context["claim_data"] = {
                    "policy_number": claim.submission.policy_number,
                    "claim_type": claim.submission.claim_type,
                    "claim_amount": claim.submission.claim_amount,
                    "status": claim.status,
                    "claim_id": claim_id
                }
        
        # Get user's claims if available
        if context.get("user_email"):
            user_claims = [
                {
                    "claim_id": c.claim_id,
                    "status": c.status,
                    "claim_type": c.submission.claim_type
                }
                for c in claims_db.values()
                if c.submission.claimant_email == context["user_email"]
            ]
            context["available_claims"] = user_claims
        
        # Get response from chat agent
        response = await orchestrator.chat_agent.chat(
            user_message=chat_request.message,
            context=context,
            conversation_id=chat_request.conversation_id
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )


@app.post("/api/chat/claim-guidance", response_model=ChatResponse)
async def claim_guidance_chat(chat_request: ChatMessage):
    """
    Specialized endpoint for claim submission guidance
    Provides step-by-step help for submitting claims
    """
    try:
        # Add claim guidance context
        context = chat_request.context or {}
        context["mode"] = "claim_guidance"
        
        # Enhance message with guidance context
        enhanced_message = f"""
User is asking about claim submission. Provide step-by-step guidance.
User message: {chat_request.message}

Help them understand:
1. What information they need
2. How to fill out the form
3. What documents to upload
4. What happens after submission
"""
        
        response = await orchestrator.chat_agent.chat(
            user_message=enhanced_message,
            context=context,
            conversation_id=chat_request.conversation_id
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )


@app.post("/api/chat/guided-submission", response_model=GuidedChatResponse)
async def guided_submission_chat(chat_request: GuidedChatMessage):
    """
    Guided claim submission endpoint
    Asks questions one by one and collects all required information
    """
    try:
        # Get or initialize collected data
        collected_data = chat_request.collected_data or {}
        
        # Process message with guided chat agent
        response = await orchestrator.guided_chat_agent.process_message(
            user_message=chat_request.message,
            collected_data=collected_data,
            conversation_id=chat_request.conversation_id
        )
        
        return GuidedChatResponse(**response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Guided chat error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug_mode
    )
