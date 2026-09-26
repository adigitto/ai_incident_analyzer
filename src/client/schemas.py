from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class StandardizedAlert(BaseModel):
    alert_id: str
    alert_name: str
    source: str  # 'datadog' or 'prometheus'
    severity: str  # 'CRITICAL', 'WARNING', etc.
    service: str
    environment: str
    timestamp: datetime
    summary: str
    raw_payload: Dict[str, Any]    

class MitigationAction(BaseModel):
    action_type: str = Field(description="e.g., KUBECTL_RESTART, ROLLBACK_DEPLOYMENT")
    command_or_instruction: str = Field(description="Exact operational step")
    risk_level: str = Field(description="LOW, MEDIUM, HIGH")

class IncidentAnalysis(BaseModel):
    root_cause_hypothesis: str
    confidence_score: float
    key_log_evidence: list[str]
    recommended_actions: list[MitigationAction]

def parse_prometheus_payload(payload: Dict[str, any]) -> StandardizedAlert:
    # Prometheus Alertmanager sends an array of alerts
    alert = payload.get("alerts",[{}])[0]
    labels= alert.get("labels",{})
    annotations = alert.get("annotations",{})

    return StandardizedAlert(
        alert_id=alert.get("fingerprint", "prom-unknown"),
        alert_name=labels.get("alertname", "Unknown Prometheus Alert"),
        source="prometheus",
        severity=labels.get("severity", "critical").upper(),
        service=labels.get("service", "unknown-service"),
        environment=labels.get("env", "production"),
        timestamp=datetime.utcnow(),
        summary=annotations.get("summary", annotations.get("description", "")),
        raw_payload=payload
    )

# Optional: If you use Datadog
# def parse_datadog_payload(payload: Dict[str, Any]) -> StandardizedAlert:
#     return StandardizedAlert(
#         alert_id=str(payload.get("id", "dd-unknown")),
#         alert_name=payload.get("event_title", "DatadogAlert"),
#         source="datadog",
#         severity="CRITICAL" if payload.get("alert_transition") == "Triggered" else "WARNING",
#         service=payload.get("tags", {}).get("service", "payment-service"),
#         environment=payload.get("tags", {}).get("env", "production"),
#         timestamp=datetime.now(timezone.utc),
#         summary=payload.get("body", ""),
#         raw_payload=payload
#     )