from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse, JSONResponse
from temporalio.client import Client
import uuid
import asyncio
import uvicorn
import logging
import os

from workflow import ReportDetailsWorkflow
from shared import ReportDetails, EnrichedReportDetails
from activities import _convert_to_prometheus_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Temporal Ship Processing API",
    description="API for processing ship reports using Temporal workflows",
    version="1.0.0"
)

class ReportDetailsRequest(BaseModel):
    source_account_id: str
    timestamp: str
    location: str
    picture_url: str

# connect Temporal client at startup
temporal_client = None
initial_metrics = []
final_metrics = []

@app.get("/")
async def root():
    return JSONResponse({
        "name": "Temporal Ship Processing API",
        "version": "1.0.0",
        "endpoints": {
            "/submit_ship": "POST endpoint for submitting ship reports",
            "/metrics": "GET endpoint for Prometheus metrics"
        }
    })

@app.on_event("startup")
async def startup_event():
    global temporal_client
    api_key = os.getenv('TEMPORAL_API_KEY')
    endpoint = os.getenv('TEMPORAL_ENDPOINT', '127.0.0.1:7234')
    namespace = os.getenv('TEMPORAL_NAMESPACE', 'default')
    
    logger.info(f"Connecting to Temporal server at {endpoint}...")
    if api_key:
        logger.info("Using cloud Temporal endpoint")
        temporal_client = await Client.connect(
            endpoint,
            tls=True,
            api_key=api_key,
            namespace=namespace
        )
    else:
        logger.info("Using local Temporal endpoint")
        temporal_client = await Client.connect(endpoint)
    logger.info("Connected to Temporal server")


@app.post("/submit_ship", response_model=EnrichedReportDetails)
async def submit_ship(ship: ReportDetails):
    logger.info(f"Received ship: {ship}")
    
    # Store initial metrics
    initial_metric = await _convert_to_prometheus_metrics(ship)
    initial_metrics.append(initial_metric)
    logger.info(f"Stored initial metric: {initial_metric}")
    
    # Start the workflow
    handle = await temporal_client.start_workflow(
        ReportDetailsWorkflow.run,
        ship,
        id=f"ship-{ship.source_account_id}",
        task_queue="ship-processing",
    )
    
    # Get the result
    result = await handle.result()
    logger.info(f"Workflow result: {result}")
    
    # Store final metrics
    final_metric = await _convert_to_prometheus_metrics(result)
    final_metrics.append(final_metric)
    logger.info(f"Stored final metric: {final_metric}")
    
    return result

@app.get("/metrics")
async def get_metrics():
    # Combine all metrics
    result = (
        '# HELP ship_trust_score Trust score for ships\n'
        '# TYPE ship_trust_score gauge\n'
        '# HELP ship_ais_number_total Total number of ships with AIS numbers\n'
        '# TYPE ship_ais_number_total counter\n'
    )
    result += '\n'.join(initial_metrics + final_metrics)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
