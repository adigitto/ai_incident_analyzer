'''
Reasoning Engine with Gemini 2.5
'''

from pydantic import BaseModel, Field
from typing import List

class MitigationAction(BaseModel):
    action_type: str = Field(description="e.g., KUBECTL_RESTART, SCALE_SERVICE, ROLLBACK_DEPLOYMENT, MANUAL_INVESTIGATION")
    command_or_instruction: str = Field(description="Exact CLI command or operational runbook step to execute")
    risk_level: str = Field(description="LOW, MEDIUM, HIGH")

class IncidentAnalysis(BaseModel):
    root_cause_hypothesis: str = Field(description="Clear explanation of the issue based on logs and runbooks")
    confidence_score: float = Field(description="Confidence from 0.0 to 1.0")
    key_log_evidence: List[str] = Field(description="Specific lines or patterns extracted from logs supporting diagnosis")
    recommended_actions: List[MitigationAction]