"""Single-agent financial research baseline for FRIS Milestone 6.5.

A baseline research system that performs the same research task without
multi-agent decomposition. Uses the same provider-agnostic LLM protocol
as FRIS but operates with a single unified agent rather than specialist
analysts, synthesizer, and orchestrator.

The baseline must not secretly invoke the FRIS specialist agents, synthesizer
or orchestrator. Architecturally independent enough to make the comparison meaningful.
"""

from __future__ import annotations

import time
import json
from typing import Any, Optional, List, Dict

from pydantic import BaseModel, Field, PrivateAttr

from fris.llms.protocol import ChatMessage, ChatCompletionRequest, ChatCompletionResponse, InferenceClient
from fris.evaluation.config import ExperimentConfig, ExperimentResult
from fris.evaluation.metrics import TrialMetric


class SingleAgentBaseline(BaseModel):
    """Single-agent baseline research system.

    Performs financial research without specialist decomposition.
    Uses the provider-agnostic LLM protocol throughout.
    """

    model_config = {"arbitrary_types_allowed": True}

    client: InferenceClient = Field(
        default_factory=lambda: None, description="LLM inference client"
    )
    model: str = Field(default="claude-sonnet-4-20250514", description="LLM model name")
    temperature: float = Field(0.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")

    # Internal state tracking (Pydantic v2)
    _call_count: int = 0
    _total_tokens: Optional[int] = None

    async def achat(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Send a chat completion request through the client."""
        if self.client is None:
            raise ValueError("LLM client not configured")
        self._call_count += 1
        start = time.time()
        response = await self.client.achat(request)
        elapsed = time.time() - start
        # Track token usage from response
        if hasattr(response, "usage") and response.usage:
            # Use PrivateAttr properly via model
            current_total = self.model_dump().get("_total_tokens", 0) or 0
            usage_tokens = getattr(response.usage, "total_tokens", 0) or 0
            self._total_tokens = current_total + usage_tokens
        return response

    async def research(self, config: ExperimentConfig) -> ExperimentResult:
        """Run a single research trial using the baseline agent.

        Args:
            config: The experiment configuration defining the research question,
            ticker, model, etc.

        Returns:
            An ExperimentResult with the research output and metrics.
        """
        start_time = time.time()
        experiment_id = config.experiment_id
        trial_number = config.trial_number

        # Build the research prompt
        prompt_text = self._build_research_prompt(config)

        # Create the chat completion request
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(
                    role="system",
                    content=self._get_system_prompt(),
                ),
                ChatMessage(role="user", content=prompt_text),
            ],
            model=config.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            extra={"ticker": config.ticker, "experiment_id": experiment_id},
        )

        # Execute the research
        response = await self.achat(request)
        end_time_float = time.time()

        # Extract the response content
        content = ""
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            if isinstance(choice, dict) and "message" in choice:
                content = choice["message"].get("content", "")
            elif hasattr(choice, "content"):
                content = choice.content

        # Parse the structured research output
        research_output = self._parse_research_output(content, config)

        # Build experiment timestamps - handle start_timestamp from config or generate from start_time
        if config.start_timestamp:
            start_timestamp = config.start_timestamp
        else:
            # Convert start_time float to ISO format string
            from datetime import datetime
            start_timestamp = datetime.fromtimestamp(end_time_float).isoformat()
        # Convert end time float to ISO format string
        end_timestamp = datetime.fromtimestamp(end_time_float).isoformat()

        # Build the experiment result
        result = ExperimentResult(
            experiment_id=experiment_id,
            research_question=config.research_question,
            ticker=config.ticker,
            system_under_evaluation="single_agent",
            trial_number=trial_number,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            quality_metrics={},
            efficiency_metrics={},
            retrieval_status="none",  # Single agent doesn't do EDGAR retrieval
            verification_outcome="unverifiable",
            execution_notes=self._build_execution_notes(config, content, end_time_float - start_time),
        )

        # Populate token and cost data if available
        if hasattr(response, "usage") and response.usage:
            usage_data = response.usage
            result.token_usage = {
                "prompt": getattr(usage_data, "prompt_tokens", 0) or 0,
                "completion": getattr(usage_data, "completion_tokens", 0) or 0,
                "total": getattr(usage_data, "total_tokens", 0) or 0,
            }
            # Estimate cost if token counts available
            if usage_data.get("prompt_tokens") is not None and usage_data.get("completion_tokens") is not None:
                estimated = (usage_data["prompt_tokens"] * 0.003 / 1000) + (
                    usage_data["completion_tokens"] * 0.015 / 1000
                )
                result.estimated_cost = round(estimated, 4)

        return result

    def _build_research_prompt(self, config: ExperimentConfig) -> str:
        """Build the research prompt for the single agent."""
        lines = [
            "Research Question: " + config.research_question,
            "Ticker: " + config.ticker,
            "Scope: full research",
            "",
            "Please provide a comprehensive financial research analysis including:",
            "1. Key financial risks",
            "2. Key financial opportunities",
            "3. Supporting evidence with source references",
            "4. Identified contradictions or competing interpretations",
            "5. Uncertainties and limitations",
            "6. Citation of sources (CIK, accession number, filing type, filing date, section)",
            "",
            "Format the response as a structured JSON with the following fields:",
            "- summary: overall summary paragraph",
            "- risks: list of key risk statements",
            "- opportunities: list of key opportunity statements",
            "- evidence: list of evidence references with source details",
            "- contradictions: list of identified contradictions",
            "- uncertainties: list of uncertainty statements",
            "- citation_verification: whether evidence supports claims (supported/partial/contradicted/unverifiable)",
        ]
        return "\n".join(lines)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the baseline agent."""
        return """You are a financial research analyst performing a comprehensive analysis.

Your task is to analyze available information about a public company and produce
a structured research report. Be factual, cite sources when possible, and clearly
distinguish between established facts, interpretations, and uncertainties.

Do not fabricate financial figures, citations, or conclusions. Clearly state
limitations and uncertainties. If evidence is insufficient, mark claims as unverifiable."""

    def _parse_research_output(self, content: str, config: ExperimentConfig) -> Dict[str, Any]:
        """Parse the LLM research output into structured data."""
        try:
            # Try to parse as JSON
            parsed = json.loads(content)
            # Validate required fields exist
            required = ["summary", "risks", "opportunities", "evidence", "contradictions", "uncertainties", "citation_verification"]
            for field in required:
                if field not in parsed:
                    raise ValueError(f"Missing field: {field}")
            return parsed
        except (json.JSONDecodeError, ValueError) as e:
            # Return raw content if parsing fails
            import traceback
            traceback.print_exc()
            return {
                "summary": content[:200] if content else "",
                "risks": [],
                "opportunities": [],
                "evidence": [],
                "contradictions": [],
                "uncertainties": [],
                "citation_verification": "unverifiable",
                "parse_error": str(e),
                "raw_output": content[:500] if content else "",
            }

    def _build_execution_notes(self, config: ExperimentConfig, output: str, runtime: float) -> str:
        """Build execution notes for the trial."""
        notes = [
            "System: single_agent",
            "Ticker: " + config.ticker,
            "Research question: " + config.research_question,
            "Model: " + config.model_name,
            "Runtime: " + f"{runtime:.2f}s",
            "Call count: " + str(self._call_count),
        ]
        if hasattr(config, "estimated_cost") and config.estimated_cost is not None:
            notes.append("Estimated cost: $" + f"{config.estimated_cost:.4f}")
        return " | ".join(notes)


class SingleAgentPipeline:
    """Pipeline wrapper for the single-agent baseline."""

    baseline: SingleAgentBaseline = Field(default_factory=SingleAgentBaseline)
    allow_network: bool = Field(default=False, description="Allow network access (ignored for baseline)")

    async def run_trial(self, config: ExperimentConfig) -> ExperimentResult:
        """Run a single trial of the baseline research system."""
        return await self.baseline.research(config)

    def reset_call_count(self) -> None:
        """Reset the internal call counter."""
        self.baseline._call_count = 0
        self.baseline._total_tokens = None


# Convenience function for running a baseline trial
async def run_baseline_trial(
    experiment_id: str,
    research_question: str,
    ticker: str,
    model_name: str = "claude-sonnet-4-20250514",
    trial_number: int = 1,
    allow_network: bool = False,
) -> ExperimentResult:
    """Run a single baseline trial with the given configuration.

    Args:
        experiment_id: Unique experiment identifier
        research_question: The research question
        ticker: Company ticker symbol
        model_name: LLM model name
        trial_number: Trial number for repeated trials
        allow_network: Network authorization flag (ignored for baseline)

    Returns:
        ExperimentResult with the research output and metrics
    """
    from fris.llms.mock import MockClient

    client = MockClient(model=model_name)
    baseline = SingleAgentBaseline(client=client, model=model_name)

    config = ExperimentConfig(
        experiment_id=experiment_id,
        research_question=research_question,
        ticker=ticker,
        model_name=model_name,
        trial_number=trial_number,
        system_under_evaluation="single_agent",
        start_timestamp=None,  # Will be set by the caller
    )

    result = await baseline.research(config)
    result.start_timestamp = config.start_timestamp or result.start_timestamp
    return result