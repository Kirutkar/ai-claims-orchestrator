"""
Review endpoints for human-in-the-loop functionality
"""
from fastapi import HTTPException
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from models.schemas import (
    ClaimStatus, ReviewDecisionRequest, ReviewDecisionResponse,
    ReviewQueueResponse, ReviewQueueItem, ReviewDetailResponse,
    ReviewAction, Claim
)
from workflow.opus_executor import WorkflowStage, StageStatus


# Review endpoints for human-in-the-loop
def get_review_queue_endpoint(claims_db: Dict[str, Claim], status: str = "pending", priority: str = None):
    """
    Get queue of claims awaiting review
    
    Returns claims that require human analyst review
    """
    queue_items = []
    
    for claim_id, claim in claims_db.items():
        # Filter claims that require review
        if claim.status == ClaimStatus.REVIEW_REQUIRED:
            # Determine priority
            priority_level = "standard"
            if claim.analysis:
                if claim.analysis.fraud_result:
                    fraud_risk = claim.analysis.fraud_result.metadata.get("fraud_risk", 0)
                    if fraud_risk >= 0.8:
                        priority_level = "high"
                
                if claim.analysis.final_decision:
                    if claim.analysis.final_decision.confidence < 0.5:
                        priority_level = "high"
            
            # Determine review reason
            review_reason = "Manual review required"
            if claim.analysis and claim.analysis.final_decision:
                if claim.analysis.final_decision.confidence < 0.7:
                    review_reason = f"Low confidence ({claim.analysis.final_decision.confidence:.2f})"
            
            queue_items.append(ReviewQueueItem(
                claim_id=claim_id,
                priority=priority_level,
                requires_review_reason=review_reason,
                ai_confidence=claim.analysis.final_decision.confidence if claim.analysis and claim.analysis.final_decision else None,
                risk_score=claim.analysis.fraud_result.metadata.get("fraud_risk") if claim.analysis and claim.analysis.fraud_result and claim.analysis.fraud_result.metadata.get("fraud_risk") is not None else None,
                claim_type=claim.submission.claim_type.value,
                claim_amount=claim.submission.claim_amount,
                created_at=claim.created_at,
                updated_at=claim.updated_at
            ))
    
    # Filter by priority if specified
    if priority:
        queue_items = [item for item in queue_items if item.priority == priority]
    
    # Sort by priority (high first) then by updated_at
    queue_items.sort(key=lambda x: (x.priority == "high", x.updated_at), reverse=True)
    
    return ReviewQueueResponse(
        claims=queue_items,
        total=len(queue_items)
    )


async def get_review_details_endpoint(claim_id: str, claims_db: Dict[str, Claim], workflow_executor=None):
    """
    Get detailed information for a claim ready for review
    
    Returns all information an analyst needs to make a decision
    """
    if claim_id not in claims_db:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    
    claim = claims_db[claim_id]
    
    if claim.status != ClaimStatus.REVIEW_REQUIRED:
        raise HTTPException(
            status_code=400, 
            detail=f"Claim {claim_id} is not in review status. Current status: {claim.status}"
        )
    
    # Build claim summary
    claim_summary = {
        "claim_id": claim.claim_id,
        "policy_number": claim.submission.policy_number,
        "claim_type": claim.submission.claim_type.value,
        "claim_amount": claim.submission.claim_amount,
        "incident_date": claim.submission.incident_date,
        "claimant_name": claim.submission.claimant_name,
        "claimant_email": claim.submission.claimant_email,
        "description": claim.submission.description,
        "documents": claim.submission.documents,
        "created_at": claim.created_at.isoformat(),
        "updated_at": claim.updated_at.isoformat()
    }
    
    # Build AI recommendation
    ai_recommendation = {}
    if claim.analysis and claim.analysis.final_decision:
        ai_recommendation = {
            "payout": None,  # Extract from findings if available
            "confidence": claim.analysis.final_decision.confidence,
            "risk_score": claim.analysis.fraud_result.metadata.get("fraud_risk") if claim.analysis.fraud_result else None,
            "status": claim.analysis.final_decision.status,
            "findings": claim.analysis.final_decision.findings,
            "recommendations": claim.analysis.final_decision.recommendations
        }
    
    # Get similar claims from workflow state if available
    similar_claims = []
    if claim.analysis:
        # First try to get from workflow state
        if workflow_executor:
            workflow_state = workflow_executor.get_workflow_state(claim_id)
            if workflow_state and workflow_state.workflow_data.get("similar_claims"):
                similar_claims = workflow_state.workflow_data["similar_claims"]
        
        # Fallback: retrieve from Qdrant directly
        if not similar_claims:
            try:
                from orchestrator import ClaimsOrchestrator
                orchestrator = ClaimsOrchestrator()
                if orchestrator.qdrant_client:
                    claim_data = claim.submission.model_dump()
                    similar_claims_list = await orchestrator._find_similar_claims(claim_data)
                    similar_claims = [
                        {
                            "claim_id": sc.get("claim_id", "N/A"),
                            "description": sc.get("description", "N/A"),
                            "amount": sc.get("amount", 0),
                            "status": sc.get("status", "unknown"),
                            "similarity_score": sc.get("similarity_score", 0)
                        }
                        for sc in similar_claims_list
                    ]
            except Exception as e:
                print(f"Error retrieving similar claims: {e}")
                similar_claims = []
    
    # Build flags
    flags = []
    if claim.analysis:
        if claim.analysis.validation_result and claim.analysis.validation_result.status == "failed":
            flags.append({
                "type": "validation_failed",
                "severity": "high",
                "message": "Claim validation failed"
            })
        
        if claim.analysis.fraud_result and claim.analysis.fraud_result.status == "warning":
            fraud_risk = claim.analysis.fraud_result.metadata.get("fraud_risk", 0)
            flags.append({
                "type": "fraud_risk",
                "severity": "high" if fraud_risk >= 0.8 else "medium",
                "message": f"Fraud risk detected: {fraud_risk:.2f}"
            })
        
        if claim.analysis.final_decision and claim.analysis.final_decision.confidence < 0.7:
            flags.append({
                "type": "low_confidence",
                "severity": "medium",
                "message": f"Low AI confidence: {claim.analysis.final_decision.confidence:.2f}"
            })
    
    # Build extracted facts
    extracted_facts = {}
    if claim.analysis:
        extracted_facts = {
            "validation": claim.analysis.validation_result.model_dump() if claim.analysis.validation_result else None,
            "fraud": claim.analysis.fraud_result.model_dump() if claim.analysis.fraud_result else None,
            "policy": claim.analysis.policy_result.model_dump() if claim.analysis.policy_result else None,
            "documents": claim.analysis.document_result.model_dump() if claim.analysis.document_result else None
        }
    
    # Determine review reason
    review_reason = None
    if claim.analysis and claim.analysis.final_decision:
        if claim.analysis.final_decision.confidence < 0.7:
            review_reason = f"Low AI confidence ({claim.analysis.final_decision.confidence:.2f} < 0.70)"
    
    return ReviewDetailResponse(
        claim_id=claim_id,
        claim_summary=claim_summary,
        ai_recommendation=ai_recommendation,
        similar_claims=similar_claims,
        flags=flags,
        extracted_facts=extracted_facts,
        requires_review=True,
        review_reason=review_reason,
        analysis=claim.analysis
    )


async def submit_review_decision_endpoint(claim_id: str, decision: ReviewDecisionRequest, claims_db: Dict[str, Claim], audit_logs: List[Dict], workflow_executor=None):
    """
    Submit analyst decision for a claim under review
    
    Actions: approve, modify, escalate, request_info
    After approve/modify, triggers Opus Deliver stage
    """
    if claim_id not in claims_db:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
    
    claim = claims_db[claim_id]
    
    if claim.status != ClaimStatus.REVIEW_REQUIRED:
        raise HTTPException(
            status_code=400,
            detail=f"Claim {claim_id} is not in review status. Current status: {claim.status}"
        )
    
    # Generate audit log ID
    audit_log_id = f"AUDIT-{uuid.uuid4().hex[:8].upper()}"
    
    # Get workflow state
    workflow_state = workflow_executor.get_workflow_state(claim_id) if workflow_executor else None
    
    # Process decision based on action
    if decision.action == ReviewAction.APPROVE:
        claim.status = ClaimStatus.APPROVED
        next_stage = "deliver"
        message = "Claim approved by analyst"
        
        # Transition workflow to Deliver stage
        if workflow_state:
            workflow_state.transition_to(WorkflowStage.DELIVER, StageStatus.IN_PROGRESS)
            workflow_state.add_stage_event(
                WorkflowStage.REVIEW,
                StageStatus.COMPLETED,
                "Review completed - Approved",
                {"action": "approve", "reason": decision.reason}
            )
            # Execute Deliver stage
            if claim.analysis and workflow_executor:
                try:
                    await workflow_executor._execute_deliver_stage(
                        claim.submission,
                        claim_id,
                        workflow_state,
                        claim.analysis,
                        None
                    )
                except Exception as e:
                    # Fallback: just mark as completed
                    workflow_state.add_stage_event(
                        WorkflowStage.DELIVER,
                        StageStatus.COMPLETED,
                        f"Delivery stage completed (with error: {str(e)})",
                        {"final_status": claim.status.value}
                    )
        
    elif decision.action == ReviewAction.MODIFY:
        if not decision.modified_payout:
            raise HTTPException(
                status_code=400,
                detail="modified_payout is required when action is 'modify'"
            )
        claim.status = ClaimStatus.APPROVED
        next_stage = "deliver"
        message = f"Claim modified by analyst. Payout changed to ${decision.modified_payout}"
        # Store modification in metadata
        if not hasattr(claim, 'metadata'):
            claim.metadata = {}
        claim.metadata['modified_payout'] = decision.modified_payout
        claim.metadata['original_payout'] = claim.analysis.final_decision.confidence if claim.analysis and claim.analysis.final_decision else None
        
        # Transition workflow to Deliver stage
        if workflow_state:
            workflow_state.transition_to(WorkflowStage.DELIVER, StageStatus.IN_PROGRESS)
            workflow_state.add_stage_event(
                WorkflowStage.REVIEW,
                StageStatus.COMPLETED,
                "Review completed - Modified",
                {"action": "modify", "modified_payout": decision.modified_payout, "reason": decision.reason}
            )
            # Execute Deliver stage
            if claim.analysis and workflow_executor:
                try:
                    await workflow_executor._execute_deliver_stage(
                        claim.submission,
                        claim_id,
                        workflow_state,
                        claim.analysis,
                        None
                    )
                except Exception as e:
                    workflow_state.add_stage_event(
                        WorkflowStage.DELIVER,
                        StageStatus.COMPLETED,
                        f"Delivery stage completed (with error: {str(e)})",
                        {"final_status": claim.status.value}
                    )
        
    elif decision.action == ReviewAction.ESCALATE:
        if not decision.escalation_reason:
            raise HTTPException(
                status_code=400,
                detail="escalation_reason is required when action is 'escalate'"
            )
        claim.status = ClaimStatus.ESCALATED
        next_stage = "senior_review"
        message = f"Claim escalated to senior adjuster: {decision.escalation_reason}"
        
        # Log escalation in workflow
        if workflow_state:
            workflow_state.add_stage_event(
                WorkflowStage.REVIEW,
                StageStatus.COMPLETED,
                "Review completed - Escalated",
                {"action": "escalate", "escalation_reason": decision.escalation_reason, "reason": decision.reason}
            )
        
    elif decision.action == ReviewAction.REQUEST_INFO:
        if not decision.requested_documents:
            raise HTTPException(
                status_code=400,
                detail="requested_documents is required when action is 'request_info'"
            )
        claim.status = ClaimStatus.NEEDS_INFO
        next_stage = "intake"  # Loop back to intake for additional info
        message = f"Additional information requested: {', '.join(decision.requested_documents)}"
        # Store requested documents
        if not hasattr(claim, 'metadata'):
            claim.metadata = {}
        claim.metadata['requested_documents'] = decision.requested_documents
        
        # Transition workflow back to Intake stage
        if workflow_state:
            workflow_state.transition_to(WorkflowStage.INTAKE, StageStatus.PENDING)
            workflow_state.add_stage_event(
                WorkflowStage.REVIEW,
                StageStatus.COMPLETED,
                "Review completed - Info Requested",
                {"action": "request_info", "requested_documents": decision.requested_documents, "reason": decision.reason}
            )
    
    claim.updated_at = datetime.now()
    
    # Log audit entry
    audit_logs.append({
        "audit_log_id": audit_log_id,
        "claim_id": claim_id,
        "timestamp": datetime.now().isoformat(),
        "action": decision.action.value,
        "analyst_id": decision.analyst_id,
        "reason": decision.reason,
        "modified_payout": decision.modified_payout,
        "escalation_reason": decision.escalation_reason,
        "requested_documents": decision.requested_documents,
        "previous_status": ClaimStatus.REVIEW_REQUIRED.value,
        "new_status": claim.status.value,
        "next_stage": next_stage,
        "workflow_stage": workflow_state.current_stage.value if workflow_state else None
    })
    
    return ReviewDecisionResponse(
        claim_id=claim_id,
        status=claim.status,
        message=message,
        next_stage=next_stage,
        audit_log_id=audit_log_id,
        updated_at=claim.updated_at
    )

