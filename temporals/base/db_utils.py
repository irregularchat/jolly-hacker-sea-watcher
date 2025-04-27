# db_utils.py
"""
Utility functions for interacting with the database for trust scores and user metadata.
Replace the stubbed logic with your actual DB/ORM/API code.
"""
import logging
from typing import Optional
import random
import os

# Example: Replace with your ORM or DB client
# from your_orm import Session, TrustScore, UserMetadata

def get_trust_score(source_account_id: str) -> Optional[float]:
    """
    Retrieve the trust score for a given account ID from the database.
    Replace this stub with your DB query logic.
    """
    # Example stub: Replace with DB query
    # session = Session()
    # trust_score = session.query(TrustScore).filter_by(account_id=source_account_id).first()
    # return trust_score.value if trust_score else None
    logging.info(f"Stub: Fetch trust score for {source_account_id} from DB")
    return None

def store_user_metadata(ip: str, user_agent: str, source_account_id: Optional[str], is_logged_in: bool):
    """
    Store user metadata (IP, user agent, login status, etc.) in the database.
    Replace this stub with your DB insert logic.
    """
    # Example stub: Replace with DB insert
    # session = Session()
    # metadata = UserMetadata(ip=ip, user_agent=user_agent, account_id=source_account_id, is_logged_in=is_logged_in)
    # session.add(metadata)
    # session.commit()
    logging.info(f"Stub: Store user metadata: IP={ip}, UserAgent={user_agent}, AccountID={source_account_id}, LoggedIn={is_logged_in}")
    return

def get_or_create_report_number(latitude: float, longitude: float) -> str:
    """
    Retrieve or generate a report number for the given coordinates from the backend or AIS data.
    Replace this stub with your DB/API logic.
    """
    # Example stub: Replace with DB/API call
    # session = Session()
    # report = session.query(ReportNumber).filter_by(lat=latitude, lon=longitude).first()
    # if report: return report.number
    # else: ... generate, store, and return new number
    logging.info(f"Stub: Generate report number for ({latitude}, {longitude})")
    return f"AIS-{random.randint(10000, 99999)}"

def get_visibility_for_location(latitude: float, longitude: float) -> int:
    """
    Retrieve visibility for the given coordinates using OpenWeatherMap Current Weather API.
    Returns visibility in metres (0-10000). Requires OPENWEATHERMAP_API_KEY in environment.
    """
    import requests  # Only import here to avoid workflow sandbox issues
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHERMAP_API_KEY not set in environment.")
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        visibility = data.get("visibility")
        if visibility is None:
            raise ValueError(f"No visibility field in OpenWeatherMap response: {data}")
        # Clamp to documented max (10000)
        visibility = min(visibility, 10000)
        logging.info(f"Fetched visibility from OpenWeatherMap for ({latitude}, {longitude}): {visibility}m")
        return visibility
    except Exception as e:
        logging.error(f"Failed to fetch visibility from OpenWeatherMap: {e}")
        raise
