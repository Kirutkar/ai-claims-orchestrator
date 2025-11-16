import google.generativeai as genai
from config import GEMINI_API_KEY, EMBEDDING_MODEL

genai.configure(api_key=GEMINI_API_KEY)

def embed_text(text: str):
    """Generate embedding vector using Gemini"""
    response = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text
    )
    return response["embedding"]
