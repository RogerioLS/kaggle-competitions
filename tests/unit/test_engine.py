"""Unit tests for src.core.engine module."""

import unittest

from src.core.engine import CoreEngine


class TestCoreEngine(unittest.TestCase):
    """Test suite for CoreEngine execution pipeline."""

    def setUp(self) -> None:
        """Sets up test instance of CoreEngine."""
        self.engine = CoreEngine("TestEngine")

    def test_engine_initialization(self) -> None:
        """Verifies engine attributes upon initialization."""
        self.assertEqual(self.engine.name, "TestEngine")
        self.assertEqual(self.engine.version, "0.1.0")

    def test_execute_pipeline_success(self) -> None:
        """Verifies statistical pipeline execution on valid input series."""
        sample_data = [10.0, 20.0, 30.0, 40.0]
        result = self.engine.execute_pipeline(sample_data)

        self.assertEqual(result["count"], 4)
        self.assertEqual(result["sum"], 100.0)
        self.assertEqual(result["mean"], 25.0)

    def test_execute_pipeline_empty_raises_error(self) -> None:
        """Verifies pipeline raises ValueError on empty input data."""
        with self.assertRaises(ValueError):
            self.engine.execute_pipeline([])


if __name__ == "__main__":
    unittest.main()
