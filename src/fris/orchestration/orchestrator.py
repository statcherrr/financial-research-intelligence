"""Research Orchestrator for FRIS.

Coordinates existing specialist agents (Fundamentals Analyst, Industry Analyst),
Research Synthesizer, Edgar Retriever, and Citation Verifier to execute the
full research pipeline. Keeps orchestration separate from specialist research
logic, uses defined agent interfaces, and preserves evidence provenance
throughout all pipeline stages.

Network Authorization:
- Preserves each agent's allow_network policy
- Does not silently elevate agent permissions
- Orchestrator cannot bypass agent-level network authorization
- Defaults to agents with allow_network=False (offline-first design)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fris.agents import FundamentalsAnalyst, IndustryAnalyst


class TaskStatus(Enum):
    """Status of a research task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskType(Enum):
    """Types of research tasks that can be assigned to specialists."""

    FUNDAMENTALS = "fundamentals"
    INDUSTRY = "industry"


@dataclass
class TaskResult:
    """Result of executing a single research task."""

    task_type: TaskType
    ticker: str
    research_question: str
    status: TaskStatus = TaskStatus.PENDING
    findings: dict[str, Any] = field(default_factory=dict)
    explicit_limitations: str = ""
    error: str | None = None
    execution_timestamp: str | None = field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat()
    )
    preserved_evidence: bool = True

    def is_success(self) -> bool:
        """Check if the task executed successfully."""
        return self.status == TaskStatus.COMPLETED and self.error is None

    def is_failure(self) -> bool:
        """Check if the task failed."""
        return self.status == TaskStatus.FAILED

    def is_complete(self) -> bool:
        """Check if the task completed (success or failure)."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)


@dataclass
class OrchestrationResult:
    """Structured result from the Research Orchestrator."""

    tasks: dict[str, TaskResult] = field(default_factory=dict)
    overall_status: TaskStatus = TaskStatus.PENDING
    overall_limitations: str = ""
    evidence_preserved: bool = True
    report_timestamp: str = field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat()
    )
    # Pipeline integration fields
    fundamentals_report: Any = field(default=None, repr=False)
    industry_report: Any = field(default=None, repr=False)
    synthesis_result: Any = field(default=None, repr=False)
    retrieval_result: Any = field(default=None, repr=False)
    verification_result: Any = field(default=None, repr=False)
    # The five canonical Milestone 6.1 semantic fields — independently evaluable
    evidence_preserved: bool = field(default=True, repr=False)
    input_compatible: bool = field(default=True, repr=False)
    synthesis_complete: bool = field(default=True, repr=False)
    source_provenance_present: bool = field(default=True, repr=False)
    source_provenance_complete: bool = field(default=True, repr=False)

    def add_task_result(self, task_result: TaskResult) -> str:
        """Add a task result to the orchestration result.

        Returns a unique task key for tracking.
        """
        task_key = f"{task_result.task_type.value}_{self._ticker}_{len(self.tasks)}"
        self.tasks[task_key] = task_result
        self._update_overall()
        return task_key

    def _update_overall(self) -> None:
        """Update the overall status based on task results."""
        if not self.tasks:
            self.overall_status = TaskStatus.PENDING
            self.overall_limitations = ""
            # Also reset pipeline fields when no tasks
            self.evidence_preserved = True
            self.input_compatible = True
            self.synthesis_complete = True
            self.source_provenance_present = True
            self.source_provenance_complete = True
            return

        completed_count = sum(1 for t in self.tasks.values() if t.is_complete())
        failed_count = sum(1 for t in self.tasks.values() if t.is_failure())
        success_count = sum(1 for t in self.tasks.values() if t.is_success())

        if success_count > 0 and failed_count == 0:
            self.overall_status = TaskStatus.COMPLETED
        elif failed_count > 0 and success_count == 0:
            self.overall_status = TaskStatus.FAILED
        elif failed_count > 0 and success_count > 0:
            self.overall_status = TaskStatus.FAILED
            self.overall_limitations = (
                f"{failed_count} task(s) failed out of {len(self.tasks)} total"
            )
        else:
            self.overall_status = TaskStatus.PENDING

        if completed_count == len(self.tasks) and success_count > 0:
            self.overall_limitations = (
                f"All {len(self.tasks)} tasks completed; findings synthesized below"
            )

    @property
    def task_count(self) -> int:
        """Return the number of tasks tracked."""
        return len(self.tasks)

    def completed_task_count(self) -> int:
        """Return the number of completed tasks."""
        return sum(1 for t in self.tasks.values() if t.is_complete())

    def failed_task_count(self) -> int:
        """Return the number of failed tasks."""
        return sum(1 for t in self.tasks.values() if t.is_failure())

    def success_count(self) -> int:
        """Return the number of successful tasks."""
        return sum(1 for t in self.tasks.values() if t.is_success())


class ResearchOrchestrator:
    """Research Orchestrator that coordinates the full research pipeline.

    Workflow:
    1. Run FundamentalsAnalyst and IndustryAnalyst
    2. Pass their reports into ResearchSynthesizer
    3. Pass synthesized EvidenceReferences into EdgarRetriever
    4. Pass the enriched evidence into CitationVerifier
    5. Aggregate all results into a coherent pipeline result

    Keeps orchestration separate from specialist research logic, uses
    defined agent interfaces, and preserves evidence provenance throughout
    all pipeline stages.

    Network Authorization:
    - Preserves each agent's allow_network policy
    - Does not silently elevate agent permissions
    - Orchestrator cannot bypass agent-level network authorization
    - Defaults to agents with allow_network=False (offline-first design)
    - Retrieval failures are NOT interpreted as evidence against claims
    - Unverifiable claims are NOT treated as false
    - The five canonical semantic fields (evidence_preserved,
      input_compatible, synthesis_complete, source_provenance_present,
      source_provenance_complete) are evaluated independently

    Responsibilities:
    - Accept a research question and company/ticker
    - Decompose the question into specialist research tasks
    - Assign tasks to appropriate agents
    - Coordinate the full pipeline: specialists → synthesis → retrieval → verification
    - Preserve original evidence and provenance at every stage
    - Return a structured orchestration result with all pipeline outputs
    - Ensure input immutability: original specialist reports and synthesis
      results are never mutated by the orchestrator
    """

    def __init__(
        self,
        fundamentals_client: FundamentalsAnalyst | None = None,
        industry_client: IndustryAnalyst | None = None,
        *,
        allow_network: bool = False,
    ) -> None:
        """Initialize the Research Orchestrator.

        Args:
            fundamentals_client: Optional FundamentalsAnalyst (defaults to new instance with allow_network=False)
            industry_client: Optional IndustryAnalyst (defaults to new instance with allow_network=False)
            allow_network: If False (default), block all HTTP/EDGAR retrieval at the
                transport boundary. Consistent with the project's offline-first design
                pattern. All agents and the retriever default to False.
        """

        self.fundamentals = fundamentals_client or FundamentalsAnalyst()
        self.industry = industry_client or IndustryAnalyst()
        self.allow_network = allow_network

    def _import_synthesizer(self):
        """Lazily import ResearchSynthesizer to avoid circular imports."""
        from fris.synthesis import ResearchSynthesizer  # noqa: F811

        return ResearchSynthesizer()

    def _import_retriever(self):
        """Lazily import EdgarRetriever to avoid circular imports."""
        from fris.retrieval.edgar_retriever import EdgarRetriever  # noqa: F811

        return EdgarRetriever(allow_network=self.allow_network)

    def _import_verifier(self):
        """Lazily import CitationVerifier to avoid circular imports."""
        from fris.verification.citation_verifier import CitationVerifier  # noqa: F811

        return CitationVerifier(allow_network=self.allow_network)

    def _decompose_task(self, research_question: str, ticker: str) -> list[dict[str, Any]]:
        """Decompose a research question into specialist tasks.

        Args:
            research_question: The research question to address
            ticker: Company ticker symbol

        Returns:
            List of task specifications
        """
        tasks = []

        # Always assign fundamentals analysis
        tasks.append(
            {
                "task_type": TaskType.FUNDAMENTALS,
                "ticker": ticker,
                "research_question": research_question,
            }
        )

        # Assign industry analysis for ticker-based questions
        if ticker and ticker.strip():
            tasks.append(
                {
                    "task_type": TaskType.INDUSTRY,
                    "ticker": ticker,
                    "research_question": research_question,
                }
            )

        return tasks

    def run_pipeline(
        self,
        ticker: str,
        research_question: str,
    ) -> OrchestrationResult:
        """Execute the full research pipeline.

        The pipeline coordinates all components in sequence:
        1. Run FundamentalsAnalyst and IndustryAnalyst
        2. Pass their reports into ResearchSynthesizer
        3. Pass synthesized EvidenceReferences into EdgarRetriever
        4. Pass the enriched evidence into CitationVerifier
        5. Aggregate all results into a coherent pipeline result

        The orchestrator is read-only: it never mutates the original specialist
        reports, synthesis results, or any nested EvidenceReference objects.

        Args:
            ticker: Company ticker symbol (e.g., "AAPL")
            research_question: The research question to address

        Returns:
            OrchestrationResult with task results, pipeline outputs, and the
            five canonical Milestone 6.1 semantic fields independently evaluated.
        """
        result = OrchestrationResult()

        # Set the ticker on the result for tracking
        object.__setattr__(result, "_ticker", ticker)

        # ------------------------------------------------------------------
        # Step 1: Run specialist agents (Fundamentals and Industry)
        # ------------------------------------------------------------------

        # Execute each task, respecting network authorization
        task_specs = self._decompose_task(research_question, ticker)

        for spec in task_specs:
            task_type = spec["task_type"]
            ticker = spec["ticker"]
            research_question = spec["research_question"]

            task_key = f"{task_type.value}_{ticker}"

            # Check for duplicate task execution
            if task_key in result.tasks:
                # Duplicate detected - skip execution but preserve existing result
                existing = result.tasks[task_key]
                existing.status = TaskStatus.COMPLETED
                continue

            # Create task result
            task_result = TaskResult(
                task_type=task_type,
                ticker=ticker,
                research_question=research_question,
            )

            try:
                # Execute the appropriate agent, respecting allow_network policy
                if task_type == TaskType.FUNDAMENTALS:
                    if not self.fundamentals.allow_network:
                        task_result.status = TaskStatus.COMPLETED
                        task_result.explicit_limitations = (
                            "Network authorization disabled (allow_network=False). "
                            "No SEC HTTP requests made. Ticker resolution used static mapping only."
                        )
                        task_result.findings = {
                            "resolution": {
                                "found": False,
                                "cik": None,
                                "company_name": None,
                                "reason": "Network disabled, using static mapping",
                            }
                        }
                    else:
                        fundamentals_report = self.fundamentals.analyze(ticker, research_question)
                        task_result.status = TaskStatus.COMPLETED
                        task_result.findings = fundamentals_report
                        task_result.explicit_limitations = fundamentals_report.get(
                            "explicit_limitations", ""
                        )

                elif task_type == TaskType.INDUSTRY:
                    if not self.industry.allow_network:
                        task_result.status = TaskStatus.COMPLETED
                        task_result.explicit_limitations = (
                            "Network authorization disabled (allow_network=False). "
                            "No SEC HTTP requests made. Ticker resolution used static mapping only."
                        )
                        task_result.findings = {
                            "resolution": {
                                "found": False,
                                "cik": None,
                                "company_name": None,
                                "reason": "Network disabled, using static mapping",
                            }
                        }
                    else:
                        industry_report = self.industry.analyze(ticker, research_question)
                        task_result.status = TaskStatus.COMPLETED
                        task_result.findings = industry_report
                        task_result.explicit_limitations = industry_report.get(
                            "explicit_limitations", ""
                        )

            except Exception as e:
                task_result.status = TaskStatus.FAILED
                task_result.error = str(e)
                task_result.explicit_limitations = (
                    f"Task execution failed: {str(e)}. Evidence could not be retrieved."
                )

            # Add the task result to the orchestration result
            result.add_task_result(task_result)

        # Get the full reports from the agents (re-run with allow_network policy)
        # We need the full ResearchReport objects for synthesis
        fa_report = self.fundamentals.analyze(ticker, research_question)
        ia_report = self.industry.analyze(ticker, research_question)

        # Store the full reports
        result.fundamentals_report = fa_report
        result.industry_report = ia_report

        # ------------------------------------------------------------------
        # Step 2: Synthesize specialist reports into ResearchSynthesizerResult
        # ------------------------------------------------------------------

        # Lazily import synthesizer
        synthesizer = self._import_synthesizer()
        synthesis_result = synthesizer.synthesize(
            fundamentals_report=fa_report,
            industry_report=ia_report,
            research_question=research_question,
            company_ticker=ticker,
        )
        result.synthesis_result = synthesis_result

        # Update the five semantic fields from the synthesis
        # These are evaluated independently by the synthesizer
        result.evidence_preserved = synthesis_result.evidence_preserved
        result.input_compatible = synthesis_result.input_compatible
        result.synthesis_complete = synthesis_result.synthesis_complete
        result.source_provenance_present = synthesis_result.source_provenance_present
        result.source_provenance_complete = synthesis_result.source_provenance_complete

        # ------------------------------------------------------------------
        # Step 3: Extract EvidenceReferences and pass to EdgarRetriever
        # ------------------------------------------------------------------

        # Collect all EvidenceReference objects from the synthesis and source reports
        evidence_references: list = []

        if synthesis_result is not None and hasattr(synthesis_result, "synthesized_findings"):
            for finding in synthesis_result.synthesized_findings:
                if hasattr(finding, "evidence_references"):
                    for ref in finding.evidence_references:
                        if ref is not None:
                            evidence_references.append(ref)

        # Also add references from source reports directly
        if fa_report is not None and hasattr(fa_report, "findings"):
            for finding in fa_report.findings:
                ref = getattr(finding, "evidence_reference", None)
                if ref is not None:
                    evidence_references.append(ref)

        if ia_report is not None and isinstance(ia_report, dict) and "findings" in ia_report:
            for finding in ia_report["findings"]:
                f_ref = finding.get("evidence_reference", None)
                if f_ref is not None:
                    evidence_references.append(f_ref)

        # Deduplicate while preserving order
        seen = set()
        unique_refs = []
        for ref in evidence_references:
            # Use a hashable key based on original_claim + original_specialist
            if ref.original_claim and ref.original_specialist:
                key = (ref.original_specialist, ref.original_claim[:50])
            else:
                key = (ref.original_specialist or "", ref.original_claim or "")
            if key not in seen:
                seen.add(key)
                unique_refs.append(ref)

        # Lazily import retriever
        retriever = self._import_retriever()
        # Retrieve evidence using EdgarRetriever
        # allow_network is already set on the retriever from the orchestrator init
        retrieval_result = retriever.retrieve(unique_refs)
        result.retrieval_result = retrieval_result

        # The five synthesis fields remain as evaluated in Step 2
        # Retrieval adds retrieval_status and evidence_source dimensions
        # but does not retroactively change the synthesis fields
        # The retrieval status and evidence source are separate dimensions
        # that track where evidence came from and whether retrieval succeeded

        # ------------------------------------------------------------------
        # Step 4: Pass enriched evidence into CitationVerifier
        # ------------------------------------------------------------------

        # Build the input for CitationVerifier.verify()
        # We need: company_ticker, research_question, synthesized_claims,
        #           evidence_references_by_claim

        synthesized_claims: list[str] = []
        evidence_references_by_claim: dict[str, list] = {}

        if synthesis_result is not None and hasattr(synthesis_result, "synthesized_findings"):
            for finding in synthesis_result.synthesized_findings:
                claim = getattr(finding, "claim", None)
                if claim and bool(claim.strip()):
                    synthesized_claims.append(claim.strip())
                    # Collect all EvidenceReferences for this claim
                    refs_for_claim = []
                    if hasattr(finding, "evidence_references"):
                        for ref in finding.evidence_references:
                            if ref is not None:
                                refs_for_claim.append(ref)
                    # Also add refs from source reports
                    if fa_report is not None and hasattr(fa_report, "findings"):
                        for f in fa_report.findings:
                            f_ref = getattr(f, "evidence_reference", None)
                            if f_ref is not None and f_ref not in refs_for_claim:
                                refs_for_claim.append(f_ref)
                    if (
                        ia_report is not None
                        and isinstance(ia_report, dict)
                        and "findings" in ia_report
                    ):
                        for f in ia_report["findings"]:
                            f_ref = f.get("evidence_reference", None)
                            if f_ref is not None and f_ref not in refs_for_claim:
                                refs_for_claim.append(f_ref)
                    evidence_references_by_claim[claim] = refs_for_claim

        # Also add claims from source reports that may not be in synthesis
        if fa_report is not None and hasattr(fa_report, "findings"):
            for finding in fa_report.findings:
                claim = getattr(finding, "claim", None)
                if claim and bool(claim.strip()) and claim not in synthesized_claims:
                    synthesized_claims.append(claim.strip())
                    refs_for_claim = []
                    f_ref = getattr(finding, "evidence_reference", None)
                    if f_ref is not None:
                        refs_for_claim.append(f_ref)
                    evidence_references_by_claim[claim] = refs_for_claim

        if ia_report is not None and isinstance(ia_report, dict) and "findings" in ia_report:
            for finding in ia_report["findings"]:
                claim = finding.get("claim", None)
                if claim and bool(claim.strip()) and claim not in synthesized_claims:
                    synthesized_claims.append(claim.strip())
                    refs_for_claim = []
                    f_ref = finding.get("evidence_reference", None)
                    if f_ref is not None:
                        refs_for_claim.append(f_ref)
                    evidence_references_by_claim[claim] = refs_for_claim

        # Lazily import verifier
        verifier = self._import_verifier()
        # Run CitationVerifier verification
        # The verifier is read-only and does not mutate input objects
        verification_result = verifier.verify(
            company_ticker=ticker,
            research_question=research_question,
            synthesized_claims=synthesized_claims,
            evidence_references_by_claim=evidence_references_by_claim,
        )
        result.verification_result = verification_result

        # The five canonical semantic fields are NOT modified by the verifier.
        # They remain as evaluated in Step 2 (synthesis).
        # The verifier's outcomes (supported, unverifiable, etc.) are separate
        # from the synthesis semantic fields (evidence_preserved, etc.)

        # ------------------------------------------------------------------
        # Step 5: Aggregate limitations and overall status
        # ------------------------------------------------------------------

        # Collect limitations from all pipeline stages
        limitations_parts = []

        # From specialist task limitations
        for task_key, task_result in result.tasks.items():
            if task_result.explicit_limitations:
                limitations_parts.append(f"Task {task_key}: {task_result.explicit_limitations}")

        # From synthesis explicit limitations
        if synthesis_result is not None and synthesis_result.explicit_limitations:
            limitations_parts.append(f"Synthesis: {synthesis_result.explicit_limitations}")

        # From retrieval limitations
        if retrieval_result is not None and retrieval_result.retrieval_status in (
            "failed",
            "blocked",
        ):
            limitations_parts.append(
                f"Retrieval: {retrieval_result.retrieval_status} "
                f"(evidence_source: {retrieval_result.evidence_source})"
            )

        # From verification limitations
        if verification_result is not None and verification_result.overall_limitations:
            limitations_parts.append(f"Verification: {verification_result.overall_limitations}")

        if limitations_parts:
            result.overall_limitations = " . ".join(limitations_parts) + "."
        else:
            result.overall_limitations = "None identified."

        # Final overall status update
        result._update_overall()

        return result

    def orchestrate(
        self,
        ticker: str,
        research_question: str,
    ) -> OrchestrationResult:
        """Execute the full research orchestration pipeline.

        This is an alias for run_pipeline() that maintains backward compatibility
        with the existing API surface.

        Args:
            ticker: Company ticker symbol (e.g., "AAPL")
            research_question: The research question to address

        Returns:
            OrchestrationResult with task results and overall status
        """
        return self.run_pipeline(ticker, research_question)
