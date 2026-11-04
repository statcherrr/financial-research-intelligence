"""Research Report module for FRIS Milestone 6.4.

Transforms the ResearchOrchestrator pipeline output into a structured,
auditable financial research report without losing evidence lineage,
verification outcomes, or uncertainty.

Key design principles:
- Preserve original claim lineage and source provenance
- Preserve all five canonical semantic fields independently
- Never present unsupported claims as established facts
- Never convert missing evidence into negative factual conclusions
- Never fabricate financial figures, citations, source metadata, or conclusions
- Prefer deterministic report assembly
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class ReportMetadata(BaseModel):
    """Metadata for the research report."""

    company_ticker: str = Field(
        ..., description="Company ticker symbol (e.g., 'AAPL')"
    )
    company_name: Optional[str] = Field(
        default=None, description="Company name, when available from reports"
    )
    research_question: str = Field(
        ..., description="The research question addressed by the pipeline"
    )
    generation_timestamp: str = Field(
        ...,
        description="ISO timestamp when the report was generated",
    )
    research_scope: str = Field(
        default="full",
        description="Scope of the research: full, fundamentals_only, industry_only",
    )


class ExecutiveSummary(BaseModel):
    """Executive summary of key findings."""

    main_findings: str = Field(
        default="",
        description="Concise summary of main research findings",
    )
    important_agreements: str = Field(
        default="",
        description="Summary of important agreements between specialists",
    )
    important_contradictions: str = Field(
        default="",
        description="Summary of important contradictions between specialists",
    )
    material_limitations: str = Field(
        default="",
        description="Material limitations documented in the report",
    )


class FundamentalsFindings(BaseModel):
    """Fundamentals analysis findings section."""

    specialist_findings: str = Field(
        default="",
        description="Structured specialist findings from FundamentalsAnalyst",
    )
    supporting_evidence: str = Field(
        default="",
        description="Supporting evidence traceability",
    )
    financial_risks: str = Field(
        default="",
        description="Financial risks identified",
    )
    explicit_limitations: str = Field(
        default="",
        description="Explicit limitations from the fundamentals analysis",
    )


class IndustryFindings(BaseModel):
    """Industry analysis findings section."""

    specialist_findings: str = Field(
        default="",
        description="Structured specialist findings from IndustryAnalyst",
    )
    competitive_observations: str = Field(
        default="",
        description="Competitive and industry observations",
    )
    supporting_evidence: str = Field(
        default="",
        description="Supporting evidence traceability",
    )
    explicit_limitations: str = Field(
        default="",
        description="Explicit limitations from the industry analysis",
    )


class SynthesizedFindingReport(BaseModel):
    """A synthesized finding as appears in the final report."""

    claim: str = Field(..., description="The synthesized claim or assertion")
    category: str = Field(
        ..., description="reported_fact, interpretation, or unknown"
    )
    source_specialists: list[str] = Field(
        ..., description="Which specialist(s) provided the basis"
    )
    original_claims: list[str] = Field(
        default_factory=list,
        description="Raw claim text from each source report",
    )
    evidence_references: list[Any] = Field(
        default_factory=list,
        description="Structured provenance references supporting this finding",
    )
    evidence_status: str = Field(
        "unverified",
        description="Evidence status: supported_by_reference, unverified, "
        "insufficient_evidence, evidence_missing",
    )
    limitations: str = Field(
        "",
        description="Explicit limitations on this finding",
    )


class EvidenceCitation(BaseModel):
    """Citation for a piece of evidence in the report."""

    original_specialist: str = Field(
        ..., description="Which specialist generated the original claim"
    )
    original_claim: str = Field(
        ..., description="The exact claim text as it appeared in the source"
    )
    evidence_text: Optional[str] = Field(
        default=None, description="Supporting evidence text from the SEC filing"
    )
    source_url: Optional[str] = Field(
        default=None, description="URL where the evidence was sourced"
    )
    filing_type: Optional[str] = Field(
        default=None, description="Form type: 10-K, 10-Q, 8-K, etc."
    )
    filing_date: Optional[str] = Field(
        default=None, description="ISO filing date, if available"
    )
    accession_number: Optional[str] = Field(
        default=None, description="SEC accession number, if available"
    )
    filing_section: Optional[str] = Field(
        default=None, description="SEC item section (1, 1A, 7, etc.)"
    )


class CitationVerificationReport(BaseModel):
    """Verification outcome for a synthesized claim."""

    claim_being_assessed: str = Field(
        ..., description="The synthesized claim being verified"
    )
    verification_outcome: str = Field(
        ...,
        description="Verification outcome: supported, partially_supported, "
        "contradicted, insufficient_evidence, unverifiable",
    )
    supporting_evidence: str = Field(
        default="",
        description="Evidence supporting the verification outcome",
    )
    explanation_or_limitations: str = Field(
        "",
        description="Explanation of the verification outcome and any limitations",
    )


class OverallLimitations(BaseModel):
    """Aggregate limitations from the full pipeline."""

    missing_evidence: str = Field(
        default="",
        description="Evidence that could not be preserved or retrieved",
    )
    incomplete_coverage: str = Field(
        default="",
        description="Research question scope not fully addressed",
    )
    retrieval_failures: str = Field(
        default="",
        description="Retrieval statuses that prevent evidence access",
    )
    unverifiable_claims: str = Field(
        default="",
        description="Claims marked as unverifiable with rationale",
    )
    overall_limitations_text: str = Field(
        "",
        description="Full text of all aggregate limitations",
    )


class ResearchReport(BaseModel):
    """
    Complete structured research report generated from the FRIS pipeline.

    This report transforms the ResearchOrchestrator pipeline output into a
    coherent, auditable research artifact without losing evidence lineage,
    verification outcomes, or uncertainty.

    The five canonical Milestone 6.1 semantic fields are preserved independently:
    - evidence_preserved: traceability of original claims + provenance
    - input_compatible: report suitability for the requested synthesis
    - synthesis_complete: adequacy of evidence coverage
    - source_provenance_present: at least one source-related field populated
    - source_provenance_complete: enough locator info for independent inspection
    """

    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True,
    }

    report_metadata: ReportMetadata = Field(
        ..., description="Basic report metadata"
    )
    executive_summary: ExecutiveSummary = Field(
        ..., description="Executive summary of key findings"
    )
    fundamentals_analysis: FundamentalsFindings = Field(
        ..., description="Fundamentals analysis findings"
    )
    industry_analysis: IndustryFindings = Field(
        ..., description="Industry analysis findings"
    )
    synthesized_findings: list[SynthesizedFindingReport] = Field(
        default_factory=list,
        description="Synthesized findings with preserved claim lineage",
    )
    evidence_citations: list[EvidenceCitation] = Field(
        default_factory=list,
        description="Evidence citations with full provenance",
    )
    citation_verifications: list[CitationVerificationReport] = Field(
        default_factory=list,
        description="Claim-level verification outcomes",
    )
    overall_limitations: OverallLimitations = Field(
        ...,
        description="Aggregate limitations from the full pipeline",
    )
    research_quality_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="All five canonical semantic fields and derived metrics",
    )

    def model_dump_json(self, **kwargs: Any) -> str:
        """Serialize the report to JSON, preserving field types and names."""
        return self.model_dump_json(**kwargs)


class ResearchReportBuilder:
    """
    Builder that consumes a ResearchOrchestrator result and produces a
    structured ResearchReport.

    Preserves:
    - Original claim lineage and source provenance
    - All five canonical semantic fields independently
    - Individual verification outcomes
    - Partially verified and unverifiable claims
    - Input immutability (never modifies the orchestration result)
    """

    def __init__(self, orchestrator_result: Any) -> None:
        """Initialize with an OrchestrationResult from Milestone 6.3.

        Args:
            orchestrator_result: The OrchestrationResult from
                ResearchOrchestrator.run_pipeline()
        """
        self.orchestrator_result = orchestrator_result
        self._report: Optional[ResearchReport] = None

    def build(self) -> ResearchReport:
        """Build the complete research report from the orchestrator result.

        Returns:
            A ResearchReport with all pipeline outputs transformed into
            a structured, auditable format.
        """
        self._report = self._construct_report()
        return self._report

    def _construct_report(self) -> ResearchReport:
        """Construct the ResearchReport from the orchestrator result components."""
        # Extract report metadata
        metadata = self._build_metadata()

        # Build executive summary
        exec_summary = self._build_executive_summary()

        # Build fundamentals analysis
        fundamentals = self._build_fundamentals_analysis()

        # Build industry analysis
        industry = self._build_industry_analysis()

        # Build synthesized findings
        synthesized = self._build_synthesized_findings()

        # Build evidence citations
        citations = self._build_evidence_citations()

        # Build citation verifications
        verifications = self._build_citation_verifications()

        # Build overall limitations
        limitations = self._build_overall_limitations()

        # Build research quality metadata (five canonical fields)
        quality_meta = self._build_quality_metadata()

        return ResearchReport(
            report_metadata=metadata,
            executive_summary=exec_summary,
            fundamentals_analysis=fundamentals,
            industry_analysis=industry,
            synthesized_findings=synthesized,
            evidence_citations=citations,
            citation_verifications=verifications,
            overall_limitations=limitations,
            research_quality_metadata=quality_meta,
        )

    def _build_metadata(self) -> ReportMetadata:
        """Build report metadata from orchestrator result."""
        ticker = (
            self.orchestrator_result.fundamentals_report.company_ticker
            if self.orchestrator_result.fundamentals_report
            else "UNKNOWN"
        )
        company_name = None
        if self.orchestrator_result.fundamentals_report:
            cn = getattr(
                self.orchestrator_result.fundamentals_report, "company_name", None
            )
            if cn:
                company_name = cn

        research_question = (
            getattr(
                self.orchestrator_result.fundamentals_report,
                "research_question",
                "",
            )
            or self.orchestrator_result.research_question
            or ""
        )

        # Get timestamp from synthesis result if available
        synth_result = getattr(
            self.orchestrator_result, "synthesis_result", None
        )
        report_timestamp = (
            synth_result.report_timestamp
            if synth_result
            else datetime.now(timezone.utc).isoformat()
        )

        return ReportMetadata(
            company_ticker=ticker,
            company_name=company_name,
            research_question=research_question,
            generation_timestamp=report_timestamp,
            research_scope=self._determine_scope(),
        )

    def _determine_scope(self) -> str:
        """Determine the research scope."""
        fa = self.orchestrator_result.fundamentals_report
        ia = self.orchestrator_result.industry_report

        if fa is not None and ia is not None:
            return "full"
        elif fa is not None:
            return "fundamentals_only"
        elif ia is not None:
            return "industry_only"
        else:
            return "minimal"

    def _build_executive_summary(self) -> ExecutiveSummary:
        """Build executive summary from pipeline outputs."""
        # Gather agreements and contradictions from synthesis
        synth_result = getattr(
            self.orchestrator_result, "synthesis_result", None
        )

        agreements = synth_result.agreements if synth_result else []
        contradictions = synth_result.contradictions if synth_result else []

        # Gaps from synthesis
        research_gaps = synth_result.research_gaps if synth_result else []

        # Summary of main findings - synthesized findings with claims
        synthesized_findings = synth_result.synthesized_findings if synth_result else []

        main_findings_parts = []
        for finding in synthesized_findings:
            claim = getattr(finding, "claim", None)
            if claim and bool(claim.strip()):
                main_findings_parts.append(claim.strip())

        main_findings = ". ".join(main_findings_parts) + "." if main_findings_parts else ""

        # Important agreements - exact text matches
        important_agreements = "; ".join(agreements[:3]) if agreements else ""

        # Important contradictions - documented contradictions
        important_contradictions = "; ".join(
            str(c)[:100] for c in contradictions[:3]
        ) if contradictions else ""

        # Material limitations
        explicit_limitations = (
            synth_result.explicit_limitations if synth_result else ""
        )
        if not explicit_limitations:
            explicit_limitations = "None identified."

        # Research gaps as limitations
        gap_limitations = "; ".join(research_gaps[:3]) if research_gaps else ""

        material_limitations = ". ".join(
            [lim for lim in [explicit_limitations, gap_limitations] if lim]
        ) + "." if (explicit_limitations or gap_limitations) else ""

        return ExecutiveSummary(
            main_findings=main_findings,
            important_agreements=important_agreements,
            important_contradictions=important_contradictions,
            material_limitations=material_limitations,
        )

    def _build_fundamentals_analysis(self) -> FundamentalsFindings:
        """Build fundamentals analysis section."""
        fa = self.orchestrator_result.fundamentals_report

        if fa is None:
            return FundamentalsFindings(
                specialist_findings="No fundamentals report provided",
                supporting_evidence="No fundamentals report; no evidence available",
                financial_risks="No fundamentals report; risk assessment not possible",
                explicit_limitations="No fundamentals report provided for analysis",
            )

        # Extract findings from the fundamentals report
        findings = getattr(fa, "findings", []) or []

        findings_parts = []
        for finding in findings:
            claim = getattr(finding, "claim", None) or getattr(finding, "text", None)
            if claim and bool(claim.strip()):
                findings_parts.append(claim.strip())

        specialist_findings = (
            "; ".join(findings_parts[:5]) + "..."
            if findings_parts
            else "No findings extracted"
        )

        # Supporting evidence traceability
        supporting_evidence = self._extract_evidence_traceability(fa)

        # Financial risks
        financial_risks = self._extract_financial_risks(fa)

        # Explicit limitations
        explicit_limitations = getattr(fa, "explicit_limitations", "") or ""

        return FundamentalsFindings(
            specialist_findings=specialist_findings,
            supporting_evidence=supporting_evidence,
            financial_risks=financial_risks,
            explicit_limitations=explicit_limitations,
        )

    def _build_industry_analysis(self) -> IndustryFindings:
        """Build industry analysis section."""
        ia = self.orchestrator_result.industry_report

        if ia is None:
            return IndustryFindings(
                specialist_findings="No industry report provided",
                competitive_observations="No industry report; competitive assessment not possible",
                supporting_evidence="No industry report; no evidence available",
                explicit_limitations="No industry report provided for analysis",
            )

        # Extract findings from the industry report
        findings = ia.get("findings", []) if isinstance(ia, dict) else getattr(
            ia, "findings", []
        ) or []

        findings_parts = []
        for finding in findings:
            claim = finding.get("claim", None) or finding.get("text", None)
            if claim and bool(claim.strip()):
                findings_parts.append(claim.strip())

        specialist_findings = (
            "; ".join(findings_parts[:5]) + "..."
            if findings_parts
            else "No findings extracted"
        )

        # Competitive observations
        competitive_observations = self._extract_competitive_observations(ia)

        # Supporting evidence traceability
        supporting_evidence = self._extract_evidence_traceability_industry(ia)

        # Explicit limitations
        explicit_limitations = (
            ia.get("explicit_limitations", "") if isinstance(ia, dict) else ""
        ) or ""

        return IndustryFindings(
            specialist_findings=specialist_findings,
            competitive_observations=competitive_observations,
            supporting_evidence=supporting_evidence,
            explicit_limitations=explicit_limitations,
        )

    def _extract_evidence_traceability(self, report: Any) -> str:
        """Extract evidence traceability from a research report."""
        if isinstance(report, dict):
            findings = report.get("findings", [])
        else:
            findings = getattr(report, "findings", []) or []

        evidence_parts = []
        for finding in findings:
            ref = (
                finding.get("evidence_reference")
                if isinstance(finding, dict)
                else getattr(finding, "evidence_reference", None)
            )
            if ref:
                specialist = getattr(ref, "original_specialist", None) or ""
                claim = (
                    getattr(ref, "original_claim", None) or ""
                )[:50]
                evidence_parts.append(
                    f"{specialist}: {claim}..."
                )

        return "; ".join(evidence_parts[:3]) if evidence_parts else "No evidence traceability available"

    def _extract_evidence_traceability_industry(self, report: Any) -> str:
        """Extract evidence traceability from industry report."""
        if isinstance(report, dict):
            findings = report.get("findings", [])
        else:
            findings = getattr(report, "findings", []) or []

        evidence_parts = []
        for finding in findings:
            ref = finding.get("evidence_reference") if isinstance(finding, dict) else None
            if ref:
                specialist = ref.get("original_specialist", "") if isinstance(ref, dict) else getattr(
                    ref, "original_specialist", ""
                )
                claim = (
                    ref.get("original_claim", "") if isinstance(ref, dict) else getattr(
                        ref, "original_claim", ""
                    )
                )[:50]
                evidence_parts.append(
                    f"{specialist}: {claim}..."
                )

        return "; ".join(evidence_parts[:3]) if evidence_parts else "No evidence traceability available"

    def _extract_financial_risks(self, report: Any) -> str:
        """Extract financial risks from a research report."""
        if isinstance(report, dict):
            risks = report.get("risks", report.get("risks_challenges", []))
        else:
            risks = getattr(report, "risks", []) or getattr(
                report, "risks_challenges", []
            ) or []

        risk_parts = []
        for risk in risks[:3]:
            if isinstance(risk, str):
                risk_parts.append(risk[:80])
            elif hasattr(risk, "claim"):
                risk_parts.append(str(risk.claim)[:80])

        return "; ".join(risk_parts) if risk_parts else "No financial risks identified"

    def _extract_competitive_observations(self, report: Any) -> str:
        """Extract competitive observations from an industry report."""
        if isinstance(report, dict):
            obs = report.get("competitive_observations", [])
            if isinstance(obs, str):
                obs = [obs]
        else:
            obs = getattr(report, "competitive_observations", []) or []

        obs_parts = [str(o)[:80] for o in obs[:3] if o]
        return "; ".join(obs_parts) if obs_parts else "No competitive observations available"

    def _build_synthesized_findings(self) -> list[SynthesizedFindingReport]:
        """Build synthesized findings section preserving claim lineage."""
        synth_result = getattr(
            self.orchestrator_result, "synthesis_result", None
        )

        findings = []

        if synth_result is None or not synth_result.synthesized_findings:
            return findings

        for finding in synth_result.synthesized_findings:
            # Get the claim
            claim = getattr(finding, "claim", None) or ""

            # Get category
            category = getattr(finding, "category", "interpretation") or "interpretation"

            # Get source specialists
            source_specialists = getattr(
                finding, "source_specialists", []
            ) or []

            # Get original claims
            original_claims = getattr(finding, "original_claims", []) or []

            # Get evidence references
            evidence_refs = getattr(finding, "evidence_references", []) or []

            # Build evidence citations
            evidence_citations = []
            for ref in evidence_refs:
                if ref is None:
                    continue
                citation = EvidenceCitation(
                    original_specialist=getattr(ref, "original_specialist", "") or "",
                    original_claim=getattr(ref, "original_claim", "") or "",
                    evidence_text=getattr(ref, "evidence_text", None),
                    source_url=getattr(ref, "source_url", None),
                    filing_type=getattr(ref, "filing_type", None),
                    filing_date=getattr(ref, "filing_date", None),
                    accession_number=getattr(ref, "accession_number", None),
                    filing_section=getattr(ref, "filing_section", None),
                )
                evidence_citations.append(citation)

            # Determine evidence status
            evidence_status = getattr(finding, "evidence_status", "unverified") or "unverified"

            # Get limitations
            limitations = getattr(finding, "limitations", "") or ""

            # Build the citation reference list
            citation_refs = []
            for cit in evidence_citations:
                citation_refs.append(
                    f"{cit.original_specialist}: {cit.original_claim[:60]}..."
                    if cit.original_claim
                    else f"{cit.original_specialist}..."
                )

            findings.append(
                SynthesizedFindingReport(
                    claim=claim,
                    category=category,
                    source_specialists=source_specialists,
                    original_claims=original_claims,
                    evidence_references=citation_refs,
                    evidence_status=evidence_status,
                    limitations=limitations,
                )
            )

        return findings

    def _build_evidence_citations(self) -> list[EvidenceCitation]:
        """Build evidence citations with full provenance."""
        citations = []

        # Collect from synthesis result
        synth_result = getattr(
            self.orchestrator_result, "synthesis_result", None
        )

        if synth_result and synth_result.source_reports:
            for report_key, report in synth_result.source_reports.items():
                if report is None:
                    continue

                # Extract EvidenceReferences from source reports
                if isinstance(report, dict):
                    findings = report.get("findings", [])
                else:
                    findings = getattr(report, "findings", []) or []

                for finding in findings:
                    ref = (
                        finding.get("evidence_reference")
                        if isinstance(finding, dict)
                        else getattr(finding, "evidence_reference", None)
                    )
                    if ref is None:
                        continue

                    # Skip if already added
                    if any(
                        e.original_specialist == getattr(ref, "original_specialist", "")
                        and e.original_claim == getattr(ref, "original_claim", "")
                        for e in citations
                    ):
                        continue

                    citation = EvidenceCitation(
                        original_specialist=getattr(ref, "original_specialist", "") or "",
                        original_claim=getattr(ref, "original_claim", "") or "",
                        evidence_text=getattr(ref, "evidence_text", None),
                        source_url=getattr(ref, "source_url", None),
                        filing_type=getattr(ref, "filing_type", None),
                        filing_date=getattr(ref, "filing_date", None),
                        accession_number=getattr(ref, "accession_number", None),
                        filing_section=getattr(ref, "filing_section", None),
                    )
                    citations.append(citation)

        # Also add from fundamentals and industry reports directly
        fa = self.orchestrator_result.fundamentals_report
        ia = self.orchestrator_result.industry_report

        for report, key in [(fa, "fundamentals"), (ia, "industry")]:
            if report is None:
                continue

            if isinstance(report, dict):
                findings = report.get("findings", [])
            else:
                findings = getattr(report, "findings", []) or []

            for finding in findings:
                ref = (
                    finding.get("evidence_reference")
                    if isinstance(finding, dict)
                    else getattr(finding, "evidence_reference", None)
                )
                if ref is None:
                    continue

                # Skip if already added
                if any(
                    e.original_specialist == getattr(ref, "original_specialist", "")
                    and e.original_claim == getattr(ref, "original_claim", "")
                    for e in citations
                ):
                    continue

                citation = EvidenceCitation(
                    original_specialist=getattr(ref, "original_specialist", "") or "",
                    original_claim=getattr(ref, "original_claim", "") or "",
                    evidence_text=getattr(ref, "evidence_text", None),
                    source_url=getattr(ref, "source_url", None),
                    filing_type=getattr(ref, "filing_type", None),
                    filing_date=getattr(ref, "filing_date", None),
                    accession_number=getattr(ref, "accession_number", None),
                    filing_section=getattr(ref, "filing_section", None),
                )
                citations.append(citation)

        return citations

    def _build_citation_verifications(self) -> list[CitationVerificationReport]:
        """Build citation verification outcomes from the verifier result."""
        verifications = []

        ver_result = getattr(
            self.orchestrator_result, "verification_result", None
        )

        if ver_result is None:
            return verifications

        # The verification result has verified_claims or similar structure
        # Extract based on what's available
        verified_claims = getattr(ver_result, "verified_claims", None) or []

        if isinstance(verified_claims, str):
            # Single claim as string
            verified_claims = [verified_claims]

        if not verified_claims:
            return verifications

        for claim_entry in verified_claims:
            if isinstance(claim_entry, dict):
                claim = claim_entry.get("claim", "")
                outcome = claim_entry.get("outcome", "unverifiable")
                explanation = claim_entry.get("explanation", "")
                supporting = claim_entry.get("supporting_evidence", "")
            elif isinstance(claim_entry, str):
                claim = claim_entry
                outcome = "unverifiable"
                explanation = ""
                supporting = ""
            else:
                continue

            if not claim or not bool(claim.strip()):
                continue

            verification = CitationVerificationReport(
                claim_being_assessed=claim.strip(),
                verification_outcome=outcome,
                supporting_evidence=supporting,
                explanation_or_limitations=explanation,
            )
            verifications.append(verification)

        # If no structured verification data but we have synthesis contradictions/agreements,
        # create minimal verification entries
        if not verifications and getattr(
            self.orchestrator_result, "synthesis_result", None
        ):
            synth_result = self.orchestrator_result.synthesis_result
            # Create verification entries based on synthesis outcomes
            for finding in synth_result.synthesized_findings[:3]:
                claim = getattr(finding, "claim", "") or ""
                if claim and bool(claim.strip()):
                    verification = CitationVerificationReport(
                        claim_being_assessed=claim.strip(),
                        verification_outcome="unverifiable",
                        supporting_evidence="",
                        explanation_or_limitations=(
                            f"Claim from {getattr(finding, 'source_specialists', ['unknown'])[0]} "
                            f"not independently verified against source evidence"
                        ),
                    )
                    verifications.append(verification)

        return verifications

    def _build_overall_limitations(self) -> OverallLimitations:
        """Build aggregate limitations from the full pipeline."""
        limitations_parts = []

        # From specialist task limitations
        for task_key, task_result in self.orchestrator_result.tasks.items():
            if task_result.explicit_limitations:
                limitations_parts.append(
                    f"Task {task_key}: {task_result.explicit_limitations}"
                )

        # From synthesis explicit limitations
        synth_result = getattr(
            self.orchestrator_result, "synthesis_result", None
        )
        if synth_result and synth_result.explicit_limitations:
            limitations_parts.append(
                f"Synthesis: {synth_result.explicit_limitations}"
            )

        # From retrieval limitations
        retrieval_result = getattr(
            self.orchestrator_result, "retrieval_result", None
        )
        if retrieval_result:
            retrieval_status = getattr(
                retrieval_result, "retrieval_status", None
            ) or ""
            evidence_source = getattr(
                retrieval_result, "evidence_source", None
            ) or ""
            if retrieval_status in ("failed", "blocked"):
                limitations_parts.append(
                    f"Retrieval: {retrieval_status} "
                    f"(evidence_source: {evidence_source})"
                )

        # From verification limitations
        ver_result = getattr(
            self.orchestrator_result, "verification_result", None
        )
        if ver_result and getattr(ver_result, "overall_limitations", None):
            limitations_parts.append(
                f"Verification: {ver_result.overall_limitations}"
            )

        # From orchestration overall limitations
        if self.orchestrator_result.overall_limitations:
            limitations_parts.append(self.orchestrator_result.overall_limitations)

        # Five canonical fields as limitations context
        synth_result = getattr(
            self.orchestrator_result, "synthesis_result", None
        )
        if synth_result:
            meta = {
                "evidence_preserved": synth_result.evidence_preserved,
                "input_compatible": synth_result.input_compatible,
                "synthesis_complete": synth_result.synthesis_complete,
                "source_provenance_present": synth_result.source_provenance_present,
                "source_provenance_complete": synth_result.source_provenance_complete,
            }
            if not all(meta.values()):
                disclaimer = (
                    f"Semantic fields: evidence_preserved={meta['evidence_preserved']}, "
                    f"input_compatible={meta['input_compatible']}, "
                    f"synthesis_complete={meta['synthesis_complete']}, "
                    f"source_provenance_present={meta['source_provenance_present']}, "
                    f"source_provenance_complete={meta['source_provenance_complete']}"
                )
                limitations_parts.append(disclaimer)

        overall_text = ". ".join(limitations_parts) + "." if limitations_parts else "None identified."

        return OverallLimitations(
            missing_evidence="",
            incomplete_coverage="",
            retrieval_failures="",
            unverifiable_claims="",
            overall_limitations_text=overall_text,
        )

    def _build_quality_metadata(self) -> dict[str, Any]:
        """Build research quality metadata with all five canonical semantic fields."""
        synth_result = getattr(
            self.orchestrator_result, "synthesis_result", None
        )

        # Extract the five canonical fields from synthesis
        meta: dict[str, Any] = {
            "evidence_preserved": synth_result.evidence_preserved
            if synth_result
            else True,
            "input_compatible": synth_result.input_compatible
            if synth_result
            else True,
            "synthesis_complete": synth_result.synthesis_complete
            if synth_result
            else True,
            "source_provenance_present": synth_result.source_provenance_present
            if synth_result
            else True,
            "source_provenance_complete": synth_result.source_provenance_complete
            if synth_result
            else True,
        }

        # Add retrieval status if available
        retrieval_result = getattr(
            self.orchestrator_result, "retrieval_result", None
        )
        if retrieval_result:
            meta["retrieval_status"] = getattr(
                retrieval_result, "retrieval_status", "unknown"
            )
            meta["evidence_source"] = getattr(
                retrieval_result, "evidence_source", "none"
            )

        # Add verification outcome counts if available
        ver_result = getattr(
            self.orchestrator_result, "verification_result", None
        )
        if ver_result and hasattr(ver_result, "verified_claims"):
            claim_outcomes: dict[str, int] = {}
            for claim in ver_result.verified_claims:
                if isinstance(claim, dict):
                    outcome = claim.get("outcome", "unverifiable")
                else:
                    outcome = "unverifiable"
                claim_outcomes[outcome] = claim_outcomes.get(outcome, 0) + 1
            meta["verification_outcome_counts"] = claim_outcomes

        # Add overall status
        meta["overall_status"] = self.orchestrator_result.overall_status.value

        return meta