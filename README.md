# ai_incident_analyzer
[WIP]
AI analyzer bot using Gemini LLM and RAG patterns that investigates production alerts, checks for past incidents, runbooks, documentation in RAG and responds with 

**Architecture**

<img width="583" height="515" alt="image" src="https://github.com/user-attachments/assets/d636b39b-5c57-40af-a27f-fdbe26a6427f" />


**High Level Steps:**
We need to create the following Python classes/modules for our incident analyzer:
1. **Payload Standardization** - We need an ingestion service that normalizes webhook payloads from Datadog or Prometheus Alertmanager into a uniform schema (use pydantic, refer schema.py)
2. **Telemetry Retrieval & Vector RAG:** - The agent needs two pieces of context to perform precise root cause analysis:
   > Telemetry Logs: Real-time log streams retrieved around the alert time frame ($T_{-5m}$ to $T_{+2m}$)
   > Domain Knowledge RAG: Internal runbooks, past incident post-mortems, and deployment history retrieved via vector similarity search.[Use Gemini Embeddings and pgvector]
3. **AI Reasoning Engine with Gemini 2.5** -  Pass the normalized alert, real-time log stream, and RAG domain knowledge into Gemini using structured schema outputs to ensure reliable JSON parsing downstream.
4. **Webhook Service using FastAPI(main.py) ** -  We need a webhook service to receive Datadog Payloads and parse them to AI engine and parse its results and output to end users


**Code Level Workflow**
1. main.py receives a webhook alert and triggers analyze_incident(alert).
2. analyzer.py queries Loki for logs and query_vector_rag() for runbooks plus the retrieval_score.
3. Gemini Flash generates an initial diagnosis (analysis).
4. analyzer.py passes retrieval_score, analysis.root_cause_hypothesis, logs, and runbook_context into compute_composite_confidence().
5. evaluator.py runs a lightweight Gemini groundedness check, combines it with log signal coverage and retrieval scores, and returns the calculated number (e.g., 0.88).
6. analyzer.py attaches this verified 0.88 score to the output payload, giving your automated routing rules a reliable metric to decide between auto-execution or human-in-the-loop escalation.
