# @@@SNIPSTART python-money-transfer-project-template-shared
from pydantic import BaseModel
from typing import Optional

class ReportDetails(BaseModel):
    """
    Report details 
    """
    # Source account ID
    source_account_id: str
    # Timestamp of the report
    timestamp: str
    # Latitude of the report
    latitude: float
    # Longitude of the report
    longitude: float
    # URL of the picture
    picture_url: str
    # Vessel registry flag
    vessel_registry: Optional[str] = None
    # Description of the report
    description: Optional[str] = None
    # Activity type
    activity_type: Optional[str] = None
    # Vessel heading
    vessel_heading: Optional[str] = None

class EnrichedReportDetails(ReportDetails):
    """
    Enriched report details
    """
    # Report number
    report_number: Optional[str] = None
    # Trust score
    trust_score: Optional[float] = None
    # AIS neighbors
    ais_neighbours: Optional[list[str]] = None
    # Visibility
    visibility: Optional[int] = 1