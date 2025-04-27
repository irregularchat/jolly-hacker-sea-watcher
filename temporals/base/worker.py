from temporalio.worker import Worker
import logging
from temporalio.client import Client
import os
from dotenv import load_dotenv

from activities import (assign_report_number, calculate_trust_score, calculate_visibility, convert_to_prometheus_metrics, llm_enrich)
                        # find_ais_neighbours,
from workflow import ReportDetailsWorkflow

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get API key from environment variable
temporal_api_key = os.getenv('TEMPORAL_API_KEY')
endpoint = os.getenv('TEMPORAL_ENDPOINT', '127.0.0.1:7234')
namespace = os.getenv('TEMPORAL_NAMESPACE', 'default')
# Check if OpenAI API key is loaded
openai_api_key = os.environ.get("OPENAI_API_KEY")

if openai_api_key:
    logger.info("OpenAI API key is loaded")
else:
    logger.error("OpenAI API key is not loaded")

async def run_worker():
    logger.info("Connecting to Temporal server...")
    if temporal_api_key:
        logger.info("Using cloud Temporal endpoint")
        client = await Client.connect(
            endpoint,
            tls=True,
            api_key=temporal_api_key,
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
        activities=[assign_report_number, calculate_trust_score, calculate_visibility, convert_to_prometheus_metrics, llm_enrich],
        # find_ais_neighbours,
    )

    logger.info("Worker started, waiting for tasks...")
    logging.info(f"Registered activities: {[fn.__name__ for fn in [assign_report_number, calculate_trust_score, calculate_visibility, convert_to_prometheus_metrics, llm_enrich]]}")
    # find_ais_neighbours
    await worker.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_worker())
