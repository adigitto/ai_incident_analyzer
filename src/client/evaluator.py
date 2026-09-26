"""
This module uses Gemini Flash as an LLM Judge to evaluate statement-level faithfulness (Groundedness) and compute the overall incident confidence score
"""

import os
import google.genai as genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

class ClaimVerification(BaseModel):
    claim: str
    is_supported_by_context: bool = Field(
        description="True if the claim is explicitly supported by the logs or runbooks."
    )

class GroundednessReport(BaseModel):
    verifications: List[ClaimVerification]

def calculate_groundedness_score(hypothesis: str, logs_context: str, rag_context: str) -> float:
    """Evaluates whether the hypothesis is grounded in the provided logs and runbooks."""
    eval_prompt = f"""
    CONTEXT DATA:
    --- LOGS ---
    {logs_context}
    --- RUNBOOKS ---
    {rag_context}

    HYPOTHESIS TO EVALUATE:
    "{hypothesis}"

    Task: Extract factual claims from the HYPOTHESIS and verify if each is supported by CONTEXT DATA.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=eval_prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are an SRE auditor verifying AI outputs against telemetry data.",
                response_mime_type="application/json",
                response_schema=GroundednessReport,
                temperature=0.0
            )
        )
        report = GroundednessReport.model_validate_json(response.text)
        if not report.verifications:
            return 0.5

        supported = sum(1 for v in report.verifications if v.is_supported_by_context)
        return supported / len(report.verifications)
    except Exception as e:
        print(f"[Warning] Groundedness verification failed: {e}")
        return 0.5  # Neutral fallback score on error

def compute_composite_confidence(
    reranker_score: float, 
    hypothesis: str, 
    logs: str, 
    runbook_context: str
) -> float:
    """Computes the weighted composite confidence score (0.0 to 1.0)."""
    groundedness = calculate_groundedness_score(hypothesis, logs, runbook_context)
    log_has_signal = 1.0 if any(k in logs.lower() for k in ["error", "exception", "fatal", "fail"]) else 0.2

    # Weighted composition
    w_retrieval = 0.30
    w_groundedness = 0.50
    w_logs = 0.20

    final_score = (w_retrieval * reranker_score) + (w_groundedness * groundedness) + (w_logs * log_has_signal)
    return round(final_score, 2)