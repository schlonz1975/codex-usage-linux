import json
import unittest
from unittest.mock import Mock, patch

from codex_usage.service import UsageService
from codex_usage.usage import parse_limits


class ServiceSerializationTests(unittest.TestCase):
    def test_snapshot_is_serialized_for_qml(self) -> None:
        snapshot = parse_limits(
            {
                "rateLimits": {
                    "planType": "plus",
                    "primary": {
                        "usedPercent": 23,
                        "windowDurationMins": 10_080,
                        "resetsAt": 2_000_000_000,
                    },
                }
            }
        )[0]
        service = object.__new__(UsageService)
        service.loading = True
        service.error = "old error"
        service.updated_at = 0
        service.data = ""
        service.markers = Mock()
        service.markers.should_notify.return_value = False
        service._emit_properties = Mock()

        with patch("codex_usage.service.time.time", return_value=1234):
            result = service._apply_snapshots([snapshot])

        payload = json.loads(service.data)
        self.assertEqual(payload["lowest"], 77)
        self.assertEqual(payload["windows"][0]["remaining"], 77)
        self.assertEqual(payload["windows"][0]["heading"], "Codex · Plus · Weekly limit")
        self.assertFalse(service.loading)
        self.assertEqual(service.updated_at, 1234)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
