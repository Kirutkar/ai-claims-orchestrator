from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any, List
from models.schemas import AgentResult

from dotenv import load_dotenv
load_dotenv()

import re
import google.generativeai as genai
from PIL import Image
import io
import base64
import os
import requests
from pathlib import Path


class DocumentAnalyzerAgent:
    """Agent to analyze and validate claim documents with OCR capabilities"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI, gemini_api_key: str = None):
        self.llm = llm
        self.name = "Document Analyzer"
        
        # Initialize Gemini Vision for OCR
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            # using 2.5 Flash as you set
            self.vision_model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.vision_model = None
    
    async def analyze(self, claim_data: Dict[str, Any], documents: List[str] = None) -> AgentResult:
        documents = documents or claim_data.get('documents', [])
        
        # Extract text from documents using OCR
        extracted_texts = []
        doc_summary = []
        
        if documents:
            for i, doc_path in enumerate(documents):
                try:
                    # Perform OCR on document
                    ocr_result = await self._extract_text_with_ocr(doc_path)
                    extracted_texts.append(ocr_result)
                    doc_summary.append(
                        f"Document {i+1}: {Path(doc_path).name}\nExtracted Text: {ocr_result[:200]}..."
                    )
                except Exception as e:
                    doc_summary.append(
                        f"Document {i+1}: {Path(doc_path).name} (OCR failed: {str(e)})"
                    )
        else:
            doc_summary.append("No documents provided")
        
        # Combine all extracted texts
        all_extracted_text = "\n\n".join(extracted_texts) if extracted_texts else "No text extracted"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a document analysis expert for insurance claims. 
            You have been provided with text extracted from claim documents via OCR.
            
            Evaluate:
            1. Completeness of supporting documentation
            2. Document authenticity indicators
            3. Consistency between documents and claim description
            4. Required documents based on claim type
            5. Quality and clarity of extracted information
            6. Verify key details match claim (dates, amounts, names, locations)
            
            Provide a confidence score (0-1) for document validity."""),  # noqa: E501
            ("human", f"""Analyze documents for this claim:
            
            Claim Information:
            - Claim Type: {claim_data.get('claim_type')}
            - Claim Amount: ${claim_data.get('claim_amount')}
            - Incident Date: {claim_data.get('incident_date')}
            - Claimant: {claim_data.get('claimant_name')}
            - Description: {claim_data.get('description')}
            
            Submitted Documents:
            {chr(10).join(doc_summary)}
            
            OCR Extracted Text from All Documents:
            {all_extracted_text[:2000]}
            
            Required Documents for {claim_data.get('claim_type')} claims:
            - Police report (if applicable)
            - Medical records (health claims)
            - Photos of damage (auto/home claims)
            - Receipts and invoices
            - Witness statements (if applicable)
            
            Cross-verify:
            - Do dates in documents match incident date?
            - Do amounts match claim amount?
            - Is claimant name consistent?
            - Are there any red flags or inconsistencies?
            
            Respond in this format:
            STATUS: [PASSED/FAILED/WARNING]
            CONFIDENCE: [0.0-1.0]
            FINDINGS: [Your detailed document analysis including OCR verification]
            RECOMMENDATIONS: [Comma-separated list of missing or additional documents needed]""")  # noqa: E501
        ])
        
        response = await self.llm.ainvoke(prompt.format_messages())
        result = self._parse_response(response.content)
        result.metadata = {
            "document_count": len(documents),
            "ocr_performed": len(extracted_texts) > 0,
            "total_extracted_chars": len(all_extracted_text)
        }
        return result
    
    async def _extract_text_with_ocr(self, document_path: str) -> str:
        """
        Extract text from document using Gemini Vision OCR
        Supports: images (jpg, jpeg, png, webp, gif, bmp), PDFs, and URLs
        """
        try:
            # 1) URL case ------------------------------------------------------
            if document_path.startswith(('http://', 'https://')):
                return await self._ocr_from_url(document_path)
            
            # 2) Local file must exist ----------------------------------------
            if not os.path.exists(document_path):
                return f"[Document not found: {document_path}]"

            # 3) Ensure we actually have a vision model -----------------------
            if not self.vision_model:
                return (
                    f"[OCR not available - Gemini API key required. "
                    f"File: {Path(document_path).name}]"
                )

            ext = Path(document_path).suffix.lower()

            # Common OCR prompt for all types
            prompt = """Extract ALL text from this document.
Maintain the original structure and format.
Include dates, amounts, names, addresses, policy numbers,
and any other important information.
If this is a medical record, invoice, repair estimate,
police report, or other official document, extract all relevant fields."""  # noqa: E501

            # 4) PDF branch ----------------------------------------------------
            if ext == ".pdf":
                # Read PDF bytes and send as application/pdf
                with open(document_path, "rb") as f:
                    pdf_bytes = f.read()

                response = self.vision_model.generate_content(
                    [
                        prompt,
                        {
                            "mime_type": "application/pdf",
                            "data": pdf_bytes,
                        },
                    ]
                )
                extracted_text = response.text
                return (
                    extracted_text
                    if extracted_text
                    else "[No text detected in PDF document]"
                )

            # 5) Image branch (jpg, png, etc.) --------------------------------
            # For non-PDFs, treat as image
            image = Image.open(document_path)
            response = self.vision_model.generate_content([prompt, image])
            extracted_text = response.text
            return extracted_text if extracted_text else "[No text detected in image]"

        except Exception as e:
            return f"[OCR Error: {str(e)}]"
    
    async def _ocr_from_url(self, url: str) -> str:
        """Extract text from image URL using Gemini Vision"""
        try:
            # Download image from URL
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(response.content))
            
            # Use Gemini Vision for OCR
            if self.vision_model:
                prompt = """Extract ALL text from this document.
                Maintain the original structure and format.
                Include all important information."""
                
                vision_response = self.vision_model.generate_content([prompt, image])
                return vision_response.text if vision_response.text else "[No text detected]"
            else:
                return f"[OCR not available - URL: {url}]"
                
        except Exception as e:
            return f"[URL OCR Error: {str(e)}]"
    
    def _parse_response(self, response: str) -> AgentResult:
        status = re.search(r'STATUS:\s*(\w+)', response, re.IGNORECASE)
        confidence = re.search(r'CONFIDENCE:\s*([\d.]+)', response, re.IGNORECASE)
        findings = re.search(
            r'FINDINGS:\s*(.+?)(?=RECOMMENDATIONS:|$)',
            response,
            re.IGNORECASE | re.DOTALL
        )
        recommendations = re.search(
            r'RECOMMENDATIONS:\s*(.+)',
            response,
            re.IGNORECASE | re.DOTALL
        )
        
        return AgentResult(
            agent_name=self.name,
            status=status.group(1).lower() if status else "warning",
            confidence=float(confidence.group(1)) if confidence else 0.5,
            findings=findings.group(1).strip() if findings else response,
            recommendations=[
                r.strip()
                for r in recommendations.group(1).split(',')
            ] if recommendations else []
        )
