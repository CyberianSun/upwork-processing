from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class JobResponse(BaseModel):
    id: str
    title: str
    ts_publish: datetime
    description: str
    type: str
    url: str
    fixed_budget_amount: Optional[float] = None
    fixed_duration_weeks: Optional[float] = None
    hourly_min: Optional[float] = None
    hourly_max: Optional[float] = None
    source: str
    scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime