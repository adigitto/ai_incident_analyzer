import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from app.schemas import parse_prometheus_payload, parse_datadog_payload
from app.analyzer import analyze_incident


app = FastAPI(title="SRE Incident Response AI Agent")

def process_incident_workflow(alert):
    # Executes the full loop: Loki Logs -> pgvector RAG -> Gemini 2.5 Reasoning
    analysis = analyze_incident(alert)
    
    # Output result (e.g., send to Slack webhook or logging system)
    print(f"=== INCIDENT ANALYSIS COMPLETE [{alert.alert_id}] ===")
    print(f"Root Cause: {analysis.root_cause_hypothesis}")
    print(f"Confidence: {analysis.confidence_score}")

@app.post("/webhooks/prometheus")
async def prometheus_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    alert = parse_prometheus_payload(payload)
    
    # Offload execution to asynchronous background task
    background_tasks.add_task(process_incident_workflow, alert)
    return {"status": "accepted", "alert_id": alert.alert_id}

# @app.post("/webhooks/datadog")
# async def datadog_webhook(request: Request, background_tasks: BackgroundTasks):
#     payload = await request.json()
#     alert = parse_datadog_payload(payload)
    
#     background_tasks.add_task(process_incident_workflow, alert)
#     return {"status": "accepted", "alert_id": alert.alert_id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)