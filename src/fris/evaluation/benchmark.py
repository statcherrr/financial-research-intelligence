"""Benchmark dataset for FRIS Milestone 6.5.

Initial case: NVIDIA (NVDA).
Support future tickers and research questions.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BenchmarkCase(BaseModel):
    """A benchmark case defining the inputs and expected criteria."""

    model_config = {"arbitrary_types_allowed": True}

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
        default_factory=list, description="Subjective expert judgments"
    )

    def has_reference_facts(self) -> bool:
        """Check if this benchmark case has independently verified reference facts."""
        return len(self.reference_facts) > 0

    def has_subjective_judgments(self) -> bool:
        """Check if this benchmark case has subjective judgments."""
        return len(self.subjective_judgments) > 0


# Initial benchmark case: NVIDIA (NVDA)
NVDA_BENCHMARK = BenchmarkCase(
    ticker="NVDA",
    research_question="What are the key financial risks and opportunities for NVIDIA Corporation?",
    scope="full",
    approved_source_materials="SEC EDGAR filings (10-K, 10-Q), company press releases, financial databases",
    evaluation_criteria=[
        "factual_accuracy",
        "evidence_support",
        "citation_accuracy",
        "research_completeness",
        "risk_identification",
        "contradiction_detection",
        "uncertainty_calibration",
    ],
    reference_facts=[],  # Will be populated with independently verifiable facts
    subjective_judgments=[],  # Distinguished from reference facts
)


class BenchmarkDataset(BaseModel):
    """Collection of benchmark cases."""

    cases: dict[str, BenchmarkCase] = Field(
        default_factory=dict, description="Benchmark cases keyed by ticker"
    )
    version: str = Field(default="v1.0", description="Dataset version")
    created_timestamp: str = Field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat()
    )

    def add_case(self, case: BenchmarkCase) -> None:
        """Add a benchmark case, keyed by ticker."""
        self.cases[case.ticker] = case

    def get_case(self, ticker: str) -> BenchmarkCase | None:
        """Get a benchmark case by ticker."""
        return self.cases.get(ticker)

    def has_case(self, ticker: str) -> bool:
        """Check if a benchmark case exists for the given ticker."""
        return ticker in self.cases

    def list_tickers(self) -> list[str]:
        """List all tickers in the benchmark dataset."""
        return list(self.cases.keys())
