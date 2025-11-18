"""
Opus Workflow Executor
Implements the workflow orchestration as defined in workflow.yaml
Provides stage management, transitions, error handling, and audit logging
"""
import yaml
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path

from models.schemas import ClaimSubmission, ClaimAnalysis, ClaimStatus, AgentResult
from orchestrator import ClaimsOrchestrator


class WorkflowStage(str, Enum):
    INTAKE = "intake"
    UNDERSTAND = "understand"  # Maps to claim_validation
    DECIDE = "decide"  # Maps to fraud_detection, policy_verification, document_analysis, final_decision
    REVIEW = "review"
    DELIVER = "deliver"
    COMPLETED = "completed"
    ERROR = "error"


class StageStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowState:
    """Tracks the state of a workflow execution"""
    
    def __init__(self, claim_id: str):
        self.claim_id = claim_id
        self.current_stage = WorkflowStage.INTAKE
        self.stage_status = StageStatus.PENDING
        self.stage_history: List[Dict] = []
        self.workflow_data: Dict[str, Any] = {}
        self.errors: List[Dict] = []
        self.start_time = datetime.now()
        self.last_updated = datetime.now()
    
    def add_stage_event(self, stage: WorkflowStage, status: StageStatus, 
                       message: str, data: Optional[Dict] = None):
        """Add an event to stage history"""
        event = {
            "stage": stage.value,
            "status": status.value,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.stage_history.append(event)
        self.last_updated = datetime.now()
    
    def transition_to(self, stage: WorkflowStage, status: StageStatus = StageStatus.IN_PROGRESS):
        """Transition to a new stage"""
        self.current_stage = stage
        self.stage_status = status
        self.add_stage_event(stage, status, f"Transitioned to {stage.value}")


class OpusWorkflowExecutor:
    """
    Executes the Opus workflow as defined in workflow.yaml
    Orchestrates the multi-agent claim processing pipeline with proper stage management
    """
    
    def __init__(self, orchestrator: ClaimsOrchestrator, workflow_config_path: Optional[str] = None):
        self.orchestrator = orchestrator
        self.workflow_config = self._load_workflow_config(workflow_config_path)
        self.workflow_states: Dict[str, WorkflowState] = {}
    
    def _load_workflow_config(self, config_path: Optional[str]) -> Dict:
        """Load workflow configuration from YAML file"""
        if config_path is None:
            # Default path
            config_path = Path(__file__).parent.parent.parent / "opus" / "workflow.yaml"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Warning: Could not load workflow config: {e}")
            # Return default config structure
            return {
                "workflow": {
                    "stages": [
                        {"name": "claim_validation"},
                        {"name": "fraud_detection"},
                        {"name": "policy_verification"},
                        {"name": "document_analysis"},
                        {"name": "final_decision"}
                    ]
                }
            }
    
    def _get_workflow_state(self, claim_id: str) -> WorkflowState:
        """Get or create workflow state for a claim"""
        if claim_id not in self.workflow_states:
            self.workflow_states[claim_id] = WorkflowState(claim_id)
        return self.workflow_states[claim_id]
    
    async def execute_workflow(
        self,
        claim_submission: ClaimSubmission,
        claim_id: str,
        status_update_callback: Optional[Callable[[ClaimStatus], None]] = None
    ) -> tuple[ClaimAnalysis, WorkflowState]:
        """
        Execute the complete Opus workflow
        
        Stages:
        1. Intake - Validate inputs
        2. Understand - Extract and validate data (claim_validation)
        3. Decide - Multi-agent analysis (fraud, policy, documents, decision)
        4. Review - Human review if needed
        5. Deliver - Finalize and generate outputs
        """
        workflow_state = self._get_workflow_state(claim_id)
        
        try:
            # Stage 1: Intake
            await self._execute_intake_stage(claim_submission, claim_id, workflow_state, status_update_callback)
            
            # Stage 2: Understand (Claim Validation)
            validation_result = await self._execute_understand_stage(
                claim_submission, claim_id, workflow_state, status_update_callback
            )
            
            # Stage 3: Decide (Multi-agent analysis)
            analysis = await self._execute_decide_stage(
                claim_submission, claim_id, workflow_state, validation_result, status_update_callback
            )
            
            # Stage 4: Review (if needed)
            requires_review = await self._check_review_required(analysis, workflow_state)
            
            if requires_review:
                workflow_state.transition_to(WorkflowStage.REVIEW, StageStatus.PENDING)
                workflow_state.add_stage_event(
                    WorkflowStage.REVIEW,
                    StageStatus.PENDING,
                    "Claim requires human review",
                    {"review_reason": workflow_state.workflow_data.get("review_reason")}
                )
                if status_update_callback:
                    status_update_callback(ClaimStatus.REVIEW_REQUIRED)
            else:
                # Skip review, go directly to deliver
                await self._execute_deliver_stage(
                    claim_submission, claim_id, workflow_state, analysis, status_update_callback
                )
            
            workflow_state.add_stage_event(
                WorkflowStage.COMPLETED,
                StageStatus.COMPLETED,
                "Workflow completed successfully"
            )
            
            return analysis, workflow_state
            
        except Exception as e:
            workflow_state.transition_to(WorkflowStage.ERROR, StageStatus.FAILED)
            workflow_state.add_stage_event(
                WorkflowStage.ERROR,
                StageStatus.FAILED,
                f"Workflow failed: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__}
            )
            workflow_state.errors.append({
                "stage": workflow_state.current_stage.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            raise
    
    async def _execute_intake_stage(
        self,
        claim_submission: ClaimSubmission,
        claim_id: str,
        workflow_state: WorkflowState,
        status_update_callback: Optional[Callable]
    ):
        """Stage 1: Intake - Validate inputs and prepare claim"""
        workflow_state.transition_to(WorkflowStage.INTAKE, StageStatus.IN_PROGRESS)
        
        # Validate file formats and required fields
        errors = []
        
        # Validate required fields
        if not claim_submission.policy_number:
            errors.append("Policy number is required")
        if not claim_submission.claim_type:
            errors.append("Claim type is required")
        if claim_submission.claim_amount <= 0:
            errors.append("Claim amount must be positive")
        if not claim_submission.incident_date:
            errors.append("Incident date is required")
        if len(claim_submission.description) < 20:
            errors.append("Description must be at least 20 characters")
        
        # Validate policy number format (basic check)
        if claim_submission.policy_number and len(claim_submission.policy_number) < 3:
            errors.append("Policy number format invalid")
        
        if errors:
            workflow_state.add_stage_event(
                WorkflowStage.INTAKE,
                StageStatus.FAILED,
                f"Intake validation failed: {', '.join(errors)}",
                {"errors": errors}
            )
            raise ValueError(f"Intake validation failed: {', '.join(errors)}")
        
        workflow_state.workflow_data["intake"] = {
            "claim_id": claim_id,
            "policy_number": claim_submission.policy_number,
            "claim_type": claim_submission.claim_type.value,
            "claim_amount": claim_submission.claim_amount,
            "documents_count": len(claim_submission.documents or [])
        }
        
        workflow_state.add_stage_event(
            WorkflowStage.INTAKE,
            StageStatus.COMPLETED,
            "Intake completed successfully",
            workflow_state.workflow_data["intake"]
        )
    
    async def _execute_understand_stage(
        self,
        claim_submission: ClaimSubmission,
        claim_id: str,
        workflow_state: WorkflowState,
        status_update_callback: Optional[Callable]
    ) -> AgentResult:
        """Stage 2: Understand - Claim validation and data extraction"""
        workflow_state.transition_to(WorkflowStage.UNDERSTAND, StageStatus.IN_PROGRESS)
        
        if status_update_callback:
            status_update_callback(ClaimStatus.VALIDATING)
        
        try:
            claim_data = claim_submission.model_dump()
            validation_result = await self.orchestrator.validator.validate(claim_data)
            
            workflow_state.workflow_data["validation"] = {
                "status": validation_result.status,
                "confidence": validation_result.confidence,
                "findings": validation_result.findings
            }
            
            # Check if validation failed
            if validation_result.status == "failed":
                workflow_state.add_stage_event(
                    WorkflowStage.UNDERSTAND,
                    StageStatus.FAILED,
                    "Claim validation failed",
                    {"validation_result": validation_result.model_dump()}
                )
                # Transition to review for manual intervention
                workflow_state.transition_to(WorkflowStage.REVIEW, StageStatus.PENDING)
                if status_update_callback:
                    status_update_callback(ClaimStatus.REVIEW_REQUIRED)
                return validation_result
            
            workflow_state.add_stage_event(
                WorkflowStage.UNDERSTAND,
                StageStatus.COMPLETED,
                f"Understanding completed: {validation_result.status}",
                {"confidence": validation_result.confidence}
            )
            
            return validation_result
            
        except Exception as e:
            workflow_state.add_stage_event(
                WorkflowStage.UNDERSTAND,
                StageStatus.FAILED,
                f"Understanding stage failed: {str(e)}",
                {"error": str(e)}
            )
            raise
    
    async def _execute_decide_stage(
        self,
        claim_submission: ClaimSubmission,
        claim_id: str,
        workflow_state: WorkflowState,
        validation_result: AgentResult,
        status_update_callback: Optional[Callable]
    ) -> ClaimAnalysis:
        """Stage 3: Decide - Multi-agent analysis and decision making"""
        workflow_state.transition_to(WorkflowStage.DECIDE, StageStatus.IN_PROGRESS)
        
        claim_data = claim_submission.model_dump()
        
        # Sub-stage 3.1: Fraud Detection
        if status_update_callback:
            status_update_callback(ClaimStatus.FRAUD_CHECK)
        workflow_state.add_stage_event(
            WorkflowStage.DECIDE,
            StageStatus.IN_PROGRESS,
            "Fraud detection in progress"
        )
        
        similar_claims = await self.orchestrator._find_similar_claims(claim_data)
        fraud_result = await self.orchestrator.fraud_detector.analyze(claim_data, similar_claims)
        
        # Store similar claims in workflow data for review stage
        workflow_state.workflow_data["similar_claims"] = similar_claims
        
        workflow_state.workflow_data["fraud"] = {
            "status": fraud_result.status,
            "confidence": fraud_result.confidence,
            "risk_score": fraud_result.metadata.get("fraud_risk", 0)
        }
        
        # Sub-stage 3.2: Policy Verification
        if status_update_callback:
            status_update_callback(ClaimStatus.POLICY_CHECK)
        workflow_state.add_stage_event(
            WorkflowStage.DECIDE,
            StageStatus.IN_PROGRESS,
            "Policy verification in progress"
        )
        
        policy_result = await self.orchestrator.policy_checker.verify(claim_data)
        
        workflow_state.workflow_data["policy"] = {
            "status": policy_result.status,
            "confidence": policy_result.confidence
        }
        
        # Sub-stage 3.3: Document Analysis
        if status_update_callback:
            status_update_callback(ClaimStatus.DOCUMENT_ANALYSIS)
        workflow_state.add_stage_event(
            WorkflowStage.DECIDE,
            StageStatus.IN_PROGRESS,
            "Document analysis in progress"
        )
        
        document_result = await self.orchestrator.document_analyzer.analyze(claim_data, claim_id=claim_id)
        
        workflow_state.workflow_data["documents"] = {
            "status": document_result.status,
            "confidence": document_result.confidence
        }
        
        # Sub-stage 3.4: Final Decision
        if status_update_callback:
            status_update_callback(ClaimStatus.DECISION_PENDING)
        workflow_state.add_stage_event(
            WorkflowStage.DECIDE,
            StageStatus.IN_PROGRESS,
            "Final decision making in progress"
        )
        
        final_decision, claim_status = await self.orchestrator.decision_maker.decide(
            claim_data,
            validation_result,
            fraud_result,
            policy_result,
            document_result
        )
        
        # Store claim in Qdrant
        await self.orchestrator._store_claim_in_qdrant(claim_id, claim_data, final_decision)
        
        # Build complete analysis
        analysis = ClaimAnalysis(
            claim_id=claim_id,
            validation_result=validation_result,
            fraud_result=fraud_result,
            policy_result=policy_result,
            document_result=document_result,
            final_decision=final_decision,
            overall_status=claim_status,
            processing_time=0  # Will be calculated in main workflow
        )
        
        workflow_state.workflow_data["decision"] = {
            "status": claim_status.value,
            "confidence": final_decision.confidence,
            "recommended_payout": final_decision.metadata.get("recommended_payout"),
            "risk_score": fraud_result.metadata.get("fraud_risk", 0)
        }
        
        workflow_state.add_stage_event(
            WorkflowStage.DECIDE,
            StageStatus.COMPLETED,
            f"Decision completed: {claim_status.value}",
            {
                "confidence": final_decision.confidence,
                "status": claim_status.value
            }
        )
        
        return analysis
    
    async def _check_review_required(self, analysis: ClaimAnalysis, workflow_state: WorkflowState) -> bool:
        """Check if claim requires human review based on business rules"""
        requires_review = False
        review_reason = None
        
        # Check confidence threshold (< 70%)
        if analysis.final_decision and analysis.final_decision.confidence < 0.7:
            requires_review = True
            review_reason = f"Low AI confidence ({analysis.final_decision.confidence:.2f} < 0.70)"
        
        # Check risk score (HIGH risk requires review)
        if analysis.fraud_result and analysis.fraud_result.status == "warning":
            fraud_risk = analysis.fraud_result.metadata.get("fraud_risk", 0)
            if fraud_risk >= 0.8:
                requires_review = True
                review_reason = f"High fraud risk detected ({fraud_risk:.2f})"
        
        # Check for anomalies in validation
        if analysis.validation_result and analysis.validation_result.status == "failed":
            requires_review = True
            review_reason = "Validation failed - requires manual review"
        
        workflow_state.workflow_data["review_required"] = requires_review
        workflow_state.workflow_data["review_reason"] = review_reason
        
        return requires_review
    
    async def _execute_deliver_stage(
        self,
        claim_submission: ClaimSubmission,
        claim_id: str,
        workflow_state: WorkflowState,
        analysis: ClaimAnalysis,
        status_update_callback: Optional[Callable]
    ):
        """Stage 5: Deliver - Finalize claim and generate outputs"""
        workflow_state.transition_to(WorkflowStage.DELIVER, StageStatus.IN_PROGRESS)
        
        # Generate adjuster brief
        adjuster_brief = self._generate_adjuster_brief(claim_submission, analysis)
        
        # Generate claimant message template
        claimant_message = self._generate_claimant_message(claim_submission, analysis)
        
        # Check if SIU alert needed
        siu_alert = None
        if analysis.fraud_result and analysis.fraud_result.metadata.get("fraud_risk", 0) >= 0.7:
            siu_alert = {
                "alert": True,
                "reason": "High fraud risk detected",
                "risk_score": analysis.fraud_result.metadata.get("fraud_risk", 0)
            }
        
        workflow_state.workflow_data["deliver"] = {
            "adjuster_brief": adjuster_brief,
            "claimant_message": claimant_message,
            "siu_alert": siu_alert,
            "final_status": analysis.overall_status.value,
            "final_decision": analysis.final_decision.model_dump() if analysis.final_decision else None
        }
        
        workflow_state.add_stage_event(
            WorkflowStage.DELIVER,
            StageStatus.COMPLETED,
            f"Delivery completed: {analysis.overall_status.value}",
            {"final_status": analysis.overall_status.value}
        )
        
        if status_update_callback:
            status_update_callback(analysis.overall_status)
    
    def _generate_adjuster_brief(self, claim_submission: ClaimSubmission, analysis: ClaimAnalysis) -> str:
        """Generate adjuster brief summary"""
        brief_parts = [
            f"Claim ID: {analysis.claim_id}",
            f"Policy: {claim_submission.policy_number}",
            f"Type: {claim_submission.claim_type.value.upper()}",
            f"Amount: ${claim_submission.claim_amount:,.2f}",
            "",
            "Analysis Summary:",
            f"- Validation: {analysis.validation_result.status.upper() if analysis.validation_result else 'N/A'}",
            f"- Fraud Risk: {analysis.fraud_result.metadata.get('fraud_risk', 0):.2%}" if analysis.fraud_result else "",
            f"- Policy Compliance: {analysis.policy_result.status.upper() if analysis.policy_result else 'N/A'}",
            f"- Document Quality: {analysis.document_result.confidence:.2%}" if analysis.document_result else "",
            "",
            f"Final Decision: {analysis.overall_status.value.upper()}",
            f"Confidence: {analysis.final_decision.confidence:.2%}" if analysis.final_decision else "",
        ]
        
        if analysis.final_decision:
            brief_parts.extend([
                "",
                "Findings:",
                analysis.final_decision.findings,
                "",
                "Recommendations:",
                "\n".join(f"- {rec}" for rec in (analysis.final_decision.recommendations or []))
            ])
        
        return "\n".join(brief_parts)
    
    def _generate_claimant_message(self, claim_submission: ClaimSubmission, analysis: ClaimAnalysis) -> str:
        """Generate claimant communication template"""
        status = analysis.overall_status.value
        
        if status == "approved":
            message = f"""
Dear {claim_submission.claimant_name},

Your claim (ID: {analysis.claim_id}) has been reviewed and approved.

Claim Details:
- Policy Number: {claim_submission.policy_number}
- Claim Type: {claim_submission.claim_type.value}
- Claim Amount: ${claim_submission.claim_amount:,.2f}
- Incident Date: {claim_submission.incident_date}

Status: APPROVED

Next Steps:
- Payment processing will begin within 5-7 business days
- You will receive confirmation via email

Thank you for your patience.

Best regards,
Claims Processing Team
"""
        elif status == "rejected":
            message = f"""
Dear {claim_submission.claimant_name},

Your claim (ID: {analysis.claim_id}) has been reviewed.

Unfortunately, we are unable to approve this claim at this time.

Claim Details:
- Policy Number: {claim_submission.policy_number}
- Claim Type: {claim_submission.claim_type.value}
- Claim Amount: ${claim_submission.claim_amount:,.2f}

Status: REJECTED

Reason: {analysis.final_decision.findings if analysis.final_decision else 'Policy coverage issue'}

If you have questions or would like to appeal this decision, please contact us.

Best regards,
Claims Processing Team
"""
        else:
            message = f"""
Dear {claim_submission.claimant_name},

Your claim (ID: {analysis.claim_id}) is currently under review.

Claim Details:
- Policy Number: {claim_submission.policy_number}
- Claim Type: {claim_submission.claim_type.value}
- Claim Amount: ${claim_submission.claim_amount:,.2f}

Status: {status.upper()}

We will notify you once the review is complete.

Best regards,
Claims Processing Team
"""
        
        return message.strip()
    
    def get_workflow_state(self, claim_id: str) -> Optional[WorkflowState]:
        """Get workflow state for a claim"""
        return self.workflow_states.get(claim_id)
    
    def get_workflow_history(self, claim_id: str) -> List[Dict]:
        """Get workflow execution history"""
        state = self.get_workflow_state(claim_id)
        if state:
            return state.stage_history
        return []

