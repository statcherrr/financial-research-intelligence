"""Experiment runner for FRIS Milestone 6.5 benchmark.

Runs experiments comparing the single-agent baseline against the
multi-agent FRIS system, recording metrics and results.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from fris.evaluation.baseline import run_baseline_trial
from fris.evaluation.config import BenchmarkCase, ExperimentConfig, ExperimentResult
from fris.evaluation.metrics import ExperimentMetrics, TrialMetric
from fris.evaluation.rubric import EvaluationRubric
from fris.orchestration.orchestrator import ResearchOrchestrator


class ExperimentRunner(BaseModel):
    """Runs experiments comparing single-agent vs multi-agent FRIS systems."""

    model_config = {"arbitrary_types_allowed": True, "use_enum_values": True}

    @field_validator("benchmark_case", mode="before")
    @classmethod
    def validate_benchmark_case(cls, v: Any) -> Any:
        """Validate and convert benchmark_case field."""
        if v is None:
            return None
        if isinstance(v, BenchmarkCase):
            return v
        if isinstance(v, dict):
            return BenchmarkCase(**v)
        return v

    experiment_id: str = Field(
        default_factory=lambda: f"exp_{uuid.uuid4().hex[:8]}",
        description="Unique experiment identifier",
    )
    research_question: str = Field(..., description="The research question being addressed")
    ticker: str = Field(..., description="Company ticker symbol")
    benchmark_case: BenchmarkCase | None = Field(
        default=None, description="Benchmark case defining evaluation criteria"
    )
    system_under_evaluation: str = Field(
        default="both", description="'single_agent', 'fris_multi_agent', or 'both'"
    )
    trials: int = Field(default=3, description="Number of repeated trials to run")
    allow_network: bool = Field(default=False, description="Allow network access for FRIS system")
    model_name: str = Field(default="claude-sonnet-4-20250514", description="LLM model name")

    # Results storage
    single_agent_results: list[ExperimentResult] = Field(
        default_factory=list, description="Single-agent trial results"
    )
    fris_results: list[ExperimentResult] = Field(
        default_factory=list, description="FRIS multi-agent trial results"
    )
    metrics: ExperimentMetrics | None = Field(default=None, description="Aggregated metrics")
    rubric: EvaluationRubric | None = Field(
        default=None, description="Evaluation rubric with scores"
    )

    def model_dump(self, **kwargs):
        """Dump with explicit handling of None values."""
        return {
            k: v
            for k, v in self.model_dump(default_factory=dict, **kwargs).items()
            if v is not None
        }

    async def run_single_agent_trials(self) -> list[ExperimentResult]:
        """Run the specified number of single-agent baseline trials."""
        results = []
        for trial_num in range(1, self.trials + 1):
            experiment_id = f"{self.experiment_id}_sa_{trial_num}"
            ExperimentConfig(
                experiment_id=experiment_id,
                research_question=self.research_question,
                ticker=self.ticker,
                model_name=self.model_name,
                trial_number=trial_num,
                system_under_evaluation="single_agent",
                start_timestamp=datetime.now(UTC).isoformat(),
            )

            result = await run_baseline_trial(
                experiment_id=experiment_id,
                research_question=self.research_question,
                ticker=self.ticker,
                model_name=self.model_name,
                trial_number=trial_num,
                allow_network=self.allow_network,
            )
            result.end_timestamp = datetime.now(UTC).isoformat()
            results.append(result)

        self.single_agent_results = results
        return results

    async def run_fris_trials(self) -> list[ExperimentResult]:
        """Run the specified number of FRIS multi-agent pipeline trials."""
        results = []
        orchestrator = ResearchOrchestrator(allow_network=self.allow_network)

        for trial_num in range(1, self.trials + 1):
            experiment_id = f"{self.experiment_id}_fris_{trial_num}"
            ExperimentConfig(
                experiment_id=experiment_id,
                research_question=self.research_question,
                ticker=self.ticker,
                model_name=self.model_name,
                trial_number=trial_num,
                system_under_evaluation="fris_multi_agent",
                start_timestamp=datetime.now(UTC).isoformat(),
            )

            result = await orchestrator.run_pipeline(
                ticker=self.ticker,
                research_question=self.research_question,
            )
            result.end_timestamp = datetime.now(UTC).isoformat()
            # Set experiment_id on the result if possible
            result.experiment_id = experiment_id
            results.append(result)

        self.fris_results = results
        return results

    async def run_experiment(self) -> dict[str, Any]:
        """Run the full experiment (both systems or just the specified system)."""
        results = {}

        if self.system_under_evaluation in ("single_agent", "both"):
            sa_results = await self.run_single_agent_trials()
            results["single_agent"] = sa_results

        if self.system_under_evaluation in ("fris_multi_agent", "both"):
            fris_results = await self.run_fris_trials()
            results["fris_multi_agent"] = fris_results

        # Aggregate metrics
        self.metrics = ExperimentMetrics(experiment_id=self.experiment_id)

        all_results = []
        system_name = "single_agent" if "single_agent" in results else "fris_multi_agent"
        for trial_result in results.get(system_name, []):
            self.metrics.add_trial(
                TrialMetric(
                    trial_number=trial_result.trial_number,
                    quality={},
                    efficiency={},
                    token_usage=trial_result.token_usage,
                    estimated_cost=trial_result.estimated_cost,
                    retrieval_status=trial_result.retrieval_status,
                    verification_outcome=trial_result.verification_outcome,
                    execution_success=True,
                )
            )
            all_results.append(trial_result)

        # Build summary
        summary = {
            "experiment_id": self.experiment_id,
            "research_question": self.research_question,
            "ticker": self.ticker,
            "system_under_evaluation": self.system_under_evaluation,
            "trials_planned": self.trials,
            "trials_completed": len(all_results),
            "single_agent_count": len(results.get("single_agent", [])),
            "fris_count": len(results.get("fris_multi_agent", [])),
            "results": all_results,
            "metrics": self.metrics.model_dump() if self.metrics else {},
            "timestamp": datetime.now(UTC).isoformat(),
        }

        return summary

    def set_rubric_scores(
        self,
        quality_scores: dict[str, float],
        efficiency_scores: dict[str, float] | None = None,
        notes: str = "",
    ) -> None:
        """Set evaluation rubric scores.

        Args:
            quality_scores: Mapping of quality dimension names to scores (0.0-1.0)
            efficiency_scores: Optional mapping of efficiency dimension names to scores
            notes: Optional overall evaluation notes
        """
        self.rubric = EvaluationRubric(experiment_id=self.experiment_id)

        for dim_name, score in quality_scores.items():
            self.rubric.add_quality_score(dim_name, score, notes=notes)

        if efficiency_scores:
            for dim_name, score in efficiency_scores.items():
                self.rubric.add_efficiency_score(dim_name, score, notes=notes)

    def get_rubric(self) -> EvaluationRubric | None:
        """Get the evaluation rubric with recorded scores."""
        return self.rubric

    def get_summary_statistics(self) -> dict[str, Any]:
        """Get summary statistics across all completed trials."""
        if not self.single_agent_results and not self.fris_results:
            return {"error": "No trial results available"}

        sa_count = len(self.single_agent_results)
        fris_count = len(self.fris_results)

        summary = {
            "experiment_id": self.experiment_id,
            "ticker": self.ticker,
            "research_question": self.research_question,
            "trials_planned": self.trials,
            "single_agent_trials": sa_count,
            "fris_trials": fris_count,
        }

        # Token usage comparison
        sa_tokens = sum((r.token_usage or {}).get("total", 0) for r in self.single_agent_results)
        fris_tokens = sum((r.token_usage or {}).get("total", 0) for r in self.fris_results)

        summary["token_usage"] = {
            "single_agent_total": sa_tokens,
            "fris_total": fris_tokens,
            "single_agent_average": sa_tokens / sa_count if sa_count > 0 else 0,
            "fris_average": fris_tokens / fris_count if fris_count > 0 else 0,
        }

        # Runtime comparison
        sa_runtimes = sum(
            (r.end_timestamp and self._parse_timestamp(r.end_timestamp) or 0)
            - (r.start_timestamp and self._parse_timestamp(r.start_timestamp) or 0)
            for r in self.single_agent_results
        )
        fris_runtimes = sum(
            (r.end_timestamp and self._parse_timestamp(r.end_timestamp) or 0)
            - (r.start_timestamp and self._parse_timestamp(r.start_timestamp) or 0)
            for r in self.fris_results
        )

        summary["runtime"] = {
            "single_agent_total_seconds": sa_runtimes,
            "fris_total_seconds": fris_runtimes,
            "single_agent_average_seconds": sa_runtimes / sa_count if sa_count > 0 else 0,
            "fris_average_seconds": fris_runtimes / fris_count if fris_count > 0 else 0,
        }

        # Verification outcomes
        sa_outcomes = {}
        fris_outcomes = {}

        for r in self.single_agent_results:
            outcome = r.verification_outcome
            sa_outcomes[outcome] = sa_outcomes.get(outcome, 0) + 1

        for r in self.fris_results:
            outcome = r.verification_outcome
            fris_outcomes[outcome] = fris_outcomes.get(outcome, 0) + 1

        summary["verification_outcomes"] = {
            "single_agent": sa_outcomes,
            "fris_multi_agent": fris_outcomes,
        }

        return summary

    @staticmethod
    def _parse_timestamp(ts: str) -> float:
        """Parse an ISO timestamp string to a float (seconds since epoch)."""
        try:
            return datetime.fromisoformat(ts).timestamp()
        except (ValueError, AttributeError):
            return 0.0


class ComparisonAnalysis(BaseModel):
    """Analysis comparing single-agent vs FRIS multi-agent results."""

    experiment_id: str = Field(..., description="Experiment identifier")

    quality_comparison: dict[str, Any] = Field(
        default_factory=dict, description="Quality dimension comparison"
    )
    efficiency_comparison: dict[str, Any] = Field(
        default_factory=dict, description="Efficiency dimension comparison"
    )
    verification_comparison: dict[str, Any] = Field(
        default_factory=dict, description="Verification outcome comparison"
    )
    statistical_assessment: dict[str, Any] = Field(
        default_factory=dict, description="Statistical assessment of differences"
    )

    def model_dump(self, **kwargs):
        """Dump with explicit handling of None values."""
        return {
            k: v
            for k, v in self.model_dump(default_factory=dict, **kwargs).items()
            if v is not None
        }
