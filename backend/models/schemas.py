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
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"
    ESCALATED = "escalated"


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
    temp_claim_id: Optional[str] = Field(None, description="Temporary claim ID for file migration")


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


# Chat-related schemas
class ChatMessage(BaseModel):
    message: str = Field(..., description="User's chat message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for history")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Optional context (claim_id, etc.)")


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant's response")
    suggestions: List[str] = Field(default=[], description="Suggested next actions")
    intent: str = Field(..., description="Detected user intent")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    timestamp: str = Field(..., description="Response timestamp")


class GuidedChatMessage(BaseModel):
    message: str = Field(..., description="User's chat message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for history")
    collected_data: Optional[Dict[str, Any]] = Field(default={}, description="Previously collected claim data")


class GuidedChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant's response")
    next_field: Optional[str] = Field(None, description="Next field to collect")
    collected_data: Dict[str, Any] = Field(..., description="Updated collected data")
    is_complete: bool = Field(..., description="Whether all required fields are collected")
    ready_to_submit: bool = Field(default=False, description="Whether claim is ready to submit")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    timestamp: str = Field(..., description="Response timestamp")


# Review-related schemas
class ReviewAction(str, Enum):
    APPROVE = "approve"
    MODIFY = "modify"
    ESCALATE = "escalate"
    REQUEST_INFO = "request_info"


class ReviewDecisionRequest(BaseModel):
    action: ReviewAction = Field(..., description="Review action to take")
    modified_payout: Optional[float] = Field(None, description="Modified payout amount (if action=modify)")
    reason: str = Field(..., description="Reason for the decision")
    escalation_reason: Optional[str] = Field(None, description="Escalation reason (if action=escalate)")
    requested_documents: Optional[List[str]] = Field(default=[], description="Requested document types (if action=request_info)")
    analyst_id: Optional[str] = Field(None, description="Analyst ID performing the review")


class ReviewDecisionResponse(BaseModel):
    claim_id: str
    status: ClaimStatus
    message: str
    next_stage: str
    audit_log_id: str
    updated_at: datetime


class ReviewQueueItem(BaseModel):
    claim_id: str
    priority: str
    requires_review_reason: str
    ai_confidence: Optional[float] = None
    risk_score: Optional[float] = None
    claim_type: str
    claim_amount: float
    created_at: datetime
    updated_at: datetime


class ReviewQueueResponse(BaseModel):
    claims: List[ReviewQueueItem]
    total: int


class ReviewDetailResponse(BaseModel):
    claim_id: str
    claim_summary: Dict[str, Any]
    ai_recommendation: Dict[str, Any]
    similar_claims: List[Dict[str, Any]]
    flags: List[Dict[str, Any]]
    extracted_facts: Dict[str, Any]
    requires_review: bool
    review_reason: Optional[str] = None
    analysis: Optional[ClaimAnalysis] = None
