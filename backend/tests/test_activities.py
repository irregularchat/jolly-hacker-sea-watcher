import sys
import types
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import BaseModel

# Create a real in-memory shared module with minimal stubs
shared_mod = types.ModuleType('shared')
class ReportDetails(BaseModel):
    source_account_id: str = "stub"
    timestamp: str = "stub"
    latitude: float = 0.0
    longitude: float = 0.0
    picture_url: str = "stub"
    vessel_registry: str = None
class EnrichedReportDetails(ReportDetails):
    report_number: str = None
    trust_score: float = None
    ais_neighbours: list = None
    visibility: int = 1
setattr(shared_mod, 'ReportDetails', ReportDetails)
setattr(shared_mod, 'EnrichedReportDetails', EnrichedReportDetails)
sys.modules['shared'] = shared_mod

# Patch only the essential external dependencies
sys.modules['temporalio'] = types.ModuleType('temporalio')
temporalio_activity_mod = types.ModuleType('temporalio.activity')
def no_op_decorator(f):
    return f
temporalio_activity_mod.defn = no_op_decorator
sys.modules['temporalio.activity'] = temporalio_activity_mod

import importlib
activities = importlib.import_module('temporals.base.activities')

class TestActivities(unittest.IsolatedAsyncioTestCase):
    async def test_assign_report_number(self):
        with patch('random.randint', return_value=12345):
            report = ReportDetails(latitude=1, longitude=2)
            result = await activities.assign_report_number(report)
            self.assertEqual(result, "AIS-12345")

    async def test_calculate_trust_score(self):
        with patch('random.uniform', return_value=0.75):
            result = await activities.calculate_trust_score("acct")
            self.assertEqual(result, 0.75)

    async def test_calculate_visibility(self):
        with patch('random.randint', return_value=8):
            report = EnrichedReportDetails(latitude=0, longitude=0)
            result = await activities.calculate_visibility(report)
            self.assertEqual(result, 8)

    # async def test_find_ais_neighbours_success(self):
    #     # Patch requests.request to simulate API call
    #     fake_response = MagicMock()
    #     fake_response.raise_for_status = MagicMock()
    #     fake_response.json.return_value = [{"vessel_name": "ShipA"}, {"vessel_name": "ShipB"}]
    #     with patch('requests.request', return_value=fake_response):
    #         report = EnrichedReportDetails(latitude=0, longitude=0, visibility=10)
    #         result = await activities.find_ais_neighbours(report)
    #         self.assertEqual(result, ["ShipA", "ShipB"])

    # async def test_find_ais_neighbours_http_error(self):
    #     # Patch requests.request to raise an exception
    #     with patch('requests.request', side_effect=Exception("fail")):
    #         report = EnrichedReportDetails(latitude=0, longitude=0, visibility=10)
    #         with self.assertRaises(Exception):
    #             await activities.find_ais_neighbours(report)

    async def test_convert_to_prometheus_metrics(self):
        # Patch _convert_to_prometheus_metrics to return a known value
        with patch('temporals.base.activities._convert_to_prometheus_metrics', new=AsyncMock(return_value="foo_metric")):
            ship = ReportDetails()
            result = await activities.convert_to_prometheus_metrics(ship)
            self.assertEqual(result, "foo_metric")

if __name__ == "__main__":
    unittest.main()
