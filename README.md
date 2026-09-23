# ai_incident_analyzer
AI analyzer to analyze incidents that get alerted to SRE/Developers using Gemini LLM and RAG Patterns

**Architecture**

```mermaid
   
┌─────────────────────────┐
│ Datadog / Alertmanager  │
└────────────┬────────────┘
             │ Webhook Post
             ▼
┌─────────────────────────┐     Fetch Logs        ┌────────────────────────┐
│ FastAPI Webhook Ingestion├─────────────────────►│ Loki/Datadog
└────────────┬────────────┘     (Time-Window)     └───────────┬────────────┘
             │ Enqueue Job                                    │ Context Data
             ▼                                                ▼
┌─────────────────────────┐     Semantic Search  ┌────────────────────────┐
│ Worker Process (Celery) ├─────────────────────►│ Vector DB (pgvector)   │
└────────────┬────────────┘                      │ (Runbooks, Postmortems)│
             │                                   └───────────┬────────────┘
             │ Context + Logs                                │ Relevant Context
             ▼                                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Gemini 2.5 Flash Engine                        │
│         - Root Cause Analysis  - Remediation Commands  - Escalation     │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Slack/Teams Notification (Interactive Block Engine with RCA & Actions)   │
└─────────────────────────────────────────────────────────────────────────


**High Level Steps:**
We need to create the following Python classes/modules for our incident analyzer:
1. **Payload Standardization** - We need an ingestion service that normalizes webhook payloads from Datadog or Prometheus Alertmanager into a uniform schema (use pydantic, refer schema.py)
2. **Telemetry Retrieval & Vector RAG:** - The agent needs two pieces of context to perform precise root cause analysis:
   > Telemetry Logs: Real-time log streams retrieved around the alert time frame ($T_{-5m}$ to $T_{+2m}$)
   > Domain Knowledge RAG: Internal runbooks, past incident post-mortems, and deployment history retrieved via vector similarity search.[Use Gemini Embeddings and pgvector]
3. **AI Reasoning Engine with Gemini 2.5** -  Pass the normalized alert, real-time log stream, and RAG domain knowledge into Gemini using structured schema outputs to ensure reliable JSON parsing downstream.
4. **Webhook Service using FastAPI(main.py) ** -  We need a webhook service to receive Datadog Payloads and parse them to AI engine and parse its results and output to end users
