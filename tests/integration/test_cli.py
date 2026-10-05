"""Integration tests verifying Clean Chassis execution pipeline."""

import unittest

from src.core.engine import CoreEngine


class TestIntegrationPipeline(unittest.TestCase):
    """Integration test suite for end-to-end pipeline execution."""

    def test_end_to_end_computation(self) -> None:
        """Verifies end-to-end calculation matches mathematical expectation."""
        engine = CoreEngine("IntegrationTest")
        dataset = [1.5, 2.5, 3.5, 4.5]
        result = engine.execute_pipeline(dataset)

        self.assertEqual(result["count"], 4)
        self.assertEqual(result["sum"], 12.0)
        self.assertEqual(result["mean"], 3.0)


if __name__ == "__main__":
    unittest.main()
