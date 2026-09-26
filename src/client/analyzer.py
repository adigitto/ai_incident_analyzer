import os
import google.genai as genai
from google.genai import types
from client.schemas import StandardizedAlert, IncidentAnalysis
from integrations.fetch_logs import fetch_loki_logs
from rag.vector_store import query_vector_rag
from client.evaluator import compute_composite_confidence

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def analyze_incident(alert: StandardizedAlert) -> IncidentAnalysis:
    # 1. Fetch Logs from Loki
    logs = fetch_loki_logs(alert.service, alert.timestamp, alert.environment)
    
    # 2. Fetch Runbooks & Retrieval Score from Vector DB
    runbook_context, retrieval_score = query_vector_rag(alert.summary, alert.service)

    # 3. Pass 1: Generate Initial Incident Analysis with Gemini 2.5
    prompt = f"""
    ALERT DETAILS: {alert.alert_name} on service {alert.service}
    SUMMARY: {alert.summary}
    
    RECENT LOG TRACES:
    {logs}
    
    RUNBOOK CONTEXT:
    {runbook_context}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="You are an SRE incident agent. Diagnose root cause and recommend actions.",
            response_mime_type="application/json",
            response_schema=IncidentAnalysis,
            temperature=0.1
        )
    )
    
    # Parse initial response model
    analysis = IncidentAnalysis.model_validate_json(response.text)

    # 4. Pass 2: Calculate Deterministic Composite Confidence Score
    verified_confidence = compute_composite_confidence(
        reranker_score=retrieval_score,
        hypothesis=analysis.root_cause_hypothesis,
        logs=logs,
        runbook_context=runbook_context
    )

    # 5. Overwrite model confidence score with calculated score
    analysis.confidence_score = verified_confidence

    return analysis