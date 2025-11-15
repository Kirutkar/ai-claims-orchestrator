from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any, List
from models.schemas import AgentResult
import re


class FraudDetectorAgent:
    """Agent to detect potential fraud in insurance claims"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI, qdrant_client=None):
        self.llm = llm
        self.qdrant_client = qdrant_client
        self.name = "Fraud Detector"
        
    async def analyze(self, claim_data: Dict[str, Any], similar_claims: List[Dict] = None) -> AgentResult:
        similar_claims_text = ""
        if similar_claims:
            similar_claims_text = "\n".join([
                f"- Claim #{i+1}: {claim.get('description', 'N/A')[:100]}... Amount: ${claim.get('amount', 0)}"
                for i, claim in enumerate(similar_claims[:3])
            ])
        else:
            similar_claims_text = "No similar claims found in history."
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a fraud detection specialist for insurance claims. Analyze for:
            1. Suspicious patterns or inconsistencies
            2. Unusually high claim amounts
            3. Vague or generic descriptions
            4. Red flags in timing or circumstances
            5. Similarities with known fraudulent claims
            
            Provide a risk score (0-1, where 1 is highest fraud risk)."""),
            ("human", f"""Analyze this claim for fraud indicators:
            
            Policy Number: {claim_data.get('policy_number')}
            Claim Type: {claim_data.get('claim_type')}
            Claim Amount: ${claim_data.get('claim_amount')}
            Incident Date: {claim_data.get('incident_date')}
            Description: {claim_data.get('description')}
            
            Similar Historical Claims:
            {similar_claims_text}
            
            Respond in this format:
            STATUS: [PASSED/FAILED/WARNING]
            CONFIDENCE: [0.0-1.0] (fraud risk score)
            FINDINGS: [Your detailed fraud analysis]
            RECOMMENDATIONS: [Comma-separated list of actions to take]""")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        return self._parse_response(response.content)
    
    def _parse_response(self, response: str) -> AgentResult:
        status = re.search(r'STATUS:\s*(\w+)', response, re.IGNORECASE)
        confidence = re.search(r'CONFIDENCE:\s*([\d.]+)', response, re.IGNORECASE)
        findings = re.search(r'FINDINGS:\s*(.+?)(?=RECOMMENDATIONS:|$)', response, re.IGNORECASE | re.DOTALL)
        recommendations = re.search(r'RECOMMENDATIONS:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
        
        return AgentResult(
            agent_name=self.name,
            status=status.group(1).lower() if status else "warning",
            confidence=float(confidence.group(1)) if confidence else 0.5,
            findings=findings.group(1).strip() if findings else response,
            recommendations=[r.strip() for r in recommendations.group(1).split(',')] if recommendations else [],
            metadata={"fraud_risk": float(confidence.group(1)) if confidence else 0.5}
        )
