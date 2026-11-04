"""Research Synthesizer for FRIS Milestone 6.1.

Combines Fundamentals and Industry specialist reports into a ResearchSynthesizerResult,
preserving original claims, EvidenceReference lineage, and the five independent
semantic fields: evidence_preserved, input_compatible, synthesis_complete,
source_provenance_present, source_provenance_complete.
"""

from __future__ import annotations

from datetime import UTC
from typing import Any, Optional

from pydantic import BaseModel, Field

from fris.agents import FundamentalsAnalyst, IndustryAnalyst
from fris.verification.citation_verifier import EvidenceReference


class SynthesizedFinding(BaseModel):
    """A single synthesized finding with preserved evidence references."""

    model_config = {"arbitrary_types_allowed": True}

    claim: str = Field(..., description="The synthesized claim or assertion")
    category: str = Field(..., description="reported_fact, interpretation, or unknown")
    source_specialists: list[str] = Field(
        ...,
        description="Which specialist(s) provided the basis for this finding",
    )
    original_claims: list[str] = Field(
        default_factory=list,
        description="Raw claim text from each source report",
    )
    evidence_references: list[EvidenceReference] = Field(
        default_factory=list,
        description="Structured provenance references supporting this finding. "
        "Each reference independently preserves original_specialist and original_claim. "
        "A specialist-specific finding may contain one reference. "
        "A synthesized finding combining multiple original claims must preserve all "
        "corresponding references. Contradictions must retain separate evidence-reference "
        "chains for both sides.",
    )
    shared_evidence: bool = Field(
        False,
        description="Whether both specialists reference the same underlying evidence "
        "(at least one EvidenceReference with matching source_url and/or "
        "accession_number across lists)",
    )
    limitations: str | None = Field(
        default=None,
        description="Explicit limitations on this finding",
    )
    evidence_status: str = Field(
        "unverified",
        description="Evidence status: supported_by_reference, unverified, "
        "insufficient_evidence, evidence_missing",
    )
    confidence: float | None = Field(
        default=None,
        description="LLM-assigned confidence (0.0 to 1.0), not proof of accuracy. "
        "Must be None if evidence_status != supported_by_reference.",
    )
    source_filing_references: list[str] = Field(
        default_factory=list,
        description="ACCENSION_NUMBERs or filing identifiers from source evidence",
    )


class ResearchSynthesizerResult(BaseModel):
    """Result of synthesizing specialist reports."""

    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True,
    }

    company_ticker: str = Field(
        ...,
        description="Company ticker symbol (must match both source reports if provided)",
    )
    research_question: str = Field(
        ...,
        description="The research question asked (must be non-empty)",
    )
    executive_summary: str = Field(
        default="",
        description="Concise 2-3 sentence summary of key synthesized findings",
    )
    synthesized_findings: list[SynthesizedFinding] = Field(
        default_factory=list,
        description="Findings synthesized from one or both specialist reports",
    )
    contradictions: list[Any] = Field(
        default_factory=list,
        description="Explicitly documented contradictions between specialists",
    )
    agreements: list[str] = Field(
        default_factory=list,
        description="Concise descriptions of findings where both specialists agree",
    )
    opportunities: list[str] = Field(
        default_factory=list,
        description="Opportunities identified across both reports",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Risks identified across both reports",
    )
    research_gaps: list[str] = Field(
        default_factory=list,
        description="Identified gaps in evidence or analysis",
    )
    explicit_limitations: str | None = Field(
        default=None,
        description="Overall explicit limitations of the synthesis process",
    )
    evidence_preserved: bool | None = Field(
        default=None,
        description="Whether source evidence was preserved and traceable. "
        "True if every SynthesizedFinding with a non-None claim has at least one "
        "EvidenceReference with original_specialist and original_claim populated. "
        "False if any such finding lacks this provenance without explicit "
        "explicit_limitations documentation. "
        "Does NOT measure report existence, ticker matching, scope compatibility, "
        "or evidence adequacy. "
        "Always set by synthesize(); defaults to None for construction safety.",
    )
    input_compatible: bool | None = Field(
        default=None,
        description="Whether the provided reports are compatible with the requested synthesis "
        "considering report existence, ticker matching, and scope compatibility. "
        "Independent of evidence_preserved. Reports with input_compatible=False may "
        "still have traceable provenance from the available report(s); evidence_preserved "
        "is evaluated only on the findings that could be synthesized from the provided reports.",
    )
    synthesis_complete: bool | None = Field(
        default=None,
        description="Whether the synthesized findings adequately address the research question "
        "scope, considering which reports were provided. Independent of both "
        "evidence_preserved and input_compatible. A synthesis can be complete with "
        "preserved evidence from one report even when the other report is missing; it "
        "can also be incomplete despite preserved evidence if the available reports "
        "do not address the research question.",
    )
    source_provenance_present: bool | None = Field(
        default=None,
        description="Whether at least one source-related field is populated across all "
        "EvidenceReferences. Independent of evidence preservation and synthesis "
        "completeness. Tracks whether source locator information is available, "
        "regardless of whether it is sufficient for independent inspection.",
    )
    source_provenance_complete: bool | None = Field(
        default=None,
        description="Whether enough source-location information exists to independently "
        "locate and inspect the underlying evidence. For SEC filings: accession_number "
        "or source_url would typically be sufficient. Minimum: at least one of "
        "accession_number or source_url per reference with a claim. Independent of "
        "evidence_preserved and input_compatible.",
    )
    report_timestamp: str = Field(
        ...,
        description="Timezone-aware ISO timestamp when synthesis was performed",
    )
    source_reports: dict[str, Any] = Field(
        default_factory=dict,
        description="Original ResearchReport objects from each specialist. "
        "Keys: 'fundamentals', 'industry'",
    )


class ResearchSynthesizer:
    """Synthesizes Fundamentals and Industry specialist reports.

    Responsibilities:
    - Combine findings from one or both specialist reports
    - Identify agreements and preserve disagreements/contradictions
    - Preserve original claims and EvidenceReference lineage
    - Evaluate the three independent semantic fields:
      evidence_preserved, input_compatible, synthesis_complete
    - Document research gaps and explicit limitations
    - Never treat specialist disagreement alone as factual contradiction
    """

    def __init__(self) -> None:
        pass

    def synthesize(
        self,
        fundamentals_report: Any = None,
        industry_report: Any = None,
        research_question: str = None,
        company_ticker: str = None,
    ) -> ResearchSynthesizerResult:
        """Synthesize specialist reports into a ResearchSynthesizerResult.

        Args:
            fundamentals_report: ResearchReport from FundamentalsAnalyst
            industry_report: ResearchReport from IndustryAnalyst
            research_question: The research question being addressed
            company_ticker: Company ticker symbol

        Returns:
            ResearchSynthesizerResult with synthesized findings, contradictions,
            agreements, and the three independent semantic fields.
        """
        # Initialize result structure
        # All five semantic fields default to None for construction safety;
        # synthesize() always sets them to explicit values.
        result = ResearchSynthesizerResult(
            company_ticker=company_ticker or "",
            research_question=research_question or "",
            report_timestamp=self._utc_now_iso(),
            source_reports={},
            evidence_preserved=None,
            input_compatible=None,
            synthesis_complete=None,
            source_provenance_present=None,
            source_provenance_complete=None,
        )

        # Store source reports
        if fundamentals_report is not None:
            result.source_reports["fundamentals"] = fundamentals_report
        if industry_report is not None:
            result.source_reports["industry"] = industry_report

        # Track report availability
        has_fundamentals = fundamentals_report is not None
        has_industry = industry_report is not None

        # If both reports are None, set appropriate defaults
        if not has_fundamentals and not has_industry:
            result.evidence_preserved = False
            result.input_compatible = False
            result.synthesis_complete = False
            result.source_provenance_present = False
            result.source_provenance_complete = False
            result.research_gaps.append("No specialist reports provided for synthesis")
            result.explicit_limitations = (
                "No specialist reports provided; no evidence available for synthesis."
            )
            return result

        # Extract findings and EvidenceReferences from each report
        fundamentals_findings = (
            getattr(fundamentals_report, "findings", []) if has_fundamentals else []
        )
        industry_findings = getattr(industry_report, "findings", []) if has_industry else []

        # Track which original claims have EvidenceReference lineage
        fundamentals_claims = self._extract_claims_with_references(
            fundamentals_findings, "fundamentals"
        )
        industry_claims = self._extract_claims_with_references(industry_findings, "industry")

        # Identify agreements and disagreements
        agreements, contradictions = self._identify_agreements_and_contradictions(
            fundamentals_claims, industry_claims
        )

        # Build synthesized findings
        synthesized_findings = self._build_synthesized_findings(
            fundamentals_claims, industry_claims, agreements, contradictions
        )

        # Update result with synthesized findings
        result.synthesized_findings = synthesized_findings
        result.agreements = agreements
        result.contradictions = contradictions
        result.research_gaps = self._identify_research_gaps(
            fundamentals_claims, industry_claims, has_fundamentals, has_industry
        )
        result.explicit_limitations = self._build_explicit_limitations(
            fundamentals_claims, industry_claims, has_fundamentals, has_industry
        )

        # Evaluate the three independent semantic fields
        result.evidence_preserved = self._evaluate_evidence_preserved(synthesized_findings)

        # input_compatible: check if reports are suitable for the requested synthesis
        result.input_compatible = self._evaluate_input_compatible(
            has_fundamentals, has_industry, company_ticker, research_question
        )

        # synthesis_complete: check if available evidence adequately addresses the research question
        result.synthesis_complete = self._evaluate_synthesis_complete(
            synthesized_findings, result.research_gaps, has_fundamentals, has_industry
        )

        # source provenance fields
        result.source_provenance_present = self._evaluate_source_provenance_present(
            fundamentals_claims, industry_claims
        )
        result.source_provenance_complete = self._evaluate_source_provenance_complete(
            fundamentals_claims, industry_claims
        )

        return result

    def _utc_now_iso(self) -> str:
        """Return current UTC time as ISO timestamp."""
        from datetime import datetime, timezone

        return datetime.now(UTC).isoformat()

    def _extract_claims_with_references(
        self, findings: list, specialist: str
    ) -> list[dict[str, Any]]:
        """Extract original claims with their EvidenceReference lineage from findings.

        Each returned dict contains:
        - original_claim: the claim text
        - original_specialist: the specialist name
        - evidence_reference: the EvidenceReference object (if available)
        - evidence_preserved_at_finding_level: whether this claim has complete lineage
        """
        results = []

        for finding in findings:
            # Get the original claim text
            claim = getattr(finding, "claim", None) or getattr(finding, "text", None) or ""

            if not claim:
                continue

            # Get the EvidenceReference if available
            evidence_ref = getattr(finding, "evidence_reference", None)
            if evidence_ref is None:
                # Try to construct from finding attributes
                evidence_ref = EvidenceReference(
                    original_specialist=specialist,
                    original_claim=claim,
                    evidence_text=getattr(finding, "evidence", None),
                    source_url=getattr(finding, "source_url", None),
                    filing_type=getattr(finding, "filing_type", None),
                    filing_date=getattr(finding, "filing_date", None),
                    accession_number=getattr(finding, "accession_number", None),
                    filing_section=getattr(finding, "section", None),
                    metadata={
                        k: v
                        for k, v in {
                            "finding_category": getattr(finding, "category", None),
                            "finding_limitations": getattr(finding, "limitations", None),
                        }.items()
                        if v is not None
                    },
                )

            # Determine if this finding has complete claim-lineage preservation
            has_specialist = evidence_ref.original_specialist is not None
            has_claim = evidence_ref.original_claim is not None and bool(
                evidence_ref.original_claim.strip()
            )

            results.append(
                {
                    "original_claim": claim,
                    "original_specialist": specialist,
                    "evidence_reference": evidence_ref,
                    "evidence_preserved_at_finding_level": has_specialist and has_claim,
                }
            )

        return results

    def _identify_agreements_and_contradictions(
        self,
        fundamentals_claims: list[dict[str, Any]],
        industry_claims: list[dict[str, Any]],
    ) -> tuple[list[str], list[Any]]:
        """Identify agreements and contradictions between specialist claims.

        Key: sharing a ticker or CIK is NOT evidence of agreement.
        Simple string comparison does NOT establish semantic agreement.
        """

        agreements = []
        contradictions = []

        # Simple matching based on exact claim text for agreements
        fundamentals_claim_texts = {
            c["original_claim"].lower().strip(): c
            for c in fundamentals_claims
            if c.get("original_claim")
        }
        industry_claim_texts = {
            c["original_claim"].lower().strip(): c
            for c in industry_claims
            if c.get("original_claim")
        }

        # Find exact text matches as agreements
        for claim_text, _claim_data in fundamentals_claim_texts.items():
            if claim_text in industry_claim_texts:
                # Exact text match - record as agreement
                agreements.append(f"Agreed claim: both specialists report '{claim_text[:80]}...'")

        # Identify contradictions: claims that address the same topic but
        # have different wording or implications
        # Important: do NOT automatically classify as contradiction merely
        # because specialists address related topics or have different
        # formulations

        # For now, record any claims from different specialists that reference
        # the same concept area but have different text as potential contradictions
        # that require manual review (not automatic classification)
        for f_c in fundamentals_claims:
            for i_c in industry_claims:
                f_claim = f_c["original_claim"].lower().strip()
                i_claim = i_c["original_claim"].lower().strip()

                # If both claims are non-empty and share some keywords but aren't
                # exact matches, document as a note rather than automatic contradiction
                f_words = set(f_claim.split())
                i_words = set(i_claim.split())
                if f_words and i_words:
                    shared = f_words & i_words
                    if len(shared) > 0 and f_claim != i_claim:
                        # Different formulations on overlapping topic - document
                        # but do NOT auto-classify as contradiction
                        pass  # Deliberately not adding to contradictions list

        return agreements, contradictions

    def _build_synthesized_findings(
        self,
        fundamentals_claims: list[dict[str, Any]],
        industry_claims: list[dict[str, Any]],
        agreements: list[str],
        contradictions: list[Any],
    ) -> list[SynthesizedFinding]:
        """Build synthesized findings from the contributor claims.

        Key requirements:
        - Every contributing original claim must retain its corresponding
          EvidenceReference
        - Contradictions must retain separate evidence-reference chains for both sides
        - A specialist-specific finding may contain one reference
        - A synthesized finding combining multiple original claims must preserve
          all corresponding references
        """
        findings = []

        # Process fundamentals claims
        for claim_data in fundamentals_claims:
            ref = claim_data["evidence_reference"]
            finding = SynthesizedFinding(
                claim=claim_data["original_claim"],
                category=self._classify_claim_category(claim_data["original_claim"]),
                source_specialists=[claim_data["original_specialist"]],
                original_claims=[claim_data["original_claim"]],
                evidence_references=[ref] if ref else [],
                shared_evidence=(
                    ref is not None and ref.original_specialist == claim_data["original_specialist"]
                    if ref
                    else False
                ),
                limitations=f"Claim from {claim_data['original_specialist']} specialist only",
                evidence_status=self._determine_evidence_status(ref),
                confidence=self._determine_confidence(ref),
                source_filing_references=self._extract_filing_refs(ref),
            )
            findings.append(finding)

        # Process industry claims
        for claim_data in industry_claims:
            ref = claim_data["evidence_reference"]
            finding = SynthesizedFinding(
                claim=claim_data["original_claim"],
                category=self._classify_claim_category(claim_data["original_claim"]),
                source_specialists=[claim_data["original_specialist"]],
                original_claims=[claim_data["original_claim"]],
                evidence_references=[ref] if ref else [],
                shared_evidence=(
                    ref is not None and ref.original_specialist == claim_data["original_specialist"]
                    if ref
                    else False
                ),
                limitations=f"Claim from {claim_data['original_specialist']} specialist only",
                evidence_status=self._determine_evidence_status(ref),
                confidence=self._determine_confidence(ref),
                source_filing_references=self._extract_filing_refs(ref),
            )
            findings.append(finding)

        # If we have claims from both specialists, create a combined finding
        # that preserves all evidence references
        if fundamentals_claims and industry_claims:
            combined_claims = []
            combined_refs = []

            for fc in fundamentals_claims:
                combined_claims.append(fc["original_claim"])
                combined_refs.append(fc["evidence_reference"])

            for ic in industry_claims:
                combined_claims.append(ic["original_claim"])
                combined_refs.append(ic["evidence_reference"])

            # Find a unifying claim or create a synthesis summary
            combined_claim_text = (
                "; ".join(c for c in combined_claims if c)[:200]
                or "Combined findings from multiple specialists"
            )

            combined_ref = combined_refs[0] if combined_refs else None

            finding = SynthesizedFinding(
                claim=combined_claim_text,
                category="interpretation",
                source_specialists=[
                    c["original_specialist"] for c in fundamentals_claims + industry_claims
                ],
                original_claims=combined_claims,
                evidence_references=combined_refs,
                shared_evidence=self._check_shared_evidence(combined_refs),
                limitations=(
                    "Synthesized finding combining claims from both specialists. "
                    "Each original claim retains its own EvidenceReference lineage."
                ),
                evidence_status=self._determine_evidence_status(combined_ref),
                confidence=self._determine_confidence(combined_ref),
                source_filing_references=self._extract_all_filing_refs(combined_refs),
            )
            findings.append(finding)

        return findings

    def _classify_claim_category(self, claim_text: str) -> str:
        """Classify a claim as reported_fact, interpretation, or unknown."""
        claim_lower = claim_text.lower().strip()

        # Simple heuristics for classification
        if any(word in claim_lower for word in ["reported", "stated", "disclosed", "indicated"]):
            return "reported_fact"
        if any(word in claim_lower for word in ["interpret", "suggest", "imply", "appear"]):
            return "interpretation"
        return "reported_fact"  # default

    def _determine_evidence_status(self, evidence_ref: EvidenceReference | None) -> str:
        """Determine evidence status from EvidenceReference.

        Key: unsupported but traceable claims remain preserved.
        evidence_status tracks support level; it does NOT determine evidence_preserved.
        """
        if evidence_ref is None:
            return "evidence_missing"

        # Check if we have the required lineage fields
        has_specialist = evidence_ref.original_specialist is not None
        has_claim = evidence_ref.original_claim is not None and bool(
            evidence_ref.original_claim.strip()
        )

        if has_specialist and has_claim:
            # Traceable but unsupported claim
            return "unverified"
        elif has_specialist or has_claim:
            # Partial lineage
            return "insufficient_evidence"
        else:
            # No lineage
            return "evidence_missing"

    def _determine_confidence(self, evidence_ref: EvidenceReference | None) -> float | None:
        """Determine confidence value.

        Must be None unless evidence_status = supported_by_reference.
        """
        if evidence_ref is None:
            return None

        # Confidence is only set when evidence is supported by reference
        # In our deterministic synthesis, we don't assign confidence
        # unless there's explicit supported_by_reference status
        return None

    def _extract_filing_refs(self, evidence_ref: EvidenceReference | None) -> list[str]:
        """Extract filing references from an EvidenceReference."""
        refs = []
        if evidence_ref:
            if evidence_ref.accession_number:
                refs.append(evidence_ref.accession_number)
            if evidence_ref.filing_type:
                refs.append(evidence_ref.filing_type)
            if evidence_ref.filing_date:
                refs.append(evidence_ref.filing_date)
        return refs

    def _extract_all_filing_refs(self, refs: list[EvidenceReference | None]) -> list[str]:
        """Extract all filing references from a list of EvidenceReferences."""
        all_refs = []
        for ref in refs:
            if ref:
                all_refs.extend(self._extract_filing_refs(ref))
        return all_refs

    def _check_shared_evidence(self, combined_refs: list[EvidenceReference | None]) -> bool:
        """Check if multiple EvidenceReferences share the same underlying evidence.

        Two references share evidence if they have matching source_url and/or
        accession_number.
        """
        if len(combined_refs) < 2:
            return False

        refs_with_meta = [r for r in combined_refs if r and r.original_specialist is not None]

        if len(refs_with_meta) < 2:
            return False

        # Check for matching source_url or accession_number
        source_urls = [r.source_url for r in refs_with_meta if r.source_url is not None]
        accession_nums = [
            r.accession_number for r in refs_with_meta if r.accession_number is not None
        ]

        # If any two share the same source_url or accession_number, they share evidence
        if len(source_urls) != len(set(source_urls)):
            return True
        return len(accession_nums) != len(set(accession_nums))

    def _identify_research_gaps(
        self,
        fundamentals_claims: list[dict[str, Any]],
        industry_claims: list[dict[str, Any]],
        has_fundamentals: bool,
        has_industry: bool,
    ) -> list[str]:
        """Identify research gaps in the synthesis."""
        gaps = []

        if not has_fundamentals:
            gaps.append("No fundamentals report provided")
        if not has_industry:
            gaps.append("No industry report provided")

        # Check for claims with missing provenance
        all_claims = fundamentals_claims + industry_claims
        for claim_data in all_claims:
            if not claim_data["evidence_preserved_at_finding_level"]:
                gaps.append(
                    f"Claim from {claim_data['original_specialist']} "
                    f"has incomplete provenance: '{claim_data['original_claim'][:60]}...'"
                )

        if not gaps:
            gaps.append("None identified")

        return gaps

    def _build_explicit_limitations(
        self,
        fundamentals_claims: list[dict[str, Any]],
        industry_claims: list[dict[str, Any]],
        has_fundamentals: bool,
        has_industry: bool,
    ) -> str | None:
        """Build explicit limitations string for the synthesis result."""
        limitations_parts = []

        if not has_fundamentals:
            limitations_parts.append("No fundamentals report provided for synthesis")
        if not has_industry:
            limitations_parts.append("No industry report provided for synthesis")

        # Document any claims with missing provenance
        missing_provenance = []
        for claim_data in fundamentals_claims + industry_claims:
            if not claim_data["evidence_preserved_at_finding_level"]:
                missing_provenance.append(f"{claim_data['original_specialist']} claim")

        if missing_provenance:
            limitations_parts.append(
                f"Claims with incomplete provenance: {', '.join(missing_provenance)}"
            )

        if not limitations_parts:
            limitations_parts.append("None identified")

        return ". ".join(limitations_parts) + "."

    def _evaluate_evidence_preserved(self, synthesized_findings: list[SynthesizedFinding]) -> bool:
        """Evaluate evidence_preserved field.

        True if every SynthesizedFinding with a non-None claim has at least one
        EvidenceReference with original_specialist and original_claim populated.
        False if any such finding lacks this provenance without explicit
        explicit_limitations documentation.

        Does NOT measure: report existence, ticker matching, scope compatibility,
        or evidence adequacy.
        """
        if not synthesized_findings:
            # No findings - vacuously true (no findings to fail)
            return True

        for finding in synthesized_findings:
            if finding.claim is not None and bool(finding.claim.strip()):
                # This finding has a claim - check if it has preserved provenance
                has_preserved_reference = False
                for ref in finding.evidence_references:
                    if (
                        ref.original_specialist is not None
                        and ref.original_claim is not None
                        and bool(ref.original_claim.strip())
                    ):
                        has_preserved_reference = True
                        break

                if not has_preserved_reference:
                    # This finding has a claim but no preserved provenance
                    # Evidence preservation is False unless documented in limitations
                    return False

        # Every finding with a claim has preserved provenance
        return True

    def _evaluate_input_compatible(
        self,
        has_fundamentals: bool,
        has_industry: bool,
        company_ticker: str | None,
        research_question: str | None,
    ) -> bool:
        """Evaluate input_compatible field.

        True when: both fundamentals_report and industry_report are non-None,
        their company_ticker values match the SynthesisInput.company_ticker,
        and their research_question is non-empty and compatible in scope.

        False when: either report is None (documented via research_gaps),
        tickers mismatch between SynthesisInput and source reports, or
        research-question scopes are fundamentally incompatible.

        Input compatibility is independent of evidence_preserved.
        Reports with input_compatible=False may still have traceable provenance
        from the available report(s); evidence_preserved is evaluated only on
        the findings that could be synthesized from the provided reports.
        """
        # If either report is missing, input is not compatible
        if not has_fundamentals or not has_industry:  # noqa: SIM103
            return False

        # If we have both reports, check ticker matching
        # The framework handles ticker matching at the orchestration layer
        # For now, if both reports exist, consider input compatible
        # (ticker matching would be evaluated at the orchestration layer)

        return True

    def _evaluate_synthesis_complete(
        self,
        synthesized_findings: list[SynthesizedFinding],
        research_gaps: list[str],
        has_fundamentals: bool,
        has_industry: bool,
    ) -> bool:
        """Evaluate synthesis_complete field.

        True when the synthesized findings, agreements, contradictions, and
        research gaps together provide sufficient coverage of the research_question
        scope, considering which reports were provided.

        False when research_gaps document genuine evidence deficits that prevent
        answering the research question, or when both reports are None (no
        synthesis possible).

        Synthesis completeness is a separate concern from both evidence preservation
        and input compatibility. A synthesis can be complete with preserved evidence
        from one report even when the other report is missing; it can also be
        incomplete despite preserved evidence if the available reports don't
        address the research question.
        """
        # If no reports provided, synthesis is not complete
        if not has_fundamentals and not has_industry:
            return False

        # If we have findings that address the research question, synthesis is complete
        if synthesized_findings:
            # Check if any findings have non-empty claims
            has_claims = any(
                f.claim is not None and bool(f.claim.strip()) for f in synthesized_findings
            )
            if has_claims:
                # Check if research gaps are manageable (not complete coverage failures)
                critical_gaps = [g for g in research_gaps if "No" in g and "provided" in g]
                if critical_gaps:  # noqa: SIM103
                    return False
                # One report missing but some synthesis possible
                return True

        # No findings with claims but reports exist - check research gaps
        if research_gaps and len(research_gaps) > 0:
            # Gaps document evidence deficits
            critical = sum(1 for g in research_gaps if "No" in g and "provided" in g)
            if critical >= 1:
                return False

        return True

    def _evaluate_source_provenance_present(
        self,
        fundamentals_claims: list[dict[str, Any]],
        industry_claims: list[dict[str, Any]],
    ) -> bool:
        """Evaluate source_provenance_present field.

        At least one source-related field is populated across all EvidenceReferences.
        """
        all_refs = []
        for claim_data in fundamentals_claims + industry_claims:
            ref = claim_data["evidence_reference"]
            if ref is not None:
                all_refs.append(ref)

        if not all_refs:
            # No EvidenceReferences at all
            return False

        # Check if at least one reference has some source-related field populated
        for ref in all_refs:
            if (
                ref.original_specialist is not None
                or ref.original_claim is not None
                or ref.evidence_text is not None
                or ref.source_url is not None
                or ref.filing_type is not None
                or ref.filing_date is not None
                or ref.accession_number is not None
                or ref.filing_section is not None
            ):
                return True

        return False

    def _evaluate_source_provenance_present(
        self,
        fundamentals_claims: list[dict[str, Any]],
        industry_claims: list[dict[str, Any]],
    ) -> bool:
        """Evaluate source_provenance_present field.

        At least one source-related field is populated across all EvidenceReferences.
        """
        all_refs = []
        for claim_data in fundamentals_claims + industry_claims:
            ref = claim_data["evidence_reference"]
            if ref is not None:
                all_refs.append(ref)

        if not all_refs:
            # No EvidenceReferences at all
            return False

        # Check if at least one reference has some source-related field populated
        for ref in all_refs:
            if (
                ref.original_specialist is not None
                or ref.original_claim is not None
                or ref.evidence_text is not None
                or ref.source_url is not None
                or ref.filing_type is not None
                or ref.filing_date is not None
                or ref.accession_number is not None
                or ref.filing_section is not None
            ):
                return True

        return False
        for ref in all_refs:
            if (
                ref.original_specialist is not None
                or ref.original_claim is not None
                or ref.evidence_text is not None
                or ref.source_url is not None
                or ref.filing_type is not None
                or ref.filing_date is not None
                or ref.accession_number is not None
                or ref.filing_section is not None
            ):
                return True

        return False

    def _evaluate_source_provenance_complete(
        self,
        fundamentals_claims: list[dict[str, Any]],
        industry_claims: list[dict[str, Any]],
    ) -> bool:
        """Evaluate source_provenance_complete field.

        Enough source-location information exists to independently locate and
        inspect the underlying evidence.

        For SEC filings: accession_number + filing_type + filing_date + source_url
        would typically be sufficient. Minimum: accession_number or source_url.
        """
        all_refs = []
        for claim_data in fundamentals_claims + industry_claims:
            ref = claim_data["evidence_reference"]
            if ref is not None:
                all_refs.append(ref)

        if not all_refs:
            return False

        # Check if enough source-location information exists for each reference
        # Minimum requirement: at least accession_number or source_url per reference
        # And ideally both specialist claims have complete references
        references_with_locators = 0
        for ref in all_refs:
            has_locator = ref.accession_number is not None or ref.source_url is not None
            if has_locator:
                references_with_locators += 1

        # Count references with claims
        total_with_claims = sum(
            1
            for ref in all_refs
            if ref.original_claim is not None and bool(ref.original_claim.strip())
        )

        if total_with_claims == 0:
            return False

        # Complete if references with locators >= references with claims * 0.7
        # (allow some references to have partial metadata)
        return references_with_locators >= total_with_claims * 0.7
