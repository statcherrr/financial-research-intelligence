"""Evaluation and benchmarking framework for FRIS Milestone 6.5.

Modules:
- config: Experimental configuration schema
- rubric: Evaluation rubric with quality and efficiency dimensions
- benchmark: Benchmark dataset (starting with NVDA case)
- metrics: Metric collection and aggregation across trials
"""

from .benchmark import BenchmarkCase as BC
from .benchmark import BenchmarkDataset
from .config import BenchmarkCase, ExperimentConfig, ExperimentResult
from .metrics import ExperimentMetrics, TrialMetric
from .rubric import EvaluationRubric, QualityDimension

__all__ = [
    "ExperimentConfig",
    "ExperimentResult",
    "BenchmarkCase",
    "EvaluationRubric",
    "QualityDimension",
    "TrialMetric",
    "ExperimentMetrics",
    "NVDA_BENCHMARK",
]
