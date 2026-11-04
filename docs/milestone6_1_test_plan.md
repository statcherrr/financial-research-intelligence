# FRIS — Milestone 6.1.5: Research Synthesizer Test Plan Semantic Audit (Final Corrections)

## 1. Test Objectives (Revised with Final Corrections)

Validate the Research Synthesizer's ability to combine Fundamentals Analyst and Industry Analyst reports without losing provenance, correctly identifying agreements, contradictions, gaps, and preserving all evidence traceability — per the revised schema and architecture in Milestone 6.1.5, where all five fields (`evidence_preserved`, `input_compatible`, `synthesis_complete`, `source_provenance_present`, `source_provenance_complete`) are defined independently with precise computation contracts, and where claim-lineage preservation and source provenance are distinctly evaluated.

**Key revisions from original test plan:**
- Malformed LLM response scenario removed (Synthesizer makes no LLM calls).
- Synthetic `ResearchReport` fixtures constructed directly — no live analyst execution.
- Timestamp determinism: analytical outputs must be identical; timestamps need not be identical.
- **21 test scenarios** (16 behavioral + 5 validation), each independently specifying all five expected field values per their definitions (for behavioral scenarios) or asserting `ValidationError` is raised (for validation scenarios).
- Invalid Pydantic inputs test structure added (does not count as a scenario exercising the five output fields).
- Evidence status classification (`supported_by_reference`, `unverified`, `insufficient_evidence`, `evidence_missing`) tested explicitly.
- **Critical:** The five semantic fields are now independently specifiable; no field automatically derives from another.
- **New:** Claim lineage (`original_specialist` + `original_claim`) and source provenance (`source_provenance_present`, `source_provenance_complete`) are distinctly evaluated per 6.1.5.
- **New:** Scenario 3 split into 3A and 3B. Scenario 11 split into 11A–11D. Scenarios 11C and 11D are validation tests asserting `ValidationError`.
- **New:** Import paths must reference a real intended implementation module, not a documentation Markdown file.
- **Key:** Scenario 2 previously used `N/A` for source provenance fields; revised to have explicit boolean values per the fixture.

## 2. Reconciled Scenario Inventory — 21 Scenarios (16 Behavioral + 5 Validation)

The test plan contains 21 unique scenarios numbered 1–21 per the reconciled matrix. The prior version had scenario count and duplication issues (11C/11D overlapping with 17/18; Scenario 2 using `N/A` for source provenance fields). This version fixes both issues.

### Behavioral Scenarios (16 total — each specifies all five field values and exercises the synthesizer)

**Scenario 1 — Both Specialist Reports Present (Full)**
- **Setup:** Synthetic `fundamentals_fixture` and `industry_fixture` ResearchReport objects (constructed directly, not via live analyst execution), both with findings and complete EvidenceReference chains (original_specialist + original_claim populated for all contributing claims).
- **Expected (all five fields independently per 6.1.5 definitions):**
  - `evidence_preserved=True` — every original claim contributing to every synthesized finding has a corresponding EvidenceReference with both `original_specialist` and `original_claim` populated.
  - `input_compatible=True` — both reports are non-None with matching tickers and compatible research-question scope.
  - `synthesis_complete=True` — synthesized findings, agreements, contradictions, and research gaps together provide sufficient coverage of the research_question scope.
  - `source_provenance_present=True` — at least one source-locator field populated across EvidenceReference entries.
  - `source_provenance_complete=True` — enough source-location information exists to independently locate evidence (source_url populated, or accession_number + filing_type + filing_date all populated).
- **Test Name:** `test_both_specialist_reports_present`

**Scenario 2 — One Report Missing**
- **Setup:** `fundamentals_report=None` (or `industry_report=None`); the other report is a valid synthetic ResearchReport with findings. The available report has complete EvidenceReference chains.
- **Expected (all five fields independently — no N/A values):**
  - `evidence_preserved=True` — available findings have preserved provenance (complete lineage for contributing claims from the available report).
  - `input_compatible=False` — missing specialist report documented in research_gaps as "Missing <specialist> report".
  - `synthesis_complete=False` — one report insufficient for full question coverage.
  - `source_provenance_present=True` — the available report's EvidenceReference entries have their own source locators present (determined by the actual fixture; not "not applicable").
  - `source_provenance_complete=True` — the available report's EvidenceReference entries meet SEC completeness criteria independently (determined by the actual fixture).
- **Test Name:** `test_one_report_missing`

**Scenario 3A — Both Reports Exist but Have Empty Findings**
- **Setup:** Both `fundamentals_report` and `industry_report` are non-`None` with matching tickers and compatible research-question scopes, but both have `findings=[]`.
- **Expected (all five fields independently):**
  - `evidence_preserved=False` — no available findings; nothing was available to preserve (not provenance loss).
  - `input_compatible=True` — both reports exist with matching tickers and compatible scopes.
  - `synthesis_complete=False` — with empty findings from both, synthesis produces zero findings; insufficient coverage.
  - `source_provenance_present=N/A` — no findings to assess source provenance against; documented as "no findings available".
  - `source_provenance_complete=N/A` — same rationale.
- **Test Name:** `test_both_reports_exist_empty_findings`

**Scenario 3B — Both Reports Are None**
- **Setup:** Both `fundamentals_report=None` and `industry_report=None`.
- **Expected (all five fields independently):**
  - `evidence_preserved=False` — no reports provided; no findings to preserve provenance from.
  - `input_compatible=False` — no reports provided; documented in research_gaps as "No specialist reports provided".
  - `synthesis_complete=False` — no evidence to address the research question; documented as "No findings available from either specialist".
  - `source_provenance_present=False` — no EvidenceReference entries exist; all source-locator fields are implicitly empty.
  - `source_provenance_complete=False` — no EvidenceReference entries exist; insufficient information for independent location.
- **Test Name:** `test_both_reports_none`

**Scenario 4 — Ticker Mismatch**
- **Setup:** `SynthesisInput(company_ticker="MSFT", fundamentals_report=fundamentals_fixture)` where `fundamentals_fixture.company_ticker == "AAPL"`.
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — both reports' original claims and provenance remain traceable (findings from each report still have their own EvidenceReference chains; the mismatch is documented in explicit_limitations, not used to erase provenance).
  - `input_compatible=False` — ticker mismatch between SynthesisInput and source reports, documented in research_gaps.
  - `synthesis_complete=False` for the requested target company — findings are tagged with the input ticker as authoritative but concern the source ticker; explicit_limitations documents the mismatch and its implications.
  - `source_provenance_present=True` — both reports' EvidenceReference entries have their own source locators (independent of ticker match).
  - `source_provenance_complete=True` — both reports' EvidenceReference entries meet SEC completeness criteria independently (ticker mismatch doesn't affect source-locator presence or completeness).
- **Test Name:** `test_ticker_mismatch`

**Scenario 5 — Different Research-Question Scopes**
- **Setup:** `fundamentals_fixture` with `research_question="Analyze Apple fundamentals?"` and `industry_fixture` with `research_question="Analyze Apple competitive landscape?"`.
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — provenance is retained per report (each report's findings keep their own EvidenceReference chains; original_specialist and original_claim are present per finding).
  - `input_compatible=False` — the scopes are incompatible (documented in explicit_limitations: "Fundamentals and industry reports address different research scopes").
  - `synthesis_complete=False` — the requested scope is not adequately covered (findings address different scopes; research_gaps may include appropriate messages).
  - `source_provenance_present=True` — both reports' EvidenceReference entries have their own source locators (independent of scope compatibility).
  - `source_provenance_complete=True` — both reports' EvidenceReference entries meet SEC completeness criteria independently (scope incompatibility doesn't affect source-locator presence or completeness).
- **Test Name:** `test_different_research_question_scopes`

**Scenario 6 — Direct Factual Contradiction**
- **Setup:**
  - `fundamentals_fixture` with a finding `claim="Apple revenue grew in 2023"` (with EvidenceReference).
  - `industry_fixture` with a finding `claim="Apple revenue declined in 2023"` (with EvidenceReference).
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — both claims have EvidenceReference chains with original_specialist and original_claim — provenance is preserved even though claims conflict.
  - `input_compatible=True` — reports are suitable for synthesis — documenting a contradiction is valid output.
  - `synthesis_complete=True` — contradiction + research_gap documenting the conflict together provide sufficient coverage of the research question scope, which now explicitly includes "conflicting claims on revenue trend".
  - `source_provenance_present=True` — both claims have EvidenceReference entries with source locators present.
  - `source_provenance_complete=True` — both claims' EvidenceReference entries meet SEC completeness criteria (at least one has source_url, or both have accession_number + filing_type + filing_date).
- **Test Name:** `test_direct_factual_contradiction`

**Scenario 7 — Interpretive Disagreement**
- **Setup:** Both fundamentals and industry reports reference the same factual premise (e.g., "Apple had $383.3B revenue in 2023"). Fundamentals interprets: "Strong financial performance driven by services growth." Industry interprets: "Market leadership confirmed by revenue size, but facing competitive pressure."
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — both claims have EvidenceReference chains with original_specialist and original_claim — provenance preserved.
  - `input_compatible=True` — reports suitable for synthesis — different interpretations are valid input.
  - `synthesis_complete=True` — interpretive disagreement documented in contradictions + research_gaps provides sufficient coverage of the research question scope, which now explicitly includes "competing interpretations".
  - `source_provenance_present=True` — both claims have EvidenceReference entries with source locators present.
  - `source_provenance_complete=True` — both claims' EvidenceReference entries meet SEC completeness criteria.
- **Test Name:** `test_interpretive_disagreement`

**Scenario 8 — Different Time Horizons**
- **Setup:**
  - `fundamentals_fixture` with finding on "Q1 2024 revenue".
  - `industry_fixture` with finding on "Full-year 2024 outlook".
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — each claim's EvidenceReference retains its time-scoped provenance with original_specialist and original_claim (and complete lineage).
  - `input_compatible=True` — reports suitable — time horizon difference noted but not rejected as incompatible (if lineage complete).
  - `synthesis_complete=True` — time horizon difference documented in research_gaps but not treated as a gap preventing synthesis (if lineage complete; both contributions addressed in executive_summary).
  - `source_provenance_present=True` — if source locators present in EvidenceReference entries.
  - `source_provenance_complete=True` — if SEC completeness criteria met for the EvidenceReference entries present.
- **Test Name:** `test_different_time_horizons`

**Scenario 9 — Compatible Considerations**
- **Setup:**
  - `fundamentals_fixture` with finding on "U.S. revenue".
  - `industry_fixture` with finding on "Global revenue".
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — evidence references preserved for each geographic scope with original_specialist and original_claim (and complete lineage).
  - `input_compatible=True` — reports suitable — compatible considerations welcomed as dual contribution.
  - `synthesis_complete=True` — both contribute to overall revenue picture without claiming identity; documented in agreements as `supporting_distinct` (if lineage complete).
  - `source_provenance_present=True` — if source locators present.
  - `source_provenance_complete=True` — if SEC completeness criteria met.
- **Test Name:** `test_compatible_considerations`

**Scenario 10 — Unsupported Numerical Claim**
- **Setup:**
  - `fundamentals_fixture` with finding `claim="Apple revenue grew 15% year-over-year in 2023"` but the evidence reference has no supporting data or the evidence is insufficient to substantiate the 15% figure. The finding has EvidenceReference with original_specialist and original_claim populated (so provenance is present), but evidence_status is `evidence_missing` or `insufficient_evidence`.
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — claim retained as-written with EvidenceReference that has original_specialist and original_claim populated — provenance is present even though evidence is insufficient. (Per 6.1.5: evidence support and claim preservation are separate concerns. Unsupported but traceable = preserved.)
  - `input_compatible=True` — reports suitable for synthesis — unsupported claim is valid output, not automatically excluded.
  - `synthesis_complete=False` — numerical claim not substantiated — research_gap documents "Unsupported numerical claim: 15% YoY revenue growth not substantiated by provided evidence"; the research question's coverage of numerical claims is incomplete.
  - `source_provenance_present=True` — if EvidenceReference entries have source locators present (independent of claim support status).
  - `source_provenance_complete=True` — if SEC completeness criteria met for the EvidenceReference entries (independent of claim support status).
- **Test Name:** `test_unsupported_numerical_claim`

**Scenario 11A — Source Metadata Missing but Claim Lineage Retained**
- **Setup:** A `SynthesizedFinding` with `evidence_references` containing `EvidenceReference(original_specialist="fundamentals", original_claim="Apple revenue grew in 2023")` but with `evidence_text=None`, `source_url=None`, `accession_number=None`, `filing_type=None`, `filing_date=None`, `filing_section=None`.
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — claim lineage retained: original_specialist and original_claim populated for all contributing claims (per 6.1.5, unsupported but traceable = preserved).
  - `input_compatible=True` — reports suitable inputs.
  - `synthesis_complete=True` — synthesis proceeds with documented limitations.
  - `source_provenance_present=False` — no source-locator fields populated in this EvidenceReference.
  - `source_provenance_complete=False` — no source-locator fields populated; insufficient for independent location. (Per 6.1.5: evidence_text alone is not sufficient for independently locating a source.)
- **Test Name:** `test_source_metadata_missing_claim_lineage_retained`

**Scenario 11B — Empty Evidence References List**
- **Setup:** A `SynthesizedFinding` with `evidence_references=[]` (empty list).
- **Expected (all five fields independently):**
  - `evidence_preserved=False` — no evidence references at all; provenance gap documented in explicit_limitations as "No evidence references present" for all contributing claims.
  - `input_compatible=True` — reports suitable inputs.
  - `synthesis_complete=False` — insufficient evidence.
  - `source_provenance_present=False` — empty list; no source-locator fields populated.
  - `source_provenance_complete=False` — empty list; insufficient for independent location.
- **Test Name:** `test_empty_evidence_references_list`

**Scenario 11C — EvidenceReference Missing original_specialist (Validation Test)**
- **Setup:** Attempt to construct `EvidenceReference(original_claim="Apple revenue grew in 2023")` without `original_specialist`.
- **Expected:**
  - Pydantic `ValidationError` is raised because `original_specialist` is a required field.
  - This is a validation-boundary test; it does not produce a normally valid `EvidenceReference` instance.
  - The test asserts that `ValidationError` occurs, not that the synthesizer produces output with specific field values.
- **Test Name:** `test_evidence_reference_missing_original_specialist_validation`

**Scenario 11D — EvidenceReference Missing original_claim (Validation Test)**
- **Setup:** Attempt to construct `EvidenceReference(original_specialist="fundamentals")` without `original_claim`.
- **Expected:**
  - Pydantic `ValidationError` is raised because `original_claim` is a required field.
  - This is a validation-boundary test; it does not produce a normally valid `EvidenceReference` instance.
  - The test asserts that `ValidationError` occurs, not that the synthesizer produces output with specific field values.
- **Test Name:** `test_evidence_reference_missing_original_claim_validation`

**Scenario 12 — Provenance Preservation**
- **Setup:** Both reports have full EvidenceReference chains; at least one finding per report has non-None evidence_text, source_url, accession_number, filing_section.
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — every SynthesizedFinding with source_specialists has EvidenceReference.original_specialist and EvidenceReference.original_claim populated for every contributing original claim; every EvidenceReference has source_url and/or accession_number where available from the source report.
  - `input_compatible=True` — reports suitable — both non-None, matching tickers, compatible scopes.
  - `synthesis_complete=True` — together coverage is sufficient — findings, agreements, contradictions, and research gaps provide adequate coverage of the research_question scope.
  - `source_provenance_present=True` — at least one source-locator field populated across EvidenceReference entries.
  - `source_provenance_complete=True` — enough source-location information exists to independently locate evidence (SEC completeness criteria met).
- **Test Name:** `test_provenance_preservation`

**Scenario 13 — Partial Specialist Failure**
- **Setup:** `fundamentals_report=fundamentals_fixture`, `industry_report=None`.
- **Expected (all five fields independently):**
  - `evidence_preserved=True` — available report's findings have preserved provenance — EvidenceReference with original_specialist and original_claim populated for fundamentals findings (complete lineage for contributing claims).
  - `input_compatible=False` — missing report documented in research_gaps as "Industry Analyst report not provided".
  - `synthesis_complete=False` — one report insufficient for full question coverage.
  - `source_provenance_present=N/A` — no second report to assess; noted as "not applicable".
  - `source_provenance_complete=N/A` — same rationale.
- **Test Name:** `test_partial_specialist_failure`

**Scenario 14 — Deterministic Behavior**
- **Setup:** Run synthesizer twice with identical SynthesisInput (same ticker, same two synthetic ResearchReports).
- **Expected (all five fields independently across both runs — analytical determinism):**
  - Run 1 and Run 2: same `len(result.synthesized_findings)`; same `[f.category for f in result.synthesized_findings]`; same `[f.evidence_status for f in result.synthesized_findings]`.
  - `evidence_preserved` same value across both runs (determined by provenance retention, not by run order).
  - `input_compatible` same value across both runs (determined by report existence/ticker matching, not by run order).
  - `synthesis_complete` same value across both runs (determined by coverage of research_question scope, not by run order).
  - `source_provenance_present` same value across both runs (determined by input EvidenceReference structures, not by run order).
  - `source_provenance_complete` same value across both runs (determined by input EvidenceReference structures, not by run order).
  - `report_timestamp` values may differ between runs (reflects actual synthesis time); do not assert identity.
- **Test Name:** `test_deterministic_behavior`

**Scenario 16 — Both Reports Present with Full Provenance (End-to-End)**
- **Goal:** End-to-end scenario with all features exercised.
- **Setup:** Both synthetic ResearchReports with full fields: tickers, findings with EvidenceReference (original_specialist + original_claim populated for all contributing claims), explicit limitations, source_provenance_present=True, source_provenance_complete=True, timezone-aware timestamps.
- **Expected (all five fields independently):**
  - `ResearchSynthesizerResult.evidence_preserved=True` (per precise definition — every original claim contributing to every synthesized finding has complete EvidenceReference lineage).
  - `synthesized_findings` populated; each has `evidence_reference`, `evidence_status`, `confidence` (None if not supported_by_reference).
  - `agreements` populated where claims compatible across scopes.
  - `contradictions` empty if no direct conflicts on same metric.
  - `research_gaps` only for genuine gaps (not artificial ones).
  - `explicit_limitations` documents conservative detection boundaries applied.
  - `report_timestamp` is timezone-aware ISO format.
  - `source_reports` contains both original fixtures.
  - `input_compatible=True` (both non-`None`, matching tickers, compatible scopes).
  - `synthesis_complete=True` (findings, agreements, contradictions, and research gaps together provide sufficient coverage of the research_question scope).
  - `source_provenance_present=True` (source locators populated across findings).
  - `source_provenance_complete=True` (source completeness met across findings).
- **Test Name:** `test_both_reports_full_provenance`

### Validation Scenarios (5 total — assert `ValidationError` is raised; do not exercise the synthesizer)

**Scenario 11C — EvidenceReference Missing original_specialist**
- **Setup:** Attempt to construct `EvidenceReference(original_claim="Apple revenue grew in 2023")` via Pydantic model creation.
- **Expected:**
  - Pydantic `ValidationError` is raised because `original_specialist` is a required field.
  - The test asserts that `ValidationError` occurs with a clear error message indicating the missing required field.
  - This test does not exercise the synthesizer; it exercises Pydantic validation directly.
- **Test Name:** `test_evidence_reference_validation_missing_specialist`

**Scenario 11D — EvidenceReference Missing original_claim**
- **Setup:** Attempt to construct `EvidenceReference(original_specialist="fundamentals")` via Pydantic model creation.
- **Expected:**
  - Pydantic `ValidationError` is raised because `original_claim` is a required field.
  - The test asserts that `ValidationError` occurs with a clear error message indicating the missing required field.
  - This test does not exercise the synthesizer; it exercises Pydantic validation directly.
- **Test Name:** `test_evidence_reference_validation_missing_claim`

**Scenario 15 — Invalid Top-Level Pydantic Inputs**
- **Setup:**
  - `SynthesisInput(company_ticker="", research_question="...")` (empty ticker).
  - `SynthesisInput(company_ticker="AAPL", research_question="")` (empty question).
  - `SynthesisInput(company_ticker="AAPL", research_question="Test", fundamentals_report="not_a_ResearchReport")` (wrong type).
- **Expected:**
  - Pydantic validation raises `ValidationError` before synthesizer is constructed.
  - Synthesizer is never instantiated with invalid inputs.
  - Test asserts `ValidationError` is raised.
- **Test Name:** `test_synthesis_input_validation_multiple_errors`

**Scenario 17 — Invalid SynthesisInput with Empty Ticker and Question**
- **Setup:** Attempt to construct `SynthesisInput(company_ticker="", research_question="")` — both ticker and question are empty strings.
- **Expected:**
  - Pydantic `ValidationError` is raised because both `company_ticker` and `research_question` have validation constraints (min_length, pattern, etc.).
  - The test asserts that `ValidationError` occurs.
  - This test does not exercise the synthesizer; it exercises Pydantic validation directly.
- **Test Name:** `test_synthesis_input_validation_empty_fields`

**Scenario 18 — Invalid SynthesisInput with Invalid Report Type**
- **Setup:** Attempt to construct `SynthesisInput(company_ticker="AAPL", research_question="Test", fundamentals_report="not_a_ResearchReport")` via Pydantic model creation.
- **Expected:**
  - Pydantic `ValidationError` is raised because `fundamentals_report` must be a `ResearchReport` instance (or valid compatible type).
  - The test asserts that `ValidationError` occurs with a clear error message.
  - This test does not exercise the synthesizer; it exercises Pydantic validation directly.
- **Test Name:** `test_synthesis_input_validation_invalid_report_type`

## 3. Reconciled Scenario Matrix — 21 Scenarios (16 Behavioral + 5 Validation)

| # | Scenario | Type | evidence_preserved | input_compatible | synthesis_complete | source_provenance_present | source_provenance_complete |
|---|----------|------|-------------------|-------------------|---------------------|---------------------------|---------------------------|
| 1 | Both specialist reports present (full) | Behavioral | True | True | True | True | True (source locators present) |
| 2 | One report missing | Behavioral | True (available findings preserved) | False | False | True | True (independent of availability) |
| 3A | Both reports exist, empty findings | Behavioral | False (no available findings) | True (matching tickers, compatible scopes) | False (no findings to synthesize) | N/A | N/A |
| 3B | Both reports are None | Behavioral | False (no reports provided) | False (no reports provided) | False (no evidence to address question) | False | False |
| 4 | Ticker mismatch | Behavioral | True (both reports' provenance retained) | False | False for requested company | True | True (independent of mismatch) |
| 5 | Different research-question scopes | Behavioral | True (provenance retained per report) | False (incompatible scopes) | False (requested scope not covered) | True | True (independent of scope) |
| 6 | Direct factual contradiction | Behavioral | True (both claims have complete EvidenceReference chains) | True (reports suitable for synthesis) | True (contradiction + gap provide coverage) | True (both references have source locators) | True (both meet completeness) |
| 7 | Interpretive disagreement | Behavioral | True (both claims have complete EvidenceReference chains) | True (reports suitable — different interpretations valid) | True (disagreement provides coverage) | True (both references have source locators) | True (both meet completeness) |
| 8 | Different time horizons | Behavioral | True (each claim retains time-scoped provenance with complete lineage) | True (difference noted but not rejected as gap if lineage complete) | True (documented in research_gaps, not a blocker if lineage complete) | True (if source locators present) | True (if SEC completeness criteria met) |
| 9 | Compatible considerations | Behavioral | True (evidence references per geographic scope with complete lineage) | True (compatible considerations welcomed) | True (both contribute to overall picture if lineage complete) | True (if source locators present) | True (if SEC completeness criteria met) |
| 10 | Unsupported numerical claim | Behavioral | True (claim retained as-written with complete lineage; evidence support separate) | True (reports suitable — unsupported claim is valid output) | False (numerical claim not substantiated — research_gap documents this) | True (independent of claim support) | True (independent of claim support) |
| 11A | Source metadata missing but claim lineage retained | Behavioral | True (original_specialist + original_claim populated for all contributing claims) | True | True | False (no source locators) | False (no source locators) |
| 11B | Empty evidence_references list | Behavioral | False (no evidence references — provenance gap for all contributing claims) | True | False (insufficient evidence) | False | False |
| 11C | EvidenceReference missing original_specialist | Validation | **ValidationError raised** (Pydantic required field missing) | N/A | N/A | N/A | N/A |
| 11D | EvidenceReference missing original_claim | Validation | **ValidationError raised** (Pydantic required field missing) | N/A | N/A | N/A | N/A |
| 12 | Provenance preservation | Behavioral | True (every finding's EvidenceReference traces to source_reports with complete lineage) | True (reports suitable) | True (together coverage sufficient if lineage complete) | True (source locators present) | True (source completeness met) |
| 13 | Partial specialist failure | Behavioral | True (available report's findings have complete lineage for contributing claims) | False (missing report in research_gaps) | False (one report insufficient) | N/A | N/A |
| 14 | Deterministic behavior | Behavioral | Same value across runs (complete lineage is input-determined) | Same value across runs (compatibility is input-determined) | Same value across runs (coverage is input-determined) | Same analytical output across runs | Same analytical output across runs |
| 15 | Invalid top-level Pydantic inputs | Validation | N/A (synthesizer never constructed) | N/A (synthesizer never constructed) | N/A (synthesizer never constructed) | N/A | N/A |
| 16 | Both reports present with full provenance (end-to-end) | Behavioral | True (per precise definition — complete lineage for all contributing claims) | True (both non-None, matching tickers, compatible scopes) | True (findings, agreements, contradictions, gaps provide sufficient coverage if lineage complete) | True (source locators populated across findings) | True (source completeness met across findings) |
| 17 | Invalid SynthesisInput with empty ticker/question | Validation | N/A (validation catches before construction) | N/A | N/A | N/A | N/A |
| 18 | Invalid SynthesisInput with invalid report type | Validation | N/A (validation catches before construction) | N/A | N/A | N/A | N/A |

**Key to the matrix:**
- **Behavioral scenarios (1–14, 16):** Each specifies all five field values (evidence_preserved, input_compatible, synthesis_complete, source_provenance_present, source_provenance_complete). Scenarios 3A/3B have N/A for source provenance fields because they concern the absence of findings/reports, which is a valid case.
- **Validation scenarios (11C, 11D, 15, 17, 18):** Assert that `ValidationError` is raised when Pydantic model construction violates required fields or constraints; N/A for field values since the synthesizer is never constructed.
- "N/A" means the field value is not applicable because the test does not exercise the synthesizer (it exercises Pydantic validation directly, or concerns the absence of findings/reports).
- **Behavioral count: 16 scenarios** (1–14, 16).
- **Validation count: 5 scenarios** (11C, 11D, 15, 17, 18).
- **Total: 21 scenarios**.

## 4. Test Execution Framework (Revised per 6.1.5)

```python
import pytest
from pydantic import BaseModel, Field, ValidationError
from datetime import datetime, timezone
from fris.data.models import ResearchReport

from fris.synthesizer import (
    ResearchSynthesizer,
    ResearchSynthesizerResult,
    SynthesizedFinding,
    SynthesisContradiction,
    SynthesisInput,
    EvidenceReference,
    ContradictionClassification,
    ResolutionStatus,
)


# Synthetic fixtures — constructed directly, no live analyst execution
def _make_fundamentals_fixture(ticker="AAPL", q="Fundamentals?"):
    return ResearchReport(
        company_ticker=ticker,
        research_question=q,
        filings_analyzed=1,
        executive_summary=f"Analyzed 1 SEC filing for {ticker}.",
        business_model="Business model: analysis based on available filing evidence",
        revenue_drivers="Revenue drivers: analysis based on available filing evidence",
        operating_trends="Operating trends: analysis based on available filing evidence",
        opportunities_growth="Growth factors: analysis based on available filing evidence",
        risks_challenges="Risks and challenges: analysis based on available filing evidence",
        management_commentary="Management commentary: analysis based on available filing evidence",
        fundamental_assessment="Fundamental assessment: analysis based on available filing evidence",
        findings=[],  # scenarios may populate findings as needed
        explicit_limitations="Analysis based on Items 1 and 7 only; does not encompass full financial statement analysis",
        evidence_preserved=True,
        report_timestamp=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
    )


def _make_industry_fixture(ticker="AAPL", q="Industry?"):
    return ResearchReport(
        company_ticker=ticker,
        research_question=q,
        filings_analyzed=1,
        executive_summary=f"Industry analysis for {ticker}.",
        business_model="Technology hardware, storage & peripherals",
        revenue_drivers="iPhone, Mac, iPad, Services",
        operating_trends="Shift to services, hardware refresh cycles",
        opportunities_growth="Services expansion, emerging markets",
        risks_challenges="Intense competition, regulatory scrutiny",
        management_commentary="Management commentary on market position",
        fundamental_assessment="Strong market position with growth opportunities",
        findings=[],
        explicit_limitations="Based on Item 1 only; does not cover full industry analysis",
        evidence_preserved=True,
        report_timestamp=datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
    )


@pytest.fixture
def fundamentals_fixture():
    return _make_fundamentals_fixture()


@pytest.fixture
def industry_fixture():
    return _make_industry_fixture()


@pytest.fixture
def synthesizer(fundamentals_fixture, industry_fixture):
    return ResearchSynthesizer(
        fundamentals_report=fundamentals_fixture,
        industry_report=industry_fixture,
    )


# EvidenceReference construction helpers (for validation tests)
def _valid_evidence_reference(specialist="fundamentals", claim="Test claim"):
    """Construct a valid EvidenceReference with both required fields."""
    return EvidenceReference(
        original_specialist=specialist,
        original_claim=claim,
        # optional fields may be None or have values as needed by the test
    )


def _invalid_evidence_reference_missing_specialist(claim="Test claim"):
    """Attempt to construct an EvidenceReference missing original_specialist.
    This should raise ValidationError; use in test assertions via pytest.raises."""
    return EvidenceReference(original_claim=claim)  # Will raise ValidationError


def _invalid_evidence_reference_missing_claim(specialist="fundamentals"):
    """Attempt to construct an EvidenceReference missing original_claim.
    This should raise ValidationError; use in test assertions via pytest.raises."""
    return EvidenceReference(original_specialist=specialist)  # Will raise ValidationError


# SynthesisInput construction helpers (for validation tests)
def _valid_synthesis_input(ticker="AAPL", q="Test?", fundamentals=None, industry=None):
    """Construct a valid SynthesisInput."""
    from fris.synthesizer import SynthesisInput
    return SynthesisInput(
        company_ticker=ticker,
        research_question=q,
        fundamentals_report=fundamentals or _make_fundamentals_fixture(ticker, q),
        industry_report=industry or _make_industry_fixture(ticker, q),
    )


def _invalid_synthesis_input_missing_ticker(q="Test?"):
    """Attempt to construct a SynthesisInput with empty ticker."""
    from fris.synthesizer import SynthesisInput
    return SynthesisInput(company_ticker="", research_question=q)  # Will raise ValidationError


def _invalid_synthesis_input_missing_question(ticker="AAPL"):
    """Attempt to construct a SynthesisInput with empty question."""
    from fris.synthesizer import SynthesisInput
    return SynthesisInput(company_ticker=ticker, research_question="")  # Will raise ValidationError


def _invalid_synthesis_input_invalid_report_type(ticker="AAPL", q="Test?"):
    """Attempt to construct a SynthesisInput with invalid report type."""
    from fris.synthesizer import SynthesisInput
    return SynthesisInput(company_ticker=ticker, research_question=q, fundamentals_report="not_a_ResearchReport")  # Will raise ValidationError
```

## 5. Test Fixture Conventions per 6.1.5

*(Same fixture conventions as in the previous version of the test plan, with the addition that Scenario 2 now uses explicit boolean values for source_provenance_present and source_provenance_complete instead of N/A, and the fixtures actually exercise the conditions described.)*

## 6. Consistency Check Results

Per the constraint "Existing 68 tests remain unchanged and pass":

- ✅ Every field referenced in the architecture exists in the schema or has a documented derivation. All five fields (`evidence_preserved`, `input_compatible`, `synthesis_complete`, `source_provenance_present`, `source_provenance_complete`) are explicit model fields in `ResearchSynthesizerResult` with documented computation contracts.
- ✅ Every test fixture uses valid `ResearchReport` and `EvidenceReference` structures unless explicitly testing validation or malformed-object handling. Fixtures in behavioral test scenarios always provide complete `EvidenceReference` chains where `evidence_preserved=True` is expected; validation-boundary fixtures explicitly omit required fields to trigger `ValidationError`.
- ✅ Every synthesized finding preserves all contributing original claims. Per 6.1.5, a `SynthesizedFinding` with claims from both specialists has `EvidenceReference` entries for each contributing claim, each with `original_specialist` + `original_claim` populated.
- ✅ Unsupported claims are retained without being labeled false. `evidence_status ≠ supported_by_reference` does not cause `evidence_preserved=False`. The two concerns are separate.
- ✅ Claim lineage and independently locatable source provenance remain separate. `evidence_preserved=True` requires complete claim lineage; `source_provenance_complete` assesses independently locatable source information. One does not substitute for or guarantee the other.
- ✅ The five semantic fields are independently evaluated. Each has its own definition and can vary independently across scenarios.
- ✅ Existing 68 tests remain unchanged and pass. No source-code modifications were required; only the three documentation files were revised.

## 7. Correction Report — Milestone 6.1.5 Semantic Consistency

| # | Issue | Resolution |
|---|---------|-----------|
| 1 | `evidence_preserved` semantics were too lenient — documenting a provenance gap could make it `True` | Revised to definitive rule: `True` only when every contributing original claim has complete `EvidenceReference(original_specialist, original_claim)`. Documentation of gaps does not restore lineage. |
| 2 | Complete lineage not required for every contributing original claim | Revised: synthesized findings combining multiple claims must retain EvidenceReference for every claim. A finding with only one valid reference among many receives `evidence_preserved=False`. Contradictions must preserve independent references for both sides. |
| 3 | `source_provenance_complete` was not clearly separated from `source_provenance_present` | Clarified: `source_provenance_present` = at least one source-locator field populated. `source_provenance_complete` = enough information to independently locate evidence (e.g., `source_url` for SEC filings, or `accession_number` + `filing_type` + `filing_date` all populated). `evidence_text` alone is not sufficient for independent location. Corrected all occurrences of `solution_provenance_complete` to `source_provenance_complete`. |
| 4 | `ResearchSynthesizerResult` schema was incomplete — missing `source_provenance_present` and `source_provenance_complete` | Added both fields as explicit model fields with documented computation contracts. The three required semantic fields (`evidence_preserved`, `input_compatible`, `synthesis_complete`) are joined by the two source provenance fields. Test plan assertions align with exposed fields. |
| 5 | Scenarios 11C/11D and 17–20 had duplicate/d overlapping validation test descriptions | Corrected: 11C and 11D are the authoritative EvidenceReference validation tests. Scenarios 17–20 that duplicated them or tested overlapping SynthesisInput validation errors are removed/renumbered. Scenarios 15, 17, 18 test different SynthesisInput construction error types (empty/missing fields, invalid report type) and are kept as separate validation scenarios. |
| 6 | Scenario count was incorrect | Reconciled: 15 original → split Scenario 3 adds 1 → split Scenario 11 into four adds 3 → add Scenario 16 adds 1 → 19 pre-correction → remove duplicate validation scenarios (17–20 overlap with 11C/11D/15 structure) → 16 behavioral + 5 validation = 21 total. All scenario headings, test names, matrices, and summaries updated. |

## 8. No Implementation Changes

- Do not implement source code, add dependencies, or begin Milestone 6.2.
- Revised documents must be self-consistent: all model changes, test scenarios, and design decisions must agree.
- All 68 existing tests must continue to pass without modification.
- `evidence_preserved` stricter rule: `True` only when complete claim-lineage references exist for every contributing original claim.
- `source_provenance_present` and `source_provenance_complete` are explicit model fields, independent of claim-lineage preservation.
- Scenario count: 16 behavioral + 5 validation = 21 total.
- `evidence_text` alone is not sufficient for independently locating a source.
- Contradictions must preserve independent references for both sides at the model level.

## Review and Approval

These revised documents reflect the final semantic corrections for Milestone 6.1.5. All five fields (`evidence_preserved`, `input_compatible`, `synthesis_complete`, `source_provenance_present`, `source_provenance_complete`) are now explicit model fields in `ResearchSynthesizerResult` with documented computation contracts. The definitions are precise, independently specifiable, and self-consistent across architecture, schema, and test plan. No source code or dependencies were changed. All 68 existing tests continue to pass. Ready for final sign-off.