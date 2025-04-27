from temporalio import workflow
from temporalio.common import RetryPolicy

import logging

from datetime import timedelta
from shared import ReportDetails, EnrichedReportDetails

from activities import (
    calculate_trust_score, 
    assign_report_number, 
    calculate_visibility, 
    # find_ais_neighbours,
    convert_to_prometheus_metrics,
    llm_enrich
)

RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
    maximum_attempts=5,
)

@workflow.defn
class ReportDetailsWorkflow:
    def __init__(self):
        self._metrics = []

    @workflow.run
    async def run(self, ship: ReportDetails) -> EnrichedReportDetails:
        logging.info(f"Running workflow with ship details: {ship}")
        
        # Store initial metrics
        initial_metric = await workflow.execute_activity(
            convert_to_prometheus_metrics,
            ship,
            start_to_close_timeout=timedelta(seconds=5),
        )
        self._metrics.append(initial_metric)
        logging.info(f"Stored initial metric: {initial_metric}")

        enriched = EnrichedReportDetails(**ship.__dict__)

        enriched.report_number = await workflow.execute_activity(
            assign_report_number,
            enriched,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RETRY_POLICY,
        )
        logging.info(f"Enriched with AIS number: {enriched.report_number}")

        enriched.visibility = await workflow.execute_activity(
            calculate_visibility,
            enriched,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RETRY_POLICY,
        )
        logging.info(f"Enriched with neighbours: {enriched.ais_neighbours}")

        enriched.ais_neighbours = await workflow.execute_activity(
            # find_ais_neighbours,
            enriched,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RETRY_POLICY,
        )
        logging.info(f"Enriched with neighbours: {enriched.ais_neighbours}")

        enriched.trust_score = await workflow.execute_activity(
            calculate_trust_score,
            enriched.source_account_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RETRY_POLICY,
        )
        logging.info(f"Trust score calculated: {enriched.trust_score}")

        logging.info("Starting LLM enrichment activity...")
        try:
            enriched.enriched_description = await workflow.execute_activity(
                llm_enrich,
                enriched,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RETRY_POLICY,
            )
            logging.info(f"Description enriched successfully: {enriched.enriched_description}")
        except Exception as e:
            logging.error(f"Failed to enrich description: {str(e)}")
            # Set a default description to indicate the enrichment failed
            enriched.enriched_description = "Description enrichment failed. Please check the logs for details."
            logging.info("Set default description due to enrichment failure")

        # Store final metrics
        final_metric = await workflow.execute_activity(
            convert_to_prometheus_metrics,
            enriched,
            start_to_close_timeout=timedelta(seconds=5),
        )
        self._metrics.append(final_metric)
        logging.info(f"Stored final metric: {final_metric}")

        return enriched

    @workflow.query
    def get_metrics(self) -> str:
        if not self._metrics:
            return ""
        # Add type and help information
        result = (
            '# HELP ship_trust_score Trust score for ships\n'
            '# TYPE ship_trust_score gauge\n'
            '# HELP ship_report_number_total Total number of ships with AIS numbers\n'
            '# TYPE ship_report_number_total counter\n'
        )
        # Add all metrics
        result += '\n'.join(self._metrics)
        return result