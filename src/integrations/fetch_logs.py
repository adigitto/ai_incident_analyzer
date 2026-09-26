import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

class FetchLogs:
    def __init__(self):
        self.LOKI_URL = os.getenv("LOKI_URL", "http://loki.monitoring.svc.cluster.local:3100")
        self.LOKI_TENANT_ID = os.getenv("LOKI_ORG_ID", "default")
        self.LOKI_AUTH_USER = os.getenv("LOKI_USER", None)
        self.LOKI_AUTH_PASS = os.getenv("LOKI_PASSWORD", None)

    def fetch_loki_logs(self,
        service_name: str,
        alert_timestamp: datetime,
        window_minutes_before: int = 5,
        window_minutes_after: int = 2,
        environment: str = "production",
        limit: int = 200
    ) -> str:
        """
        Queries Grafana Loki via /loki/api/v1/query_range for logs around the alert time.
        """
        endpoint = f"{self.LOKI_URL.rstrip('/')}/loki/api/v1/query_range"
        
        start_dt = alert_timestamp - timedelta(minutes=window_minutes_before)
        end_dt = alert_timestamp + timedelta(minutes=window_minutes_after)
        
        start_ns = int(start_dt.timestamp() * 1e9)
        end_ns = int(end_dt.timestamp() * 1e9)
        
        # Fixed LogQL: Using regex pipe (|~) for OR logic
        logql_query = (
            f'{{app="{service_name}", env="{environment}"}} '
            f'|~ "error|exception|fatal|fail"'
        )
        
        params = {
            "query": logql_query,
            "start": str(start_ns),
            "end": str(end_ns),
            "limit": limit,
            "direction": "FORWARD"
        }
        
        headers = {}
        if self.LOKI_TENANT_ID:
            headers["X-Scope-OrgID"] = self.LOKI_TENANT_ID

        # Fixed auth tuple mapping password instead of repeating user
        auth = (self.LOKI_AUTH_USER, self.LOKI_AUTH_PASS) if self.LOKI_AUTH_USER else None

        try:
            response = requests.get(
                endpoint, 
                params=params, 
                headers=headers, 
                auth=auth, 
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return self.format_loki_response(data)
            
        except requests.exceptions.RequestException as e:
            print(f"[Error] Failed to fetch logs from Loki: {e}")
            return f"Warning: Log retrieval failed due to HTTP connection error: {str(e)}"

    def format_loki_response(self, loki_data: Dict[str, Any]) -> str:
        results = loki_data.get("data", {}).get("result", [])
        if not results:
            return "No error logs found in Loki within the specified time range."
        
        extracted_logs = []
        
        for stream in results:
            labels = stream.get("stream", {})
            stream_meta = f"Stream [{labels.get('pod', 'unknown-pod')} / {labels.get('container', 'unknown-container')}]:"
            extracted_logs.append(stream_meta)
            
            for entry in stream.get("values", []):
                raw_ts = int(entry[0]) / 1e9
                human_ts = datetime.fromtimestamp(raw_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                log_line = entry[1].strip()
                extracted_logs.append(f"  [{human_ts}] {log_line}")
                
        return "\n".join(extracted_logs)