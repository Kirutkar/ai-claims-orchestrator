from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ClaimStatus(str, Enum):
    SUBMITTED = "submitted"
    VALIDATING = "validating"
    FRAUD_CHECK = "fraud_check"
    POLICY_CHECK = "policy_check"
    DOCUMENT_ANALYSIS = "document_analysis"
    DECISION_PENDING = "decision_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"


class ClaimType(str, Enum):
    HEALTH = "health"
    AUTO = "auto"
    HOME = "home"
    LIFE = "life"


class ClaimSubmission(BaseModel):
    policy_number: str = Field(..., description="Insurance policy number")
    claim_type: ClaimType = Field(..., description="Type of insurance claim")
    claim_amount: float = Field(..., gt=0, description="Claimed amount")
    incident_date: str = Field(..., description="Date of incident (YYYY-MM-DD)")
    description: str = Field(..., min_length=20, description="Detailed description of the claim")
    claimant_name: str = Field(..., description="Name of the claimant")
    claimant_email: str = Field(..., description="Email of the claimant")
    documents: Optional[List[str]] = Field(default=[], description="List of document URLs/paths")


class AgentResult(BaseModel):
    agent_name: str
    status: str  # "passed", "failed", "warning"
    confidence: float = Field(ge=0.0, le=1.0)
    findings: str
    recommendations: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class ClaimAnalysis(BaseModel):
    claim_id: str
    validation_result: Optional[AgentResult] = None
    fraud_result: Optional[AgentResult] = None
    policy_result: Optional[AgentResult] = None
    document_result: Optional[AgentResult] = None
    final_decision: Optional[AgentResult] = None
    overall_status: ClaimStatus
    processing_time: Optional[float] = None  # in seconds


class Claim(BaseModel):
    claim_id: str
    submission: ClaimSubmission
    status: ClaimStatus = ClaimStatus.SUBMITTED
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    analysis: Optional[ClaimAnalysis] = None


class ClaimResponse(BaseModel):
    claim_id: str
    status: ClaimStatus
    message: str
    created_at: datetime


class ClaimStatusResponse(BaseModel):
    claim_id: str
    status: ClaimStatus
    current_step: str
    progress_percentage: int
    analysis: Optional[ClaimAnalysis] = None
    updated_at: datetime


class AnalysisTriggerResponse(BaseModel):
    claim_id: str
    message: str
    status: str
