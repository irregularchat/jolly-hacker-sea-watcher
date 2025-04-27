# @@@SNIPSTART python-money-transfer-project-template-shared
from pydantic import BaseModel
from typing import Optional

class ReportDetails(BaseModel):
    source_account_id: str
    timestamp: str
    latitude: float
    longitude: float
    picture_url: str
    description: Optional[str] = None
    vessel_registry: Optional[str] = None

class EnrichedReportDetails(ReportDetails):
    report_number: Optional[str] = None
    trust_score: Optional[float] = None
    ais_neighbours: Optional[dict |list[dict] | list[str]] = None
    visibility: Optional[int] = 1
    enriched_description: Optional[str] = None