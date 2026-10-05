"""Core Engine Module for Clean Chassis.

Provides production-grade domain logic, input validation, and execution pipeline.
"""

from typing import Any, Dict, List


class CoreEngine:
    """Production execution engine implementing business logic and validation."""

    def __init__(self, name: str = "CleanChassisEngine") -> None:
        """Initializes the CoreEngine instance.

        Args:
            name (str): Engine instance identifier.
        """
        self.name = name
        self.version = "0.1.0"

    def execute_pipeline(self, data: List[float]) -> Dict[str, Any]:
        """Processes an array of numerical values through the core computation pipeline.

        Args:
            data (List[float]): Input numerical series.

        Returns:
            Dict[str, Any]: Summary metrics containing count, total, and average.

        Raises:
            ValueError: If input data is empty.
        """
        if not data:
            raise ValueError("Input data cannot be empty.")

        total = sum(data)
        count = len(data)
        mean = total / count

        return {
            "engine": self.name,
            "version": self.version,
            "count": count,
            "sum": total,
            "mean": mean,
        }
