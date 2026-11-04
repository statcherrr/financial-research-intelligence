"""Synthetic fixtures for Citation Verifier tests.

These fixtures use synthetic evidence and mocked HTTP transports.
No live SEC requests are made during tests.
"""

from src.fris.verification.citation_verifier import (
    CitationVerifier,
    VerificationOutcome,
    EvidenceReference,
    ClaimVerification,
    CitationVerificationResult,
    EvidenceVerification,
    VerificationIssue,
)


# ---------------------------------------------------------------------------
# EvidenceReference fixtures
# ---------------------------------------------------------------------------

# Fully specified EvidenceReference (with source locators)
ref_full = EvidenceReference(
    original_specialist="fundamentals",
    original_claim="Apple reported revenue of $94.8B for Q3 2024",
    source_url="https://www.sec.gov/Archives/edgar/data/320193/20241024/0000320193-24-000012-index.html",
    accession_number="0000320193-24-000012",
    filing_type="10-Q",
    filing_date="2024-08-08",
    filing_section="7",
    evidence_text="Revenue of $94.8 billion, up 2.1% year-over-year",
)

# EvidenceReference with only lineage (no source locators)
ref_lineage_only = EvidenceReference(
    original_specialist="industry",
    original_claim="Competitive pressure may limit future growth",
)

# EvidenceReference with partial provenance
ref_partial = EvidenceReference(
    original_specialist="fundamentals",
    original_claim="Revenue growth driven by iPhone sales",
    source_url="https://www.sec.gov/Archives/edgar/data/320193/20241024/0000320193-24-000012-index.html",
    # accession_number, filing_type, filing_date are None
)

# EvidenceReference missing both required fields (should raise ValidationError)
# This is tested via validation scenarios


# ---------------------------------------------------------------------------
# CitationVerifier fixtures
# ---------------------------------------------------------------------------

# Verifier with network disabled (default)
verifier_offline = CitationVerifier(allow_network=False)

# Verifier with network enabled
verifier_online = CitationVerifier(allow_network=True)


# ---------------------------------------------------------------------------
# Synthetic filing text fixtures (for mocked HTTP transport)
# ---------------------------------------------------------------------------

# Filing text that explicitly contains the claim
filing_with_explicit_claim = (
    "Apple Inc. (AAPL) Q3 2024 Earnings Release.\n"
    "Revenue of $94.8 billion, up 2.1% year-over-year.\n"
    "Net income of $24.2 billion, up 15.3% year-over-year.\n"
    "Item 1. Business: Apple designs iPhones, Macs, iPads, and services.\n"
    "Item 7. MD&A: Management discussion of results."
)

# Filing text with close but not exact numerical match
filing_with_close_numerical = (
    "Apple Inc. Q3 2024 Results.\n"
    "Revenue of $94.5 billion, up 2.0% year-over-year.\n"
    "Net income of $24.0 billion, up 14.8% year-over-year."
)

# Filing text with contradictory claim
filing_with_contradiction = (
    "Apple Inc. Q3 2024 Results.\n"
    "Revenue of $92.1 billion, down 1.5% year-over-year.\n"
    "Net income of $23.5 billion, down 8.2% year-over-year."
)

# Filing text with different time period
filing_different_period = (
    "Apple Inc. Fiscal Year 2023 Results.\n"
    "Revenue of $365.8 billion, up 8.0% year-over-year.\n"
    "Net income of $99.8 billion, up 12.3% year-over-year."
)

# Filing text with no relevant content
filing_no_relevant_content = (
    "Apple Inc. Q3 2024 Proxy Statement.\n"
    "Board of Directors: ..." "\n" "Executive Compensation: ..." "\n" "Stockholder Matters: ..."
)


# ---------------------------------------------------------------------------
# ResearchReport fixtures (minimal)
# ---------------------------------------------------------------------------

class ResearchReport:
    """Minimal fixture representing a specialist report."""

    def __init__(self, specialist: str, ticker: str, claim: str,
                 evidence_reference: EvidenceReference | None = None):
        self.specialist = specialist
        self.ticker = ticker
        self.claim = claim
        self.evidence_reference = evidence_reference or EvidenceReference(
            original_specialist=specialist,
            original_claim=claim
        )


# Pre-built reports for test scenarios
fundamentals_report = ResearchReport(
    specialist="fundamentals",
    ticker="AAPL",
    claim="Apple reported revenue of $94.8B for Q3 2024",
    evidence_reference=ref_full
)

industry_report = ResearchReport(
    specialist="industry",
    ticker="AAPL",
    claim="Competitive pressure may limit future growth",
    evidence_reference=ref_lineage_only
)


# ---------------------------------------------------------------------------
# Test scenario data
# ---------------------------------------------------------------------------

# Scenario 1: Both reports present, claim supported by evidence
scenario_1_claims = ["Apple demonstrated strong financial performance in Q3 2024"]
scenario_1_refs = {
    "Apple demonstrated strong financial performance in Q3 2024": [ref_full]
}

# Scenario 2: One report missing (only fundamentals)
scenario_2_claims = ["Apple's risk factors include regulatory uncertainty"]
scenario_2_refs = {
    "Apple's risk factors include regulatory uncertainty": [ref_full]
}

# Scenario 3: Both reports exist but empty findings
scenario_3_claims = ["No findings available to synthesize"]
scenario_3_refs = {
    "No findings available to synthesize": []
}

# Scenario 4: Ticker mismatch
scenario_4_claims = ["Microsoft's revenue growth driven by cloud"]
scenario_4_refs = {
    "Microsoft's revenue growth driven by cloud": [ref_full]  # ref_full has AAPL ticker context
}

# Scenario 5: Different research-question scopes
scenario_5_claims = ["Apple's services revenue growth"]
scenario_5_refs = {
    "Apple's services revenue growth": [ref_full]
}

# Scenario 6: Direct factual contradiction between specialists
scenario_6_claims = [
    "Apple reported strong revenue growth in Q3 2024",
    "Competitive pressure may limit future growth"
]
scenario_6_refs = {
    "Apple reported strong revenue growth in Q3 2024": [ref_full],
    "Competitive pressure may limit future growth": [ref_lineage_only]
}

# Scenario 7: Interpretive disagreement
scenario_7_claims = [
    "Apple's strong brand loyalty is a competitive advantage",
    "Apple's brand loyalty is overestimated by market analysts"
]
scenario_7_refs = {
    "Apple's strong brand loyalty is a competitive advantage": [ref_full],
    "Apple's brand loyalty is overestimated by market analysts": [ref_lineage_only]
}

# Scenario 8: Different time horizons
scenario_8_claims = ["Apple's revenue for fiscal year 2023"]
scenario_8_refs = {
    "Apple's revenue for fiscal year 2023": [ref_full]
}

# Scenario 9: Compatible considerations
scenario_9_claims = ["Apple's revenue growth and margin pressure are related but distinct"]
scenario_9_refs = {
    "Apple's revenue growth and margin pressure are related but distinct": [ref_full]
}

# Scenario 10: Unsupported numerical claim
scenario_10_claims = ["Apple reported revenue of $10B for FY 2023"]
scenario_10_refs = {
    "Apple reported revenue of $10B for FY 2023": [ref_full]
}

# Scenario 11A: Source metadata missing but claim lineage retained
scenario_11A_claims = ["Apple's growth driven by iPhone"]
scenario_11A_refs = {
    "Apple's growth driven by iPhone": [ref_lineage_only]
}

# Scenario 11B: Empty evidence references list
scenario_11B_claims = ["No evidence to assess"]
scenario_11B_refs = {
    "No evidence to assess": []
}

# Scenario 11C: EvidenceReference missing original_specialist (validation test)
# Scenario 11D: EvidenceReference missing original_claim (validation test)

# Scenario 12: Provenance preservation (all references have complete lineage)
scenario_12_claims = ["Apple's financial performance"]
scenario_12_refs = {
    "Apple's financial performance": [ref_full, ref_lineage_only]
}

# Scenario 13: Partial specialist failure (one report unavailable)
scenario_13_claims = ["Apple's industry analysis"]
scenario_13_refs = {
    "Apple's industry analysis": [ref_full]
}

# Scenario 14: Deterministic behavior (same input → same output)
scenario_14_claims = ["Apple's financial performance"]
scenario_14_refs = {
    "Apple's financial performance": [ref_full]
}

# Scenario 15: Invalid top-level Pydantic inputs (validation test)

# Scenario 16: Both reports present with full provenance (end-to-end)
scenario_16_claims = ["Apple demonstrated strong financial performance in Q3 2024"]
scenario_16_refs = {
    "Apple demonstrated strong financial performance in Q3 2024": [ref_full]
}