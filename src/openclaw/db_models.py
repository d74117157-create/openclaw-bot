from pydantic import BaseModel
from typing import Optional

class Deployment(BaseModel):
    name: str
    provider: str
    status: str = 'offline'
    base_url: str
    last_checked: Optional[float] = None
    priority: int = 100
    notion_page_id: Optional[str] = None
