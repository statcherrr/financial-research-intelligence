"""Evaluation and benchmarking framework for FRIS Milestone 6.5.

Modules:
- config: Experimental configuration schema
- rubric: Evaluation rubric with quality and efficiency dimensions
- benchmark: Benchmark dataset (starting with NVDA case)
- metrics: Metric collection and aggregation across trials
"""

from .config import ExperimentConfig, ExperimentResult, BenchmarkCase
from .rubric import EvaluationRubric, QualityDimension
from .benchmark import BenchmarkCase as BC, BenchmarkDataset
from .metrics import TrialMetric, ExperimentMetrics

__all__ = [
    "ExperimentConfig", "ExperimentResult", "BenchmarkCase",
    "EvaluationRubric", "QualityDimension",
    "TrialMetric", "ExperimentMetrics",
    "NVDA_BENCHMARK",
]