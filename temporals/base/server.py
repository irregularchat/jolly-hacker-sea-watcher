from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse
from temporalio.client import Client
import uuid
import asyncio
import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware

from workflow import ReportDetailsWorkflow
from shared import ReportDetails, EnrichedReportDetails
from activities import _convert_to_prometheus_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.on_event("startup")
async def startup_event():
    global temporal_client
    temporal_client = await Client.connect("127.0.0.1:7234")


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

@app.get("/", response_class=PlainTextResponse)
async def root():
    return "Ship Enrichment API is running."

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
