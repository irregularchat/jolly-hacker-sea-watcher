from temporalio.worker import Worker
import logging
from temporalio.client import Client
import os

from activities import assign_report_number, calculate_trust_score, calculate_visibility, find_ais_neighbours, convert_to_prometheus_metrics
from workflow import ReportDetailsWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_worker():
    # Get API key from environment variable
    api_key = os.getenv('TEMPORAL_API_KEY')
    endpoint = os.getenv('TEMPORAL_ENDPOINT', '127.0.0.1:7234')
    namespace = os.getenv('TEMPORAL_NAMESPACE', 'default')
    
    logger.info(f"Connecting to Temporal server at {endpoint}...")
    if api_key:
        logger.info("Using cloud Temporal endpoint")
        client = await Client.connect(
            endpoint,
            tls=True,
            api_key=api_key,
            namespace=namespace
        )
    else:
        logger.info("Using local Temporal endpoint")
        client = await Client.connect(endpoint)
    
    logger.info("Connected to Temporal server")

    logger.info("Starting worker...")
    worker = Worker(
        client,
        task_queue="ship-processing",
        workflows=[ReportDetailsWorkflow],
        activities=[assign_report_number, calculate_trust_score, calculate_visibility, find_ais_neighbours, convert_to_prometheus_metrics],
    )

    logger.info("Worker started, waiting for tasks...")
    await worker.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_worker())
