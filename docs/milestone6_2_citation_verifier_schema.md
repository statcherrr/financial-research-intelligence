# FRIS — Milestone 6.2: Citation Verifier Schema Design

## 1. Enumerations

### `VerificationOutcome` — Verification Outcome Taxonomy

```python
from enum import Enum

class VerificationOutcome(str, Enum):
    """Typed verification outcome taxonomy — five independent statuses."""

    supported = "supported"
    """The independently retrieved evidence explicitly confirms the claim.
    The evidence text contains the claim statement or directly substantiates it.
    Company-reported figures match the claimed values with the stated reporting period and unit.
    """

    partially_supported = "partially_supported"
    """The evidence partially confirms the claim but has limitations.
    Some aspects of the claim are supported while others are not, or the evidence
    supports a related but narrower statement.
    """

    contradicted = "contradicted"
    """The independently retrieved evidence directly contradicts the claim.
    Example: one filing states 'revenue increased' while the claim states 'revenue decreased',
    or two specialist reports make incompatible claims with supporting evidence.
    """

    insufficient_evidence = "insufficient_evidence"
    """The evidence cannot definitively support or contradict the claim.
    Includes: evidence excerpt too brief, relevant section not included in the filing,
    accession number leads to a different filing, or evidence excerpts exist but do not
    clearly address the claim.
    """

    unverifiable = "unverifiable"
    """The claim cannot be verified due to: missing source (no EvidenceReference),
    unavailable filing (HTTP error, 404, rate limit, inaccessible document),
    insufficient provenance (no source_url, no accession_number + filing_type + filing_date),
    or the claim involves metrics or time periods not present in the available evidence.
    Do not treat missing evidence as proof that the claim is false.
    """
```

## 2. Core Pydantic Models

### 2.1 `EvidenceVerification` — Per-Evidence Verification

```python
class EvidenceVerification(BaseModel):
    """Verification of a single evidence reference against its claim."""

    evidence_reference: EvidenceReference = Field(
        ...,
        description="The EvidenceReference object being verified. "
        "Must have original_specialist and original_claim populated "
        "(validated per Milestone 6.1.5).",
    )
    claim_text: str = Field(
        ...,
        description="The original claim text from the EvidenceReference "
        "or the synthesized finding being assessed.",
    )
    verified_status: VerificationOutcome = Field(
        ...,
        description="The verification outcome: supported, partially_supported, "
        "contradicted, insufficient_evidence, unverifiable.",
    )
    evidence_excerpt: Optional[str] = Field(
        default=None,
        description="The specific evidence passage from the retrieved filing "
        "that was assessed. May be None if retrieval failed.",
    )
    source_location: Optional[str] = Field(
        default=None,
        description="How the evidence was located: source_url, "
        "accession_number + filing_type + filing_date, "
        "or provenance_gap documentation.",
    )
    retrieval_status: Literal["retrieved", "retrieval_failed", "not_attempted"] = Field(
        default="not_attempted",
        description="Whether the evidence retrieval succeeded or failed.",
    )
    retrieval_reason: Optional[str] = Field(
        default=None,
        description="Reason for retrieval failure if applicable: "
        "HTTP error, 404, rate limit, inaccessible, network disabled, etc.",
    )
    comparison_reasoning: str = Field(
        ...,
        description="Text explanation of how the evidence was compared to "
        "the claim and why the outcome was assigned.",
    )
    limitations: str = Field(
        default="",
        description="Explicit limitations on this verification (e.g., excerpt too brief, "
        "period mismatch, only qualitative match possible, LLM confidence low).",
    )
    verified_at: constr(regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$") = Field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat(),
        description="ISO timestamp when this verification was performed.",
    )
```

**Notes:**
- `evidence_reference` must have `original_specialist` and `original_claim` populated;
  construction without these fields raises `ValidationError` per Milestone 6.1.5.
- `source_location` documents the actual locator used; if all source-locator fields are None,
  this is "provenance_gap" and `retrieval_status` will be "not_attempted" or "retrieval_failed".
- `verified_at` must be timezone-aware ISO format per the model config.
- `retrieval_status = "not_attempted"` means the verifier did not attempt retrieval
  (typically because `allow_network` is disabled or provenance is insufficient).

### 2.2 `VerificationIssue` — Per-Issue Tracking

```python
class VerificationIssue(BaseModel):
    """Tracks a specific verification issue or finding."""

    issue_id: str = Field(
        ...,
        description="Unique identifier for this verification issue (e.g., 'issue-001').",
    )
    claim_text: str = Field(
        ...,
        description="The claim being assessed.",
    )
    issue_type: Literal[
        "retrieval_failure",
        "provenance_gap",
        "evidence_mismatch",
        "period_mismatch",
        "metric_undefined",
        "insufficient_coverage",
    ] = Field(
        ...,
        description="The type of issue encountered.",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the issue.",
    )
    severity: Literal["high", "medium", "low"] = Field(
        ...,
        description="Severity of the issue for the overall verification outcome.",
    )
```

### 2.3 `ClaimVerification` — Per-Claim Verification

```python
class ClaimVerification(BaseModel):
    """Verification of a single synthesized claim against its original evidence."""

    synthesized_claim: str = Field(
        ...,
        description="The synthesized claim as it appears in the ResearchSynthesizerResult.",
    )
    original_claim_references: list[str] = Field(
        ...,
        description="List of original claim texts from contributing specialist reports. "
        "One entry per contributing original claim.",
    )
    evidence_references: list[EvidenceReference] = Field(
        ...,
        description="EvidenceReference objects supporting this claim. "
        "Must have original_specialist and original_claim populated per Milestone 6.1.5.",
    )
    verification_status: VerificationOutcome = Field(
        ...,
        description="Overall verification status for this claim.",
    )
    evidence_verifications: list[EvidenceVerification] = Field(
        default_factory=list,
        description="Per-evidence detailed verification entries. "
        "One per EvidenceReference, or per-sub-evidence if multiple references support one claim.",
    )
    verification_issues: list[VerificationIssue] = Field(
        default_factory=list,
        description="List of issues encountered during verification of this claim.",
    )
    evidence_excerpt: Optional[str] = Field(
        default=None,
        description="Best evidence excerpt found supporting or refuting the claim.",
    )
    overall_reasoning: str = Field(
        ...,
        description="Summary of the verification reasoning across all evidence references.",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="LLM-assigned confidence (0.0 to 1.0), if justified. "
        "Must be None if verification_status != supported.",
    )
    verified_at: constr(regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$") = Field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat(),
        description="ISO timestamp when this claim verification was performed.",
    )
    limitations: str = Field(
        default="",
        description="Overall limitations of this verification.",
    )
```

**Key constraints:**
- `evidence_references` must have `original_specialist` and `original_claim` populated
  in each entry; construction without these raises `ValidationError`.
- `confidence` must be `None` unless `verification_status = VerificationOutcome.supported`.
  Prevents assigning confidence to unsupported or unverifiable claims.
- `evidence_excerpt` is the "best" excerpt found across all evidence references;
  may be None if no evidence was successfully retrieved or assessed.
- `overall_reasoning` must explicitly reference the evidence evaluation logic.

### 2.4 `CitationVerificationResult` — Overall Result

```python
class CitationVerificationResult(BaseModel):
    """Overall result from the Citation Verifier."""

    company_ticker: str = Field(
        ...,
        description="Company ticker the verification relates to.",
    )
    research_question: str = Field(
        ...,
        description="The research question being verified.",
    )
    verification_completed: bool = Field(
        ...,
        description="Whether verification was completed for all claims.",
    )
    all_claims_evaluated: bool = Field(
        ...,
        description="Whether every synthesised claim was evaluated.",
    )
    sources_independently_retrieved: bool = Field(
        ...,
        description="Whether evidence sources were independently retrieved "
        "(not just referenced from EvidenceReference metadata). "
        "True only if retrieval_status = 'retrieved' for at least one source.",
    )
    claims: list[ClaimVerification] = Field(
        default_factory=list,
        description="Per-claim verification results. One per synthesized claim.",
    )
    overall_outcome: VerificationOutcome = Field(
        ...,
        description="Overall assessment: supported if all claims supported, "
        "contradicted if any contradicted, insufficient_evidence if no claims "
        "could be definitively supported or contradicted, "
        "unverifiable if all claims are unverifiable due to missing/retrievable evidence.",
    )
    sources_retrieved_successfully: int = Field(
        default=0,
        description="Count of evidence sources successfully retrieved "
        "(retrieval_status = 'retrieved').",
    )
    sources_total: int = Field(
        default=0,
        description="Total number of evidence references attempted.",
    )
    verification_issues: list[VerificationIssue] = Field(
        default_factory=list,
        description="List of all issues encountered across all claims.",
    )
    overall_limitations: str = Field(
        default="",
        description="Overall limitations of the verification process "
        "(e.g., network disabled, partial retrieval, LLM fallback used).",
    )
    verified_at: constr(regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$") = Field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat(),
        description="ISO timestamp when verification was completed.",
    )
```

**Critical independence from Milestone 6.1 fields:**
- `verification_completed` and `all_claims_evaluated` are NOT automatic derivations of
  `evidence_preserved`, `input_compatible`, or `synthesis_complete`.
- `sources_independently_retrieved` is NOT the same as `source_provenance_present`
  or `source_provenance_complete`. A result may have `sources_independently_retrieved=False`
  (retrieval disabled or failed) while `source_provenance_complete=True` (provenance fields populated).
- `overall_outcome` is independent of the five Milestone 6.1 semantic fields.
- The Citation Verifier must NOT retroactively change any Milestone 6.1 field.

### 2.5 `EvidenceReference` — (Reuse from Milestone 6.1, with confirmed fields)

The `EvidenceReference` model from Milestone 6.1 is reused without modification:

```python
class EvidenceReference(BaseModel):
    """Structured reference to the original evidence supporting a synthesized finding."""

    original_specialist: str = Field(
        ...,
        description="Which specialist generated the original claim: 'fundamentals' or 'industry'",
    )
    original_claim: str = Field(
        ...,
        description="The exact claim text as it appeared in the source specialist's report",
    )
    evidence_text: str | None = Field(
        default=None,
        description="Supporting evidence text from the SEC filing, if available",
    )
    source_url: str | None = Field(
        default=None,
        description="URL where the evidence was sourced (SEC filing URL, etc.)",
    )
    filing_type: str | None = Field(
        default=None,
        description="Form type: 10-K, 10-Q, 8-K, etc., if known",
    )
    filing_date: str | None = Field(
        default=None,
        description="ISO filing date, if available",
    )
    accession_number: str | None = Field(
        default=None,
        description="SEC accession number, if available",
    )
    filing_section: str | None = Field(
        default=None,
        description="SEC item section (1, 1A, 7, etc.), if applicable",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Any additional source-location metadata not captured by dedicated fields",
    )
```

**Semantic clarification (from Milestone 6.1.5):**
- `original_specialist` and `original_claim` are the only required fields.
- All other fields (`evidence_text`, `source_url`, `filing_type`, `filing_date`,
  `accession_number`, `filing_section`, `metadata`) are optional.
- An `EvidenceReference` with only `original_specialist` and `original_claim` populated
  (and other fields as None) is sufficient for `evidence_preserved=True` in Milestone 6.1,
  because evidence preservation measures traceability of original claims and provenance.
- `source_provenance_present`: At least one source-related field is populated
  (`source_url` ∨ `accession_number` ∧ `filing_type` ∧ `filing_date`).
- `source_provenance_complete`: Enough source-location information exists to independently
  locate and inspect the underlying evidence (`source_url` ∨ (`accession_number` ∧ `filing_type` ∧ `filing_date`)).
- `evidence_text` alone is NOT sufficient for independently locating a source.

## 3. Validation Rules

### 3.1 EvidenceReference Construction Validation (Milestone 6.1.5)

```python
# These MUST raise ValidationError:
EvidenceReference(original_claim="some claim")  # missing original_specialist
EvidenceReference(original_specialist="fundamentals")  # missing original_claim

# These are valid (other fields default to None):
EvidenceReference(original_specialist="fundamentals", original_claim="some claim")
EvidenceReference(original_specialist="fundamentals", original_claim="some claim", evidence_text="some text")
```

### 3.2 ClaimVerification Validation

```python
# These constraints are enforced at model level:
- Each entry in evidence_references must have original_specialist and original_claim populated.
- If verification_status != VerificationOutcome.supported, confidence must be None.
- synthesized_claim must be non-empty string.
- original_claim_references must have one entry per contributing original claim 
  (length must match the count of contributing claims from the synthesized finding).
- overall_outcome in CitationVerificationResult must be one of the five VerificationOutcome values.
```

### 3.3 CitationVerificationResult Cross-Field Validation

```python
- verification_completed and all_claims_evaluated are independent booleans;
  both may be True, both may be False, or either may be True/False independently.
- sources_independently_retrieved is independent of source_provenance_present
  and source_provenance_complete. All three may have different values.
- overall_outcome should be consistent with the distribution of claims' verification_status:
  - supported: all claims have verification_status = supported
  - contradicted: any claim has verification_status = contradicted
  - insufficient_evidence: no claims have supported or contradicted, and some have insufficient_evidence
  - unverifiable: all claims have verification_status = unverifiable
  - mixed/other: recorded in overall_limitations
- verification_issues across all claims must have unique issue_ids.
```

## 4. Output Contract

### 4.1 Verifier Invocation

```python
# Standalone invocation
result = CitationVerifier.verify(
    synthesizer_result=ResearchSynthesizerResult,
    allow_network: bool = True,  # respects existing network authorization boundaries
) -> CitationVerificationResult
```

### 4.2 Read-Only Guarantee

The `CitationVerifier.verify()` method must be **read-only** with respect to its input:
- It must NOT modify the input `ResearchSynthesizerResult`.
- It must NOT modify any `EvidenceReference` objects within the result.
- It must NOT modify any specialist agent state.
- It must NOT persist any data (no file writes, no database updates, no network caching beyond the single invocation).

### 4.3 Verification Report Format

The output `CitationVerificationResult` can be serialized to JSON for reporting:

```json
{
  "company_ticker": "AAPL",
  "research_question": "What are Apple's main revenue drivers and risk factors?",
  "verification_completed": true,
  "all_claims_evaluated": true,
  "sources_independently_retrieved": true,
  "claims": [
    {
      "synthesized_claim": "Apple reported strong revenue growth in Q3 2024",
      "original_claim_references": ["Apple reported strong revenue growth in Q3 2024"],
      "evidence_references": [
        {
          "original_specialist": "fundamentals",
          "original_claim": "Apple reported strong revenue growth in Q3 2024"
        }
      ],
      "verification_status": "supported",
      "evidence_excerpt": "Revenue of $94.8 billion, up 2.1% year-over-year",
      "overall_reasoning": "Filing 10-Q for Q3 2024 explicitly states revenue of $94.8B",
      "confidence": None,
      "verified_at": "2025-01-15T10:30:00-05:00",
      "limitations": "No comparison to prior quarters provided"
    }
  ],
  "overall_outcome": "supported",
  "sources_retrieved_successfully": 1,
  "sources_total": 1,
  "verification_issues": [],
  "overall_limitations": "",
  "verified_at": "2025-01-15T10:35:00-05:00"
}
```

## 5. How Verifier Outputs Remain Distinct from Milestone 6.1 Fields

| Milestone 6.1 Field | Verifier Output | Key Distinction |
|---|---|---|
| `evidence_preserved` | `sources_independently_retrieved` | `evidence_preserved` = traceability of lineage (`original_specialist`+`original_claim` populated). `sources_independently_retrieved` = actual HTTP retrieval succeeded. A claim can have `evidence_preserved=True` but `sources_independently_retrieved=False` (retrieval disabled or failed). |
| `input_compatible` | N/A (irrelevant to verification) | `input_compatible` assesses whether provided reports were suitable for synthesis. The verifier operates on already-completed synthesis. |
| `synthesis_complete` | N/A (independent concern) | `synthesis_complete` assesses whether synthesized findings adequately address the research question. The verifier assesses individual claim support. |
| `source_provenance_present` | `sources_independently_retrieved` (related but different) | `source_provenance_present` = at least one source-locator field populated. `sources_independently_retrieved` = retrieval actually succeeded. Provenance may be present but retrieval may fail (HTTP 404, network disabled). |
| `source_provenance_complete` | N/A (independent concern) | `source_provenance_complete` = enough locator info to independently find evidence. The verifier actually attempts retrieval and evaluates evidence support. Complete provenance does not guarantee the evidence supports the claim. |

**Explicit rule:** The Citation Verifier must document its own outcomes alongside (not atop) the Milestone 6.1 fields. It must not retroactively alter those fields, and its output schema does not include them as derived properties.

## 6. Deterministic/LLM Separation Markers

```python
# Marker used to distinguish deterministic vs. LLM-assisted assessment
# in comparison_reasoning and limitations fields:

DETERMINISTIC_MARKER = "[deterministic]"
LLM_ASSISTED_MARKER = "[LLM-assisted]"

# Example comparison_reasoning entries:
# "Exact excerpt 'Revenue of $94.8B' found as substring in 10-Q Item 7 text. [deterministic]"
# "LLM assessed whether qualitative description 'strong growth' matches claim; "
# "deterministic check found no explicit figure, so outcome based on LLM assessment. [LLM-assisted]"
```