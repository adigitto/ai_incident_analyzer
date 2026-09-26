import os
import google.genai as genai
import psycopg2
from pgvector.psycopg2 import register_vector
from typing import Tuple

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"]) # Get this from secrets store or vault

def query_vector_rag(alert_summary: str, service: str) -> Tuple[str, float]:
    """Returns a tuple of (retrieved_context_text, top_similarity_score)."""
    try:
        emb = client.models.embed_content(
            model="text-embedding-004",
            contents=f"Service: {service}. Alert: {alert_summary}"
        ).embedding.values

        conn = psycopg2.connect(os.environ["POSTGRES_DSN"])
        register_vector(conn)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT content, 1 - (embedding <=> %s::vector) AS similarity
            FROM incident_knowledge
            ORDER BY similarity DESC LIMIT 2;
        """, (emb,))
        
        records = cursor.fetchall()
        if records:
            context = "\n---\n".join([r[0] for r in records])
            top_score = float(records[0][1])
            return context, top_score
        
        return "No matching runbooks found.", 0.0
    except Exception as e:
        print(f"[Error] Vector search failed: {e}")
        return f"RAG Query bypassed: {str(e)}", 0.0