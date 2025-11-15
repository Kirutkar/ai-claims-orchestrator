from langchain.agents import AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any
from models.schemas import AgentResult
import re


class ClaimValidatorAgent:
    """Agent to validate claim completeness and data integrity"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.name = "Claim Validator"
        
    async def validate(self, claim_data: Dict[str, Any]) -> AgentResult:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a claims validation expert. Analyze the claim submission for:
            1. Completeness of required information
            2. Data format correctness
            3. Reasonable claim amount for the incident type
            4. Incident date validity
            
            Provide a confidence score (0-1) and specific findings."""),
            ("human", f"""Validate this claim:
            
            Policy Number: {claim_data.get('policy_number')}
            Claim Type: {claim_data.get('claim_type')}
            Claim Amount: ${claim_data.get('claim_amount')}
            Incident Date: {claim_data.get('incident_date')}
            Description: {claim_data.get('description')}
            Claimant: {claim_data.get('claimant_name')}
            Documents: {len(claim_data.get('documents', []))} files
            
            Respond in this format:
            STATUS: [PASSED/FAILED/WARNING]
            CONFIDENCE: [0.0-1.0]
            FINDINGS: [Your detailed analysis]
            RECOMMENDATIONS: [Comma-separated list of recommendations]""")
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
            recommendations=[r.strip() for r in recommendations.group(1).split(',')] if recommendations else []
        )
