"""Experimental configuration for FRIS Milestone 6.5 benchmark.

Defines the configuration for running experiments comparing
single-agent baseline against the multi-agent FRIS system.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExperimentConfig(BaseModel):
    """Configuration for a single experiment trial."""

    experiment_id: str = Field(..., description="Unique experiment identifier")
    research_question: str = Field(..., description="The research question being addressed")
    ticker: str = Field(..., description="Company ticker symbol")
    source_dataset_version: str = Field(default="v1", description="Version of the source dataset")
    model_name: str = Field(..., description="LLM model name used for the trial")
    model_version: str = Field(default="unknown", description="LLM model version")
    prompt_config_version: str = Field(
        default="unknown", description="Version of the prompt configuration"
    )
    system_under_evaluation: str = Field(..., description="'single_agent' or 'fris_multi_agent'")
    trial_number: int = Field(..., description="Trial number for repeated trials")
    start_timestamp: str | None = Field(default=None, description="ISO trial start timestamp")
    end_timestamp: str | None = Field(default=None, description="ISO trial end timestamp")
    token_usage: dict[str, int] | None = Field(
        default=None, description="Token usage: {prompt, completion, total}"
    )
    estimated_cost: float | None = Field(default=None, description="Estimated monetary cost")
    execution_status: str = Field(
        default="pending", description="Execution status: pending, running, completed, failed"
    )

    def model_dump(self, **kwargs):
        """Dump with explicit handling of None values."""
        return {
            k: v
            for k, v in self.model_dump(default_factory=dict, **kwargs).items()
            if v is not None
        }


class ExperimentResult(BaseModel):
    """Result of a single experiment trial."""

    experiment_id: str = Field(..., description="Experiment identifier")
    research_question: str = Field(..., description="Research question")
    ticker: str = Field(..., description="Ticker symbol")
    system_under_evaluation: str = Field(..., description="'single_agent' or 'fris_multi_agent'")
    trial_number: int = Field(..., description="Trial number")
    start_timestamp: str = Field(..., description="ISO trial start timestamp")
    end_timestamp: str | None = Field(default=None, description="ISO trial end timestamp")
    quality_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Per-quality-area scores"
    )
    efficiency_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Per-efficiency-area scores"
    )
    retrieval_status: str = Field(default="none", description="EDGAR retrieval status")
    verification_outcome: str = Field(
        default="unverifiable", description="Citation verification outcome"
    )
    execution_notes: str = Field(default="", description="Additional execution notes")

    def model_dump(self, **kwargs):
        """Dump with explicit handling of None values."""
        return {
            k: v
            for k, v in self.model_dump(default_factory=dict, **kwargs).items()
            if v is not None
        }


class BenchmarkCase(BaseModel):
    """A benchmark case defining the inputs and expected criteria."""

    ticker: str = Field(..., description="Company ticker symbol")
    research_question: str = Field(..., description="The research question asked")
    scope: str = Field(
        default="full", description="Research scope: full, fundamentals_only, industry_only"
    )
    approved_source_materials: str = Field(
        default="", description="Description of approved source materials"
    )
    evaluation_criteria: list[str] = Field(
        default_factory=list, description="List of evaluation criteria to assess"
    )
    reference_facts: list[str] = Field(
        default_factory=list, description="Independently verified reference facts"
    )
    subjective_judgments: list[str] = Field(
        default_factory=list,
        description="Subjective expert judgments (distinguished from reference facts)",
    )

    def has_reference_facts(self) -> bool:
        """Check if this benchmark case has independently verified reference facts."""
        return len(self.reference_facts) > 0

    def has_subjective_judgments(self) -> bool:
        """Check if this benchmark case has subjective judgments."""
        return len(self.subjective_judgments) > 0
