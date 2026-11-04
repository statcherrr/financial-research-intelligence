"""Evaluation rubric for FRIS Milestone 6.5 benchmark.

Defines structured scoring dimensions for both single-agent and multi-agent systems.
Quality scores are kept separate from efficiency measurements.
"""

from __future__ import annotations

from typing import Any, Optional, List, Dict

from pydantic import BaseModel, Field


class QualityDimension(BaseModel):
    """A single quality dimension for evaluation."""

    name: str = Field(..., description="Name of the quality dimension")
    description: str = Field(
        ..., description="Detailed description of what is being evaluated"
    )
    score: Optional[float] = Field(
        default=None, description="Score 0.0-1.0, or None if not evaluable"
    )
    score_anchor_high: str = Field(
        description="Description of what score=1.0 looks like"
    )
    score_anchor_low: str = Field(
        description="Description of what score=0.0 looks like"
    )
    evaluator_notes: str = Field(
        default="", description="Optional notes from the evaluator"
    )

    def is_complete(self) -> bool:
        """Check if this dimension has a scorable value."""
        return self.score is not None


class EvaluationRubric(BaseModel):
    """Complete evaluation rubric with all quality and efficiency dimensions."""

    experiment_id: str = Field(..., description="Experiment identifier")
    quality_dimensions: List[QualityDimension] = Field(
        default_factory=list, description="Quality evaluation dimensions"
    )
    efficiency_dimensions: List[QualityDimension] = Field(
        default_factory=list, description="Efficiency evaluation dimensions"
    )
    overall_quality: Optional[float] = Field(
        default=None, description="Optional overall quality aggregate (0.0-1.0)"
    )
    overall_efficiency: Optional[float] = Field(
        default=None, description="Optional overall efficiency aggregate (0.0-1.0)"
    )
    evaluation_notes: str = Field(
        default="", description="Optional overall evaluation notes"
    )

    def add_quality_score(self, dimension_name: str, score: float, notes: str = "") -> None:
        """Add a score to a quality dimension by name."""
        # Check if dimension already exists
        for dim in self.quality_dimensions:
            if dim.name == dimension_name:
                dim.score = score
                if notes:
                    dim.evaluator_notes = notes
                return
        # Add new dimension
        new_dim = QualityDimension(
            name=dimension_name,
            description=f"Evaluation of {dimension_name}",
            score=score,
            score_anchor_high="Defined by evaluator",
            score_anchor_low="Defined by evaluator",
            evaluator_notes=notes,
        )
        self.quality_dimensions.append(new_dim)

    def add_efficiency_score(self, dimension_name: str, score: float, notes: str = "") -> None:
        """Add a score to an efficiency dimension by name."""
        for dim in self.efficiency_dimensions:
            if dim.name == dimension_name:
                dim.score = score
                if notes:
                    dim.evaluator_notes = notes
                return
        new_dim = QualityDimension(
            name=dimension_name,
            description=f"Evaluation of {dimension_name}",
            score=score,
            score_anchor_high="Defined by evaluator",
            score_anchor_low="Defined by evaluator",
            evaluator_notes=notes,
        )
        self.efficiency_dimensions.append(new_dim)

    def get_quality_score(self, dimension_name: str) -> Optional[float]:
        """Get a quality dimension score by name."""
        for dim in self.quality_dimensions:
            if dim.name == dimension_name:
                return dim.score
        return None

    def get_efficiency_score(self, dimension_name: str) -> Optional[float]:
        """Get an efficiency dimension score by name."""
        for dim in self.efficiency_dimensions:
            if dim.name == dimension_name:
                return dim.score
        return None

    @property
    def has_quality_scores(self) -> bool:
        """Check if any quality scores have been recorded."""
        return any(dim.score is not None for dim in self.quality_dimensions)

    @property
    def has_efficiency_scores(self) -> bool:
        """Check if any efficiency scores have been recorded."""
        return any(dim.score is not None for dim in self.efficiency_dimensions)
