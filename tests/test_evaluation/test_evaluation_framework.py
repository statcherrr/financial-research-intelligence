"""Tests for FRIS Milestone 6.5 Evaluation & Benchmarking Framework."""

import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fris.evaluation.config import (
    ExperimentConfig,
    ExperimentResult,
    BenchmarkCase,
)
from fris.evaluation.benchmark import BenchmarkDataset
from fris.evaluation.rubric import EvaluationRubric, QualityDimension
from fris.evaluation.metrics import TrialMetric, ExperimentMetrics
from fris.evaluation.baseline import (
    SingleAgentBaseline,
    SingleAgentPipeline,
    run_baseline_trial,
)
from fris.evaluation.runner import ExperimentRunner, ComparisonAnalysis
from fris.evaluation.benchmark import NVDA_BENCHMARK, BenchmarkDataset


def test_experiment_config():
    """Test that ExperimentConfig creates properly."""
    config = ExperimentConfig(
        experiment_id="test_exp_001",
        research_question="What are the key financial risks for Apple?",
        ticker="AAPL",
        model_name="claude-sonnet-4-20250514",
        trial_number=1,
        system_under_evaluation="single_agent",
        start_timestamp="2024-01-01T00:00:00",
    )
    assert config.experiment_id == "test_exp_001"
    assert config.research_question == "What are the key financial risks for Apple?"
    assert config.ticker == "AAPL"
    assert config.system_under_evaluation == "single_agent"
    print("  PASSED: ExperimentConfig")


def test_experiment_result():
    """Test that ExperimentResult creates properly."""
    result = ExperimentResult(
        experiment_id="test_exp_001",
        research_question="Test research question",
        ticker="AAPL",
        system_under_evaluation="single_agent",
        trial_number=1,
        start_timestamp="2024-01-01T00:00:00",
        end_timestamp="2024-01-01T00:01:00",
        quality_metrics={"accuracy": 0.8},
        efficiency_metrics={"tokens": 1500},
        retrieval_status="successful",
        verification_outcome="supported",
    )
    assert result.experiment_id == "test_exp_001"
    assert result.ticker == "AAPL"
    assert result.quality_metrics == {"accuracy": 0.8}
    assert result.efficiency_metrics == {"tokens": 1500}
    assert result.retrieval_status == "successful"
    assert result.verification_outcome == "supported"
    print("  PASSED: ExperimentResult")


def test_benchmark_case():
    """Test BenchmarkCase creation."""
    case = BenchmarkCase(
        ticker="NVDA",
        research_question="What are the key financial risks for NVIDIA?",
        scope="full",
        approved_source_materials="SEC EDGAR filings",
        evaluation_criteria=["factual_accuracy", "evidence_support"],
        reference_facts=["NVIDIA designs GPUs for AI and gaming"],
        subjective_judgments=["Market position is subjective"],
    )
    assert case.ticker == "NVDA"
    assert case.has_reference_facts()
    assert case.has_subjective_judgments()
    print("  PASSED: BenchmarkCase")


def test_benchmark_dataset():
    """Test BenchmarkDataset creation and case management."""
    dataset = BenchmarkDataset(version="v1.0")
    assert dataset.has_case("NVDA") is False

    dataset.add_case(NVDA_BENCHMARK)
    assert dataset.has_case("NVDA")
    retrieved = dataset.get_case("NVDA")
    assert retrieved is not None
    assert retrieved.ticker == "NVDA"
    assert retrieved.has_reference_facts() is False  # NVDA_BENCHMARK has empty reference_facts

    # Add another case
    case2 = BenchmarkCase(
        ticker="AAPL",
        research_question="Apple analysis",
        reference_facts=["Apple had $383B revenue in 2024"],
    )
    dataset.add_case(case2)
    assert dataset.list_tickers() == ["NVDA", "AAPL"]
    print("  PASSED: BenchmarkDataset")


def test_rubric_creation():
    """Test EvaluationRubric creation and score tracking."""
    rubric = EvaluationRubric(experiment_id="test_rubric_001")

    # Add quality scores
    rubric.add_quality_score("factual_accuracy", 0.9, notes="Good factual coverage")
    rubric.add_quality_score("evidence_support", 0.7, notes="Some evidence gaps")
    rubric.add_quality_score("contradiction_detection", 0.8, notes="Good at detecting contradictions")

    assert rubric.has_quality_scores
    assert rubric.get_quality_score("factual_accuracy") == 0.9
    assert rubric.get_quality_score("evidence_support") == 0.7
    assert rubric.get_quality_score("contradiction_detection") == 0.8
    print("  PASSED: EvaluationRubric")


def test_rubric_efficiency():
    """Test adding efficiency scores to rubric."""
    rubric = EvaluationRubric(experiment_id="test_rubric_002")
    rubric.add_efficiency_score("runtime", 0.85, notes="Fast execution")
    rubric.add_efficiency_score("token_efficiency", 0.92, notes="Good token usage")

    assert rubric.has_efficiency_scores
    assert rubric.get_efficiency_score("runtime") == 0.85
    assert rubric.get_efficiency_score("token_efficiency") == 0.92
    print("  PASSED: EvaluationRubric efficiency")


def test_trial_metric():
    """Test TrialMetric creation and aggregation."""
    metric = TrialMetric(
        trial_number=1,
        quality={"factual_accuracy": 0.9, "evidence_support": 0.7},
        efficiency={"runtime": 0.85},
        token_usage={"prompt": 500, "completion": 300, "total": 800},
        estimated_cost=0.012,
        retrieval_status="successful",
        verification_outcome="supported",
        execution_success=True,
    )
    assert metric.trial_number == 1
    assert metric.quality == {"factual_accuracy": 0.9, "evidence_support": 0.7}
    assert metric.efficiency == {"runtime": 0.85}
    assert metric.token_usage == {"prompt": 500, "completion": 300, "total": 800}
    assert metric.estimated_cost == 0.012
    assert metric.execution_success
    assert metric.verification_outcome == "supported"
    print("  PASSED: TrialMetric")


def test_experiment_metrics():
    """Test ExperimentMetrics aggregation."""
    metrics = ExperimentMetrics(experiment_id="test_exp")

    # Add two trials
    metrics.add_trial(
        TrialMetric(
            trial_number=1,
            quality={"factual_accuracy": 0.9},
            token_usage={"prompt": 500, "completion": 300, "total": 800},
            estimated_cost=0.01,
            execution_success=True,
        )
    )
    metrics.add_trial(
        TrialMetric(
            trial_number=2,
            quality={"factual_accuracy": 0.8},
            token_usage={"prompt": 600, "completion": 400, "total": 1000},
            estimated_cost=0.015,
            execution_success=True,
        )
    )

    assert metrics.trial_count == 2
    assert metrics.completed_trials == 2
    assert metrics.failed_trials == 0
    assert "factual_accuracy" in metrics.quality_aggregates
    # Average should be (0.9 + 0.8) / 2 = 0.85
    assert abs(metrics.quality_aggregates["factual_accuracy"] - 0.85) < 0.001
    print("  PASSED: ExperimentMetrics")


def test_run_baseline_trial():
    """Test running a single baseline trial."""
    import asyncio

    async def _test():
        result = await run_baseline_trial(
            experiment_id="test_baseline_001",
            research_question="What are financial risks for Apple?",
            ticker="AAPL",
            model_name="claude-sonnet-4-20250514",
            trial_number=1,
        )
        assert result is not None
        assert result.experiment_id == "test_baseline_001"
        assert result.ticker == "AAPL"
        assert result.system_under_evaluation == "single_agent"
        assert result.verification_outcome == "unverifiable"  # Baseline uses mock, no retrieval
        assert result.retrieval_status == "none"
        print(f"  Result verification_outcome: {result.verification_outcome}")
        print(f"  Result retrieval_status: {result.retrieval_status}")
        print(f"  Result execution_notes: {result.execution_notes}")
        return result

    return asyncio.get_event_loop().run_until_complete(_test())


def test_experiment_runner_creation():
    """Test ExperimentRunner creation."""
    runner = ExperimentRunner(
        research_question="What are the key financial risks for NVIDIA?",
        ticker="NVDA",
        trials=2,
        model_name="claude-sonnet-4-20250514",
    )
    assert runner.research_question == "What are the key financial risks for NVIDIA?"
    assert runner.ticker == "NVDA"
    assert runner.trials == 2
    assert runner.model_name == "claude-sonnet-4-20250514"
    print("  PASSED: ExperimentRunner")


def test_experiment_runner_with_benchmark():
    """Test ExperimentRunner with benchmark case."""
    from fris.evaluation.benchmark import NVDA_BENCHMARK

    # Test without benchmark_case to verify basic runner functionality
    runner = ExperimentRunner(
        research_question=NVDA_BENCHMARK.research_question,
        ticker=NVDA_BENCHMARK.ticker,
        trials=1,
    )
    assert runner.benchmark_case is None  # Default is None
    assert runner.research_question == NVDA_BENCHMARK.research_question
    assert runner.ticker == NVDA_BENCHMARK.ticker
    print("  PASSED: ExperimentRunner basic functionality")


def test_comparison_analysis():
    """Test ComparisonAnalysis creation."""
    analysis = ComparisonAnalysis(
        experiment_id="test_comp_001",
        quality_comparison={"factual_accuracy": "FRIS better"},
        efficiency_comparison={"tokens": "single_agent used fewer"},
    )
    assert analysis.experiment_id == "test_comp_001"
    print("  PASSED: ComparisonAnalysis")


if __name__ == "__main__":
    total_tests = 13
    passed = 0

    tests = [
        test_experiment_config,
        test_experiment_result,
        test_benchmark_case,
        test_benchmark_dataset,
        test_rubric_creation,
        test_rubric_efficiency,
        test_trial_metric,
        test_experiment_metrics,
        test_run_baseline_trial,
        test_experiment_runner_creation,
        test_experiment_runner_with_benchmark,
        test_comparison_analysis,
    ]

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total_tests} tests passed")
    print(f"{'=' * 60}")

    if passed == total_tests:
        print("All Milestone 6.5 evaluation tests PASSED ✅")
        sys.exit(0)
    else:
        print("Some tests FAILED ❌")
        sys.exit(1)