"""Metric collection and aggregation for FRIS Milestone 6.5.

Handles recording and aggregation of quality and efficiency metrics
across experiment trials.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrialMetric(BaseModel):
    """Metrics from a single trial."""

    trial_number: int = Field(..., description="Trial number")
    quality: dict[str, float] = Field(
        default_factory=dict, description="Quality dimension scores: {dimension_name: score}"
    )
    efficiency: dict[str, float] = Field(
        default_factory=dict, description="Efficiency dimension scores: {dimension_name: score}"
    )
    token_usage: dict[str, int] | None = Field(
        default=None, description="Token usage: {prompt, completion, total}"
    )
    estimated_cost: float | None = Field(default=None, description="Estimated monetary cost")
    retrieval_status: str = Field(default="none", description="EDGAR retrieval status")
    verification_outcome: str = Field(
        default="unverifiable", description="Citation verification outcome"
    )
    execution_success: bool = Field(
        default=True, description="Whether the trial executed successfully"
    )
    failure_reason: str | None = Field(default=None, description="Reason if trial failed")


class ExperimentMetrics(BaseModel):
    """Aggregated metrics across all trials for an experiment."""

    experiment_id: str = Field(..., description="Experiment identifier")
    trial_count: int = Field(default=0, description="Number of trials run")
    completed_trials: int = Field(default=0, description="Number of successful trials")
    failed_trials: int = Field(default=0, description="Number of failed trials")
    per_trial_metrics: list[TrialMetric] = Field(
        default_factory=list, description="Per-trial metric records"
    )

    @property
    def quality_aggregates(self) -> dict[str, float]:
        """Compute average quality scores from per-trial metrics."""
        dim_scores: dict[str, list[float]] = {}
        for t in self.per_trial_metrics:
            for dim_name, score in t.quality.items():
                if dim_name not in dim_scores:
                    dim_scores[dim_name] = []
                dim_scores[dim_name].append(score)
        return {
            dim: sum(scores) / len(scores) if scores else 0.0 for dim, scores in dim_scores.items()
        }

    @property
    def efficiency_aggregates(self) -> dict[str, float]:
        """Compute average efficiency scores from per-trial metrics."""
        dim_scores: dict[str, list[float]] = {}
        for t in self.per_trial_metrics:
            for dim_name, score in t.efficiency.items():
                if dim_name not in dim_scores:
                    dim_scores[dim_name] = []
                dim_scores[dim_name].append(score)
        return {
            dim: sum(scores) / len(scores) if scores else 0.0 for dim, scores in dim_scores.items()
        }

    def add_trial(self, trial_metric: TrialMetric) -> None:
        """Add a trial's metrics to the aggregation."""
        self.per_trial_metrics.append(trial_metric)
        self.trial_count += 1
        if trial_metric.execution_success:
            self.completed_trials += 1
        else:
            self.failed_trials += 1

    def get_average_quality(self, dimension_name: str) -> float | None:
        """Get average quality score for a dimension."""
        scores = [
            t.quality.get(dimension_name)
            for t in self.per_trial_metrics
            if t.quality.get(dimension_name) is not None
        ]
        if not scores:
            return None
        return sum(scores) / len(scores)

    def get_average_efficiency(self, dimension_name: str) -> float | None:
        """Get average efficiency score for a dimension."""
        scores = [
            t.efficiency.get(dimension_name)
            for t in self.per_trial_metrics
            if t.efficiency.get(dimension_name) is not None
        ]
        if not scores:
            return None
        return sum(scores) / len(scores)
