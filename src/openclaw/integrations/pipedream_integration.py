import os
from loguru import logger

PIPEDREAM_API_KEY = os.getenv('PIPEDREAM_API_KEY')

def trigger_pipedream(flow_url: str, payload: dict) -> bool:
    # POST to pipeline
    import requests
    try:
        r = requests.post(flow_url, json=payload, timeout=10)
        logger.info(f"Pipedream trigger {r.status_code}")
        return r.ok
    except Exception:
        logger.exception('Pipedream trigger failed')
        return False
