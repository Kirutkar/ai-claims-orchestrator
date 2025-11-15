from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any
from models.schemas import AgentResult, ClaimStatus
import re


class DecisionMakerAgent:
    """Agent to make final claim decision based on all agent analyses"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.name = "Decision Maker"
        
    async def decide(
        self, 
        claim_data: Dict[str, Any],
        validator_result: AgentResult,
        fraud_result: AgentResult,
        policy_result: AgentResult,
        document_result: AgentResult
    ) -> tuple[AgentResult, ClaimStatus]:
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the final decision maker for insurance claims. Based on all agent analyses, make a final decision.
            
            Decision Guidelines:
            - APPROVE: All checks passed with high confidence
            - REJECT: Critical failures or high fraud risk
            - NEEDS_INFO: Missing documents or information
            
            Consider all factors holistically and provide clear reasoning."""),
            ("human", f"""Make final decision for this claim:
            
            Claim Information:
            - Policy: {claim_data.get('policy_number')}
            - Type: {claim_data.get('claim_type')}
            - Amount: ${claim_data.get('claim_amount')}
            
            Agent Analyses:
            
            1. Validation: {validator_result.status.upper()} (Confidence: {validator_result.confidence})
               {validator_result.findings}
            
            2. Fraud Detection: {fraud_result.status.upper()} (Risk Score: {fraud_result.confidence})
               {fraud_result.findings}
            
            3. Policy Check: {policy_result.status.upper()} (Confidence: {policy_result.confidence})
               {policy_result.findings}
            
            4. Document Analysis: {document_result.status.upper()} (Confidence: {document_result.confidence})
               {document_result.findings}
            
            Respond in this format:
            STATUS: [APPROVED/REJECTED/NEEDS_INFO]
            CONFIDENCE: [0.0-1.0]
            FINDINGS: [Your comprehensive final decision reasoning]
            RECOMMENDATIONS: [Comma-separated list of next steps or actions]""")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        result = self._parse_response(response.content)
        
        # Map decision to claim status
        status_map = {
            "approved": ClaimStatus.APPROVED,
            "rejected": ClaimStatus.REJECTED,
            "needs_info": ClaimStatus.NEEDS_INFO,
            "passed": ClaimStatus.APPROVED
        }
        
        claim_status = status_map.get(result.status, ClaimStatus.DECISION_PENDING)
        
        result.metadata = {
            "validation_score": validator_result.confidence,
            "fraud_risk": fraud_result.confidence,
            "policy_compliance": policy_result.confidence,
            "document_quality": document_result.confidence,
            "final_decision": result.status
        }
        
        return result, claim_status
    
    def _parse_response(self, response: str) -> AgentResult:
        status = re.search(r'STATUS:\s*(\w+)', response, re.IGNORECASE)
        confidence = re.search(r'CONFIDENCE:\s*([\d.]+)', response, re.IGNORECASE)
        findings = re.search(r'FINDINGS:\s*(.+?)(?=RECOMMENDATIONS:|$)', response, re.IGNORECASE | re.DOTALL)
        recommendations = re.search(r'RECOMMENDATIONS:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
        
        return AgentResult(
            agent_name=self.name,
            status=status.group(1).lower() if status else "needs_info",
            confidence=float(confidence.group(1)) if confidence else 0.5,
            findings=findings.group(1).strip() if findings else response,
            recommendations=[r.strip() for r in recommendations.group(1).split(',')] if recommendations else []
        )
