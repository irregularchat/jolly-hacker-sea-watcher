from temporalio import activity
import random
import logging
import os
import json
from db_utils import get_trust_score, store_user_metadata, get_or_create_report_number, get_visibility_for_location
import uuid
from datetime import datetime

from shared import ReportDetails, EnrichedReportDetails

logging.info("activities.py loaded: registering activities...")

@activity.defn
async def calculate_trust_score(source_account_id: str, ip: str = None, user_agent: str = None, is_logged_in: bool = False) -> float:
    try:
        """
        Calculate or retrieve the trust score for a user from the DB/API. Store user metadata.
        Args:
            source_account_id: User/account identifier.
            ip: User IP address (optional, for logging/analytics).
            user_agent: User agent string (optional).
            is_logged_in: Whether the user is logged in.
        Returns:
            Trust score as a float.
        """
        logging.info(f"Calculating trust score for account: {source_account_id}")
        # Store user metadata if provided
        if ip or user_agent:
            store_user_metadata(ip=ip, user_agent=user_agent, source_account_id=source_account_id, is_logged_in=is_logged_in)
        # Try to get trust score from DB
        trust_score = get_trust_score(source_account_id)
        if trust_score is not None:
            logging.info(f"Fetched trust score from DB: {trust_score}")
            return trust_score
        # TODO: Insert your trust score calculation logic here if not found in DB
        # For now, default to a safe value (e.g., 0.7)
        trust_score = 0.7
        logging.info(f"Defaulted trust score to: {trust_score}")
        return trust_score
    except Exception as e:
        logging.error(f"Exception in calculate_trust_score: {e}")
        raise

@activity.defn
async def assign_report_number(report: ReportDetails) -> str:
    try:
        """
        Assign a report number using backend/AIS data instead of random placeholder.
        """
        logging.info(f"Assigning report number for ship at coordinates: {report.latitude}, {report.longitude}")
        # Use backend or AIS data to get or create a report number
        report_number = get_or_create_report_number(report.latitude, report.longitude)
        logging.info(f"Assigned report number: {report_number}")
        return report_number
    except Exception as e:
        logging.error(f"Exception in assign_report_number: {e}")
        raise

@activity.defn
async def calculate_visibility(report: EnrichedReportDetails) -> int:
    try:
        """
        Calculate visibility using real backend/API data instead of random placeholder.
        """
        logging.info(f"Calculating visibility at coordinates: {report.latitude}, {report.longitude}")
        visibility = get_visibility_for_location(report.latitude, report.longitude)
        logging.info(f"Calculated visibility: {visibility}")
        return visibility
    except Exception as e:
        logging.error(f"Exception in calculate_visibility: {e}")
        raise

# @activity.defn
# async def find_ais_neighbours(report: EnrichedReportDetails) -> list[str]:
#     try:
#         import requests
#         logging.info(f"Fetching AIS data for ships around coordinates: {report.latitude}, {report.longitude}")
#         url = f"http://0.0.0.0:8000/ships?lat={report.latitude}&lon={report.longitude}&radius={report.visibility}&tail_hours=0.1&sim_window_minutes=120"
#         logging.info(f"Making GET request to {url}")
#         try:
#             response = requests.request(
#                 method="GET",
#                 url=url,
#                 timeout=15 # Example timeout for the request itself
#             )
#             # Raise an exception for bad status codes (4xx or 5xx)
#             response.raise_for_status()
#
#             # Handle cases where response might not have JSON body if needed
#             ais_data = response.json()
#             neighbours = []
#             for ship in ais_data:
#                 logging.info(f"{ship}")
#                 neighbours.append(ship["vessel_name"])
#
#             logging.info(f"Found ships around location at this time: {neighbours}")
#             return neighbours
#
#         except requests.exceptions.RequestException as e:
#             activity.logger.error(f"HTTP request failed: {e}")
#             # Re-raise the exception so Temporal knows the activity failed
#             raise e
#     except Exception as e:
#         logging.error(f"Exception in find_ais_neighbours: {e}")
#         raise

@activity.defn
async def llm_enrich(report: EnrichedReportDetails) -> str:
    try:
        logging.info("llm_enrich activity registered and ready.")
        """
        Enriches the report description using LLM.
        This activity takes the existing description and enhances it with additional context
        about the vessel, location, and surrounding conditions.
        """
        logging.info(f"Starting LLM enrichment for ship at coordinates: {report.latitude}, {report.longitude}")
        
        # Import requests inside the activity to avoid sandbox restrictions
        import requests
        import json
        
        # Prepare system prompt and user message
        system_prompt = """You are an AI Maritime Security Analyst Assistant. Your purpose is to analyze incoming maritime intelligence data gathered by the "jolly-hacker-sea-watcher" platform.

        Context: The platform integrates crowdsourced reports from coastal communities and fishermen (who may have low technical proficiency) with PAI/CAI data (like AIS, satellite imagery, potentially radar/ELINT) to detect and respond to malign maritime activities. The primary focus is on countering greyzone tactics, particularly those associated with foreign state actors like China, targeting activities such as illegal fishing (IUU), AIS spoofing/manipulation, unauthorized transshipments, and misuse of maritime emergency laws by vessels often using flags of convenience to exploit regional vulnerabilities. Your analysis must be presented clearly, often in natural language, to support decision-making by users ranging from local stakeholders to maritime security forces.

        1. Data Reliability: Consider the source account's trust score when evaluating the report's reliability
        2. Location Context: Analyze the geographical position and any notable maritime features in the area
        3. Traffic Analysis: From the reported nearby vessels, identify:
           - Which vessels are likely to be currently visible given conditions
           - Any notable vessel types or patterns
           - Potential navigation concerns based on vessel density
        4. Visibility Assessment: How current visibility conditions affect:
           - Reliability of the vessel count
           - Navigation safety in the area
           - Recommended precautions
        5. Key Insights: Highlight the most relevant information for maritime authorities, considering:
           - The reliability of the source
           - Current visibility conditions
           - The operational significance of nearby vessels

        Keep the analysis concise, professional, and focused on what can be confidently determined from the available data."""
        

        user_message = f"""Please analyze and enrich this ship report:
        - Report Number: {report.report_number}
        - Location: {report.latitude}, {report.longitude} 
        - Visibility: {report.visibility}/10
        - Trust Score: {report.trust_score}
        - Nearby Vessels: { ", ".join(report.ais_neighbours) if report.ais_neighbours else "None detected"}
        
        Provide a detailed description incorporating all available information."""

        logging.info("Preparing OpenAI API call...")
        # Call LLM service with prepared prompt
        try:
            # Use direct API call instead of the OpenAI library to avoid sandbox restrictions
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                error_msg = "OPENAI_API_KEY environment variable not set"
                logging.error(error_msg)
                raise ValueError(error_msg)
                
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            logging.info("Making OpenAI API request...")
            logging.info(f"Request data: {json.dumps(data, indent=2)}")
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Log the response status and headers
            logging.info(f"OpenAI API response status: {response.status_code}")
            logging.info(f"OpenAI API response headers: {dict(response.headers)}")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            logging.info(f"OpenAI API response: {json.dumps(result, indent=2)}")
            
            if not result.get("choices") or not result["choices"][0].get("message", {}).get("content"):
                error_msg = "Invalid response format from OpenAI API"
                logging.error(error_msg)
                raise ValueError(error_msg)
                
            enriched_description = result["choices"][0]["message"]["content"]
            
            if not enriched_description:
                error_msg = "Empty response from LLM"
                logging.error(error_msg)
                raise ValueError(error_msg)
                
            logging.info(f"Generated enriched description: {enriched_description}")
            return enriched_description
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logging.error(error_msg)
            if hasattr(e.response, 'text'):
                logging.error(f"Response text: {e.response.text}")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error calling LLM service: {str(e)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
    except Exception as e:
        logging.error(f"Exception in llm_enrich: {e}")
        raise

@activity.defn
async def convert_to_prometheus_metrics(report_data) -> str:
    try:
        return await _convert_to_prometheus_metrics(report_data)
    except Exception as e:
        logging.error(f"Exception in convert_to_prometheus_metrics: {e}")
        raise

async def _convert_to_prometheus_metrics(report_data) -> str:
    logging.info(f"Converting to Prometheus metrics: {report_data}")
    
    # Handle both dict and object inputs
    if isinstance(report_data, dict):
        source_account_id = report_data['source_account_id']
        latitude = report_data['latitude']
        longitude = report_data['longitude']
        report_number = report_data.get('report_number')
        trust_score = report_data.get('trust_score')
        enriched_description = report_data.get('enriched_description')
        visibility = report_data.get('visibility')
        ais_neighbours = report_data.get('ais_neighbours')
        timestamp_str = report_data.get('timestamp')
        if timestamp_str:
            timestamp = int(datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).timestamp() * 1000)
        else:
            timestamp = int(datetime.now().timestamp() * 1000)
    else:
        source_account_id = report_data.source_account_id
        latitude = report_data.latitude
        longitude = report_data.longitude
        report_number = getattr(report_data, 'report_number', None)
        trust_score = getattr(report_data, 'trust_score', None)
        enriched_description = getattr(report_data, 'enriched_description', None)
        visibility = getattr(report_data, 'visibility', None)
        ais_neighbours = getattr(report_data, 'ais_neighbours', None)
        timestamp_str = getattr(report_data, 'timestamp', None)
        if timestamp_str:
            timestamp = int(datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).timestamp() * 1000)
        else:
            timestamp = int(datetime.now().timestamp() * 1000)
    
    # Determine if this is initial or final metrics
    is_final = report_number is not None and trust_score is not None
    stage = "final" if is_final else "initial"
    
    # Build metrics with stage label
    metrics = []
    
    # Add numeric coordinates metrics
    metrics.extend([
        f'ship_latitude{{source_account_id="{source_account_id}",'
        f'stage="{stage}",timestamp="{timestamp}"}} {latitude}',
        f'ship_longitude{{source_account_id="{source_account_id}",'
        f'stage="{stage}",timestamp="{timestamp}"}} {longitude}'
    ])
    
    # For initial metrics, we only have basic ship info
    if not is_final:
        metrics.append(
            f'ship_info{{source_account_id="{source_account_id}",'
            f'latitude="{latitude}",longitude="{longitude}",'
            f'stage="{stage}",timestamp="{timestamp}"}} 1'
        )
    else:
        # For final metrics, we have all enriched data
        metrics.extend([
            f'ship_trust_score{{source_account_id="{source_account_id}",'
            f'latitude="{latitude}",longitude="{longitude}",'
            f'report_number="{report_number}",stage="{stage}",enriched="true",'
            f'timestamp="{timestamp}"}} {trust_score}',
            f'ship_report_number_total{{source_account_id="{source_account_id}",'
            f'latitude="{latitude}",longitude="{longitude}",'
            f'stage="{stage}",enriched="true",timestamp="{timestamp}"}} 1'
        ])
        if enriched_description:
            metrics.append(
                f'ship_description_length{{source_account_id="{source_account_id}",'
                f'latitude="{latitude}",longitude="{longitude}",'
                f'stage="{stage}",enriched="true",timestamp="{timestamp}"}} {len(enriched_description)}'
            )
            # Add a new metric for the LLM enrichment result
            # We'll use a gauge type metric with a fixed value of 1 to indicate presence
            # and include the enriched description as a label
            escaped_description = enriched_description.replace('"', '\\"')
            metrics.append(
                f'ship_llm_enrichment{{source_account_id="{source_account_id}",'
                f'latitude="{latitude}",longitude="{longitude}",'
                f'report_number="{report_number}",stage="{stage}",enriched="true",'
                f'description="{escaped_description}",timestamp="{timestamp}"}} 1'
            )
    
    result = '\n'.join(metrics)
    logging.info(f"Generated Prometheus metrics: {result}")
    return result
