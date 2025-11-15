from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any
from models.schemas import AgentResult
import re


class PolicyCheckerAgent:
    """Agent to verify policy coverage and eligibility"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.name = "Policy Checker"
        
    async def verify(self, claim_data: Dict[str, Any], policy_info: Dict[str, Any] = None) -> AgentResult:
        # Mock policy info for demo - in production, this would query a policy database
        if not policy_info:
            policy_info = {
                "status": "active",
                "coverage_type": claim_data.get('claim_type'),
                "max_coverage": 50000,
                "deductible": 1000,
                "effective_date": "2023-01-01",
                "expiry_date": "2025-12-31"
            }
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a policy verification expert. Analyze the claim against policy terms:
            1. Policy is active and valid
            2. Incident is covered under the policy type
            3. Claim amount is within coverage limits
            4. Incident date falls within policy period
            5. No exclusions apply
            
            Provide a confidence score (0-1) for policy compliance."""),
            ("human", f"""Verify policy coverage for this claim:
            
            Claim Details:
            - Policy Number: {claim_data.get('policy_number')}
            - Claim Type: {claim_data.get('claim_type')}
            - Claim Amount: ${claim_data.get('claim_amount')}
            - Incident Date: {claim_data.get('incident_date')}
            
            Policy Information:
            - Status: {policy_info.get('status')}
            - Coverage Type: {policy_info.get('coverage_type')}
            - Max Coverage: ${policy_info.get('max_coverage')}
            - Deductible: ${policy_info.get('deductible')}
            - Policy Period: {policy_info.get('effective_date')} to {policy_info.get('expiry_date')}
            
            Respond in this format:
            STATUS: [PASSED/FAILED/WARNING]
            CONFIDENCE: [0.0-1.0]
            FINDINGS: [Your detailed policy analysis]
            RECOMMENDATIONS: [Comma-separated list of recommendations]""")
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        result = self._parse_response(response.content)
        result.metadata = {"policy_info": policy_info}
        return result
    
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
            recommendations=[r.strip() for r in recommendations.group(1).split(',')] if recommendations else []
        )
