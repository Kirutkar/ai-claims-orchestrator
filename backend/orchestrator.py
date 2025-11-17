from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import google.generativeai as genai
from typing import Dict, Any, List
import asyncio
import time
import uuid

from config import get_settings
from models.schemas import ClaimSubmission, ClaimAnalysis, AgentResult, ClaimStatus
from datetime import datetime
from agents.validator import ClaimValidatorAgent
from agents.fraud_detector import FraudDetectorAgent
from agents.policy_checker import PolicyCheckerAgent
from agents.document_analyzer import DocumentAnalyzerAgent
from agents.decision_maker import DecisionMakerAgent
from agents.chat_agent import ChatAgent
from agents.guided_chat_agent import GuidedChatAgent


class ClaimsOrchestrator:
    """Main orchestrator for AI-powered claims processing using multi-agent system"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize Gemini LLM
        genai.configure(api_key=self.settings.gemini_api_key)
        self.llm = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.gemini_api_key,
            temperature=0.3,
            convert_system_message_to_human=True  # Required for Gemini compatibility
        )
        
        # Initialize Gemini Embeddings for RAG
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=self.settings.gemini_embedding_model,
            google_api_key=self.settings.gemini_api_key
        )
        
        # Initialize Qdrant client - Docker-aware (supports both local and cloud)
        try:
            self.qdrant_client = QdrantClient(
                # host=self.settings.qdrant_host,
                # port=self.settings.qdrant_port
                 url=self.settings.qdrant_host,
                 api_key=self.settings.qdrant_api_key,
            )
            print(f"✅ Connected to Qdrant at {self.settings.qdrant_host}:{self.settings.qdrant_port}")
        except Exception as e:
            print(f"⚠️  Could not connect to Qdrant: {e}")
            print(f"Using host: {self.settings.qdrant_host}:{self.settings.qdrant_port}")
            self.qdrant_client = None
            
        
        
        # Initialize all AI agents
        self.validator = ClaimValidatorAgent(self.llm)
        self.fraud_detector = FraudDetectorAgent(self.llm, self.qdrant_client)
        self.policy_checker = PolicyCheckerAgent(self.llm)
        self.document_analyzer = DocumentAnalyzerAgent(
            self.llm, 
            gemini_api_key=self.settings.gemini_api_key
        )
        self.decision_maker = DecisionMakerAgent(self.llm)
        self.chat_agent = ChatAgent(self.llm)
        self.guided_chat_agent = GuidedChatAgent(self.llm)
        
        # Ensure Qdrant collection exists
        self._initialize_qdrant_collection()
    
    def _initialize_qdrant_collection(self):
        """Initialize Qdrant collection for claims storage"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.settings.qdrant_collection not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.settings.qdrant_collection,
                    vectors_config=VectorParams(
                        size=self.settings.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created Qdrant collection: {self.settings.qdrant_collection}")
        except Exception as e:
            print(f"Qdrant collection initialization: {e}")
    
    async def process_claim(self, claim_submission: ClaimSubmission, claim_id: str, status_update_callback=None) -> ClaimAnalysis:
        """
        Orchestrate the complete claims processing workflow
        
        Workflow:
        1. Validate claim completeness
        2. Check for fraud indicators
        3. Verify policy coverage
        4. Analyze supporting documents
        5. Make final decision
        
        Args:
            claim_submission: The claim submission data
            claim_id: Unique claim identifier
            status_update_callback: Optional callback function(status: ClaimStatus) to update claim status in real-time
        """
        start_time = time.time()
        
        claim_data = claim_submission.model_dump()
        
        # Step 1: Validate Claim
        print(f"[{claim_id}] Step 1: Validating claim...")
        if status_update_callback:
            status_update_callback(ClaimStatus.VALIDATING)
        validation_result = await self.validator.validate(claim_data)
        
        # Step 2: Fraud Detection
        print(f"[{claim_id}] Step 2: Checking for fraud indicators...")
        if status_update_callback:
            status_update_callback(ClaimStatus.FRAUD_CHECK)
        similar_claims = await self._find_similar_claims(claim_data)
        fraud_result = await self.fraud_detector.analyze(claim_data, similar_claims)
        
        # Step 3: Policy Verification
        print(f"[{claim_id}] Step 3: Verifying policy coverage...")
        if status_update_callback:
            status_update_callback(ClaimStatus.POLICY_CHECK)
        policy_result = await self.policy_checker.verify(claim_data)
        
        # Step 4: Document Analysis
        print(f"[{claim_id}] Step 4: Analyzing documents...")
        if status_update_callback:
            status_update_callback(ClaimStatus.DOCUMENT_ANALYSIS)
        document_result = await self.document_analyzer.analyze(claim_data, claim_id=claim_id)
        
        # Step 5: Final Decision
        print(f"[{claim_id}] Step 5: Making final decision...")
        if status_update_callback:
            status_update_callback(ClaimStatus.DECISION_PENDING)
        final_decision, claim_status = await self.decision_maker.decide(
            claim_data,
            validation_result,
            fraud_result,
            policy_result,
            document_result
        )
        
        processing_time = time.time() - start_time
        
        # Store claim in Qdrant for future similarity searches
        await self._store_claim_in_qdrant(claim_id, claim_data, final_decision)
        
        return ClaimAnalysis(
            claim_id=claim_id,
            validation_result=validation_result,
            fraud_result=fraud_result,
            policy_result=policy_result,
            document_result=document_result,
            final_decision=final_decision,
            overall_status=claim_status,
            processing_time=processing_time
        )
    
    async def _find_similar_claims(self, claim_data: Dict[str, Any]) -> List[Dict]:
        """Find similar historical claims using vector search with embeddings"""
        try:
            # Create search query from claim data
            search_text = f"{claim_data.get('claim_type', '')} claim: {claim_data.get('description', '')} Amount: ${claim_data.get('claim_amount', 0)}"
            
            # Generate embedding for the search query
            query_embedding = self.embeddings.embed_query(search_text)
            
            # Search Qdrant for similar claims
            search_results = self.qdrant_client.search(
                collection_name=self.settings.qdrant_collection,
                query_vector=query_embedding,
                limit=5,
                with_payload=True
            )
            
            # Format results
            similar_claims = []
            for result in search_results:
                similar_claims.append({
                    "description": result.payload.get("description", "N/A"),
                    "amount": result.payload.get("amount", 0),
                    "status": result.payload.get("status", "unknown"),
                    "claim_type": result.payload.get("claim_type", "N/A"),
                    "similarity_score": result.score
                })
            
            return similar_claims if similar_claims else []
            
        except Exception as e:
            print(f"Error finding similar claims: {e}")
            # Fallback to mock data for demo
            return [
                {
                    "description": "Similar claim (fallback)",
                    "amount": claim_data.get("claim_amount", 0) * 0.9,
                    "status": "approved"
                }
            ]
    
    async def _store_claim_in_qdrant(self, claim_id: str, claim_data: Dict, decision: AgentResult):
        """Store processed claim in Qdrant for future reference with embeddings"""
        try:
            # Create embedding from claim data using Gemini embeddings
            claim_text = f"{claim_data.get('claim_type', '')} claim: {claim_data.get('description', '')} Amount: ${claim_data.get('claim_amount', 0)}"
            claim_embedding = self.embeddings.embed_query(claim_text)
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=claim_embedding,
                payload={
                    "claim_id": claim_id,
                    "claim_type": claim_data.get("claim_type"),
                    "amount": claim_data.get("claim_amount"),
                    "description": claim_data.get("description"),
                    "decision": decision.status,
                    "confidence": decision.confidence,
                    "claimant_name": claim_data.get("claimant_name"),
                    "incident_date": claim_data.get("incident_date")
                }
            )
            
            self.qdrant_client.upsert(
                collection_name=self.settings.qdrant_collection,
                points=[point]
            )
            print(f"[{claim_id}] Stored claim in Qdrant with embeddings")
        except Exception as e:
            print(f"Error storing claim in Qdrant: {e}")
