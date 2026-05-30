import os
from loguru import logger

CREVIO_WEBHOOK_URL = os.getenv('CREVIO_WEBHOOK_URL')
CREVIO_API_KEY = os.getenv('CREVIO_API_KEY')

def notify_crevio(event: dict) -> bool:
    # Generic webhook sender
    import requests
    headers = {'Authorization': f'Bearer {CREVIO_API_KEY}'} if CREVIO_API_KEY else {}
    try:
        r = requests.post(CREVIO_WEBHOOK_URL, json=event, headers=headers, timeout=10)
        logger.info(f"Crevio notify {r.status_code}")
        return r.ok
    except Exception:
        logger.exception('Crevio notify failed')
        return False
