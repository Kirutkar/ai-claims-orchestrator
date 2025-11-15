"""
Utility functions for document handling and OCR
"""
import os
import base64
from pathlib import Path
from typing import List, Dict
import mimetypes


class DocumentProcessor:
    """Helper class for processing claim documents"""
    
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    SUPPORTED_DOCUMENT_FORMATS = ['.pdf']
    
    @staticmethod
    def is_supported_document(file_path: str) -> bool:
        """Check if document format is supported for OCR"""
        ext = Path(file_path).suffix.lower()
        return ext in (DocumentProcessor.SUPPORTED_IMAGE_FORMATS + 
                      DocumentProcessor.SUPPORTED_DOCUMENT_FORMATS)
    
    @staticmethod
    def get_document_type(file_path: str) -> str:
        """Determine document type from file path"""
        ext = Path(file_path).suffix.lower()
        
        if ext in DocumentProcessor.SUPPORTED_IMAGE_FORMATS:
            return 'image'
        elif ext in DocumentProcessor.SUPPORTED_DOCUMENT_FORMATS:
            return 'pdf'
        else:
            return 'unknown'
    
    @staticmethod
    def validate_documents(documents: List[str]) -> Dict[str, List[str]]:
        """
        Validate list of documents and categorize them
        
        Returns:
            Dict with 'valid', 'invalid', and 'missing' lists
        """
        result = {
            'valid': [],
            'invalid': [],
            'missing': []
        }
        
        for doc in documents:
            # Check if URL
            if doc.startswith(('http://', 'https://')):
                result['valid'].append(doc)
                continue
            
            # Check if local file exists
            if not os.path.exists(doc):
                result['missing'].append(doc)
                continue
            
            # Check if supported format
            if DocumentProcessor.is_supported_document(doc):
                result['valid'].append(doc)
            else:
                result['invalid'].append(doc)
        
        return result
    
    @staticmethod
    def encode_image_base64(image_path: str) -> str:
        """Encode image file to base64 string"""
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """Get MIME type of file"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
