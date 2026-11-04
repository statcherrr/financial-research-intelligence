# FRIS — Milestone 6.2: Citation Verifier Architecture & Engineering Design

## 1. System Overview

The Citation Verifier is an independent quality-control layer that evaluates synthesized research claims against their original evidence. It sits between the Research Synthesizer and the final output, assessing claim validity without silently accepting the Synthesizer's interpretation or the specialist agents' outputs.

**Primary objective:** Determine whether cited evidence corresponds to the stated source, whether the evidence supports the associated claim, and classify the support level (supported, partially_supported, contradicted, insufficient_evidence, unverifiable).

**Independence requirement:** The verifier must evaluate original evidence rather than simply accepting the Synthesizer's interpretation. It may use the synthesized claim as the verification target but must independently inspect the underlying EvidenceReference objects and source documents.

**Three distinct concepts the verifier must track:**
- **Claim lineage:** Which specialist produced the original claim (fundamentals or industry). Preserved from Milestone 6.1 `EvidenceReference.original_specialist`.
- **Source provenance:** Where the supporting evidence can be located (SEC filing URL, accession number, filing type, filing date, section). Preserved from Milestone 6.1 `EvidenceReference` source-locator fields.
- **Evidence support:** Whether the source actually supports the claim (supported, partially_supported, contradicted, insufficient_evidence, unverifiable). The verifier's core output.

**The verifier must NOT:**
- Retroactively change the five Milestone 6.1 semantic fields (`evidence_preserved`, `input_compatible`, `synthesis_complete`, `source_provenance_present`, `source_provenance_complete`).
- Treat missing evidence as proof that a claim is false.
- Treat a claim's presence in an SEC filing as automatic proof that the claim is accurate.
- Distinguish company-reported statements from independently established facts without explicit evaluation.
- Fabricate source locations or infer that a source was checked when retrieval did not occur.

## 2. Component Responsibilities

### 2.1 CitationVerifier (Core Component)
- Receives a `ResearchSynthesizerResult` as input.
- For each synthesized claim, identifies contributing original claims and their `EvidenceReference` objects.
- Resolves `EvidenceReference` objects to retrieve original SEC filing evidence.
- Compares each claim against its independently retrieved evidence.
- Assigns a typed verification outcome from the taxonomy.
- Records reasoning, evidence excerpts, and limitations for each claim.
- Produces a `CitationVerificationResult` with per-claim outcomes and overall status.
- Does NOT modify the input `ResearchSynthesizerResult`.
- Does NOT rewrite the synthesized research report; it only annotates and assesses.

### 2.2 EvidenceRetriever (Supporting Component)
- Receives an `EvidenceReference` object.
- Attempts to retrieve the original SEC filing evidence using the existing EDGAR client and ingestion layer.
- Handles retrieval failures gracefully (HTTP errors, rate limits, unavailable filings, malformed responses).
- Distinguishes retrieval failures from evidence-support failures.
- Returns either the retrieved evidence text/excerpt or a "retrieval_failed" marker.
- Does NOT fabricate source locations or claim a source was checked when retrieval did not occur.

### 2.3 VerificationOrchestrator (Optional Integration Layer)
- Coordinates the CitationVerifier across multiple `ResearchSynthesizerResult` instances.
- Aggregates verification outcomes into summary metrics.
- Integrates with the Research Orchestrator's `OrchestrationResult` for end-to-end workflows.
- Does NOT take responsibility for rewriting research reports; handles annotation and assessment only.

## 3. Data Flow

```
ResearchSynthesizerResult
       │
       ▼
CitationVerifier receives input
       │
       ├─► For each SynthesizedFinding:
       │    ├─► Extract claim text
       │    ├─► Identify contributing original claims
       │    ├─► Resolve corresponding EvidenceReference objects
       │    ├─► EvidenceRetriever retrieves original SEC filing evidence
       │    ├─► Compare evidence with claim
       │    ├─► Assign verification outcome (taxonomy)
       │    ├─► Record reasoning, evidence excerpts, limitations
       │    └─► Collect verification data
       │
       ▼
CitationVerificationResult produced
       │
       ▼
Annotates/assesses without modifying original synthesis
```

## 4. Independence Requirement

The verifier evaluates three orthogonal dimensions:

| Dimension | What It Assesses | Preserved From |
|---|---|---|
| **Claim lineage** | Which specialist produced the original claim (`fundamentals` or `industry`) | `EvidenceReference.original_specialist` |
| **Source provenance** | Where supporting evidence can be located (source_url, accession_number, filing_type, filing_date, section) | `EvidenceReference.evidence_text`, `source_url`, `accession_number`, `filing_type`, `filing_date`, `filing_section` |
| **Evidence support** | Whether source actually supports the claim (supported/partially_supported/contradicted/insufficient_evidence/unverifiable) | Verifier's core output — newly computed |

**These three dimensions are independent.** A claim can have complete claim lineage and source provenance but still receive `evidence_support = insufficient_evidence`. Conversely, a claim with incomplete provenance might still be `supported` if the available evidence clearly confirms it. The verifier must track and report all three dimensions without allowing one to substitute for or automatically determine the others.

## 5. Verification Outcome Taxonomy

**Five possible statuses with precise criteria:**

1. **`supported`** — The independently retrieved evidence explicitly confirms the claim. The evidence text contains the claim statement or directly substantiates it. Company-reported figures match the claimed values with the stated reporting period and unit.

2. **`partially_supported`** — The evidence partially confirms the claim but has limitations. Some aspects of the claim are supported while others are not, or the evidence supports a related but narrower statement.

3. **`contradicted`** — The independently retrieved evidence directly contradicts the claim. For example, one filing states "revenue increased" while the claim states "revenue decreased," or two specialist reports make incompatible claims with supporting evidence.

4. **`insufficient_evidence`** — The evidence cannot definitively support or contradict the claim. This includes cases where the evidence excerpt is too brief, the relevant section is not included in the filing, the accession number leads to a different filing, or the evidence excerpts exist but do not clearly address the claim.

5. **`unverifiable`** — The claim cannot be verified due to: missing source (no EvidenceReference), unavailable filing (HTTP error, rate limit, inaccessible document), insufficient provenance (no source_url, no accession_number + filing_type + filing_date), or the claim involves metrics or time periods not present in the available evidence. **Do not treat missing evidence as proof that the claim is false.**

**Design decision for `source_unavailable`/`source_not_found`:**
Represent as a verification failure reason under `unverifiable`, not as a separate status. This avoids implying that `unverifiable` means "the claim might be true but we can't check it." Instead, `unverifiable` means "we cannot evaluate the claim due to missing/ unretrievable evidence." This distinction is important for the experimental research metrics: `unverifiable` counts reflect retrieval/interoperability issues, not evidence-against claims.

## 6. Evidence Retrieval and Source Validation

### 6.1 Retrieval Workflow

For SEC EDGAR evidence, the verifier follows this workflow:

1. **Extract reference metadata** from `EvidenceReference`: `source_url`, `accession_number`, `filing_type`, `filing_date`, `filing_section`, `evidence_text`.
2. **Attempt source retrieval** using the existing `EdgarClient` and ingestion layer:
   - Construct SEC filing URL from accession number and filing type.
   - Fetch the filing document (or use cached/previously extracted text).
   - Extract the relevant section (item number) from the filing.
3. **Handle edge cases:**
   - **Missing source URLs:** Mark as `retrieval_failed`; outcome depends on whether evidence_support can be determined from `evidence_text` alone (per 6.1.5, `evidence_text` alone is NOT sufficient for independent location; mark as `unverifiable` if no locator fields are populated).
   - **Incomplete accession metadata:** If `accession_number` is present but `filing_type` or `filing_date` is missing, attempt URL construction with partial information; if retrieval fails, mark as `unverifiable`.
   - **Invalid accession numbers:** If the accession number cannot be normalized (per `_normalize_accession` in `models.py`), mark as `retrieval_failed` → `unverifiable`.
   - **Unavailable filings:** HTTP 404, 410, or other errors from SEC → mark as `retrieval_failed`; outcome = `unverifiable` (distinguish from evidence-support failure).
   - **HTTP errors and rate limits:** Respect rate limiting; on persistent errors, mark as `retrieval_failed` → `unverifiable`.
   - **Empty or malformed source documents:** If the filing is retrieved but contains no extractable text for the relevant section → mark as `retrieval_failed` → `unverifiable`.
   - **Evidence excerpts that cannot be matched to the original document:** If the `evidence_text` from the `EvidenceReference` cannot be located in the retrieved filing → mark as `evidence_mismatch`; outcome = `contradicted` if the filing says the opposite, `insufficient_evidence` if the excerpt exists but doesn't address the claim, or `unverifiable` if the match failure is uncertain.
   - **Evidence that exists but does not support the associated claim:** If the evidence is retrievable but does not substantiate the claim (e.g., filing discusses different metrics, different time periods, or different companies) → outcome = `insufficient_evidence` or `contradicted` depending on nature of mismatch.

### 6.2 Retrieval Failure vs. Evidence-Support Failure

**Crucial distinction:** The verifier must distinguish between:
- **Retrieval failure:** The source document could not be fetched (HTTP error, 404, rate limit, network disabled, inaccessible file). → Outcome: `unverifiable` with reason "retrieval_failed".
- **Evidence-support failure:** The source was successfully retrieved but does not support the claim (evidence text exists but doesn't address the claim, contradicts the claim, addresses different metrics/periods). → Outcome: `insufficient_evidence`, `contradicted`, or `partially_supported` depending on nature of mismatch.

**The verifier must not fabricate source locations or infer that a source was checked when retrieval did not occur.** If retrieval failed, the verification outcome must reflect that (typically `unverifiable`) and explicitly note the retrieval failure as a reason.

## 7. Claim Verification Methodology

### 7.1 Verification Pipeline

A structured pipeline for evaluating claims individually:

1. **Extract the synthesized claim** from `SynthesizedFinding.claim` (or from the top-level research question/context).
2. **Identify every original claim contributing to it** from the `SynthesizedFinding.original_claims` list and corresponding `EvidenceReference` objects.
3. **Resolve the corresponding EvidenceReferences** — verify that `original_specialist` and `original_claim` are populated (per Milestone 6.1.5); if not, the claim's lineage is incomplete and this is documented.
4. **Retrieve the original evidence independently** using `EvidenceRetriever` with the `EvidenceReference` metadata.
5. **Locate or validate the relevant passage** — find the evidence excerpt within the retrieved filing section, or determine that the excerpt is not present.
6. **Compare the evidence with the claim** — assess whether the evidence explicitly confirms, partially confirms, contradicts, or does not address the claim.
7. **Assign a typed verification outcome** from the taxonomy (supported/partially_supported/contradicted/insufficient_evidence/unverifiable).
8. **Record reasoning, evidence, and limitations** for each claim.
9. **Produce a structured verification report** entry for the claim.

### 7.2 Handling Specific Cases

| Case | Verification Approach |
|---|---|
| **One claim supported by multiple sources** | All contributing sources are evaluated; outcome = `supported` if all/majority support, `partially_supported` if some support and some don't, `contradicted` if any contradict. |
| **One synthesized claim combining multiple original claims** | Each original claim is verified individually; the synthesized claim's outcome is determined by the aggregate of its components (e.g., `supported` if all components are `supported`, `partially_supported` if some are, `contradicted` if any are contradicted). |
| **Contradictions between specialist reports** | Both claims are evaluated independently; outcome for each is recorded. If the synthesized claim combines incompatible claims, this is reflected in the verification outcome (likely `contradicted` or `insufficient_evidence`). |
| **Numerical financial claims** | Verify: metric name, value, currency/unit, reporting period, fiscal vs. calendar period, whether figure is reported/calculated/estimated. **Do not assume numerical verification is possible from a text excerpt alone** — require structured data or explicit figure statements in the filing. |
| **Claims involving time periods** | Verify that the claimed period matches the evidence's reporting period. If periods differ, assess whether the difference is expected (e.g., quarterly vs. annual) or constitutes a contradiction/insufficient evidence. |
| **Claims that are interpretations rather than reported facts** | Assess whether the evidence supports the interpretation or only the underlying reported fact. If only the underlying fact is supported, outcome may be `partially_supported` (fact supported, interpretation not assessed) or `insufficient_evidence` (interpretation unsupported). |
| **Claims based on company-reported information** | Company-reported statements are not automatically verified as accurate. The verifier assesses whether the filing actually contains the reported statement, not whether the statement is true. Outcome: `supported` (statement present in filing), `insufficient_evidence` (statement not found), or `contradicted` ( filing contains opposite statement). |
| **Claims with incomplete source provenance** | If `EvidenceReference` is missing `original_specialist` or `original_claim` (per 6.1.5 validation), or missing all source-locator fields, the claim's provenance is incomplete. Outcome: `unverifiable` with documented provenance gap. |
| **Claims whose original evidence is unavailable** | If retrieval fails (HTTP error, 404, rate limit, inaccessible document), outcome: `unverifiable` with "retrieval_failed" reason. If provenance is complete but evidence is excluded from the filing, outcome: `insufficient_evidence` or `unverifiable` depending on whether the exclusion is understood. |

### 7.3 Numerical Claim Verification

For numerical financial claims, the verifier should attempt to verify:

- **Metric name:** Is the claimed metric (e.g., "revenue", "net income", "EPS") present in the evidence?
- **Value:** Does the claimed value appear in the evidence?
- **Currency or unit:** Is the currency/unit specified and consistent?
- **Reporting period:** Does the evidence's reporting period match the claimed period?
- **Fiscal versus calendar period:** If the company uses a fiscal year, verify alignment with the claimed period.
- **Whether the figure is reported, calculated, or estimated:** Note this classification; "reported" carries more weight than "estimated".

**Critical constraint:** Do not assume numerical verification is possible from a text excerpt alone. If the filing only mentions "revenue grew" without stating a specific figure, the claim cannot be numerically verified — outcome = `insufficient_evidence` (for the numerical aspect) or `supported` (for the qualitative aspect that revenue growth is mentioned).

## 8. Data Models and Output Contract

### 8.1 Pydantic Models

#### `EvidenceVerification` — Per-Evidence Verification

```python
class EvidenceVerification(BaseModel):
    """Verification of a single evidence reference against its claim."""
    
    evidence_reference: EvidenceReference = Field(
        ...,
        description="The EvidenceReference object being verified, with original_specialist and original_claim",
    )
    claim_text: str = Field(
        ...,
        description="The original claim text from the EvidenceReference or synthesized finding",
    )
    verified_status: VerificationOutcome = Field(
        ...,
        description="The verification outcome: supported, partially_supported, contradicted, insufficient_evidence, unverifiable",
    )
    evidence_excerpt: Optional[str] = Field(
        default=None,
        description="The specific evidence passage from the retrieved filing that was assessed",
    )
    source_location: Optional[str] = Field(
        default=None,
        description="How the evidence was located (source_url, accession_number + filing_type + filing_date, or provenance_gap documentation)",
    )
    retrieval_status: Literal["retrieved", "retrieval_failed", "not_attempted"] = Field(
        default="not_attempted",
        description="Whether the evidence retrieval succeeded or failed",
    )
    retrieval_reason: Optional[str] = Field(
        default=None,
        description="Reason for retrieval failure if applicable (HTTP error, 404, rate limit, inaccessible, etc.)",
    )
    comparison_reasoning: str = Field(
        ...,
        description="Text explanation of how the evidence was compared to the claim and why the outcome was assigned",
    )
    limitations: str = Field(
        default="",
        description="Explicit limitations on this verification (e.g., excerpt too brief, period mismatch, only qualitative match possible)",
    )
    verified_at: constr(regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$") = Field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat(),
        description="ISO timestamp when this verification was performed",
    )
```

#### `VerificationIssue` — Per-Issue Tracking

```python
class VerificationIssue(BaseModel):
    """Tracks a specific verification issue or finding."""
    
    issue_id: str = Field(
        ...,
        description="Unique identifier for this verification issue",
    )
    claim_text: str = Field(
        ...,
        description="The claim being assessed",
    )
    issue_type: Literal["retrieval_failure", "provenance_gap", "evidence_mismatch", "period_mismatch", "metric_undefined", "insufficient_coverage"] = Field(
        ...,
        description="The type of issue encountered",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the issue",
    )
    severity: Literal["high", "medium", "low"] = Field(
        ...,
        description="Severity of the issue for the overall verification outcome",
    )
```

#### `ClaimVerification` — Per-Claim Verification

```python
class ClaimVerification(BaseModel):
    """Verification of a single synthesized claim against its original evidence."""
    
    synthesized_claim: str = Field(
        ...,
        description="The synthesized claim as it appears in the ResearchSynthesizerResult",
    )
    original_claim_references: list[str] = Field(
        ...,
        description="List of original claim texts from contributing specialist reports",
    )
    evidence_references: list[EvidenceReference] = Field(
        ...,
        description="EvidenceReference objects supporting this claim",
    )
    verification_status: VerificationOutcome = Field(
        ...,
        description="Overall verification status for this claim",
    )
    evidence_verifications: list[EvidenceVerification] = Field(
        default_factory=list,
        description="Per-evidence detailed verification entries",
    )
    verification_issues: list[VerificationIssue] = Field(
        default_factory=list,
        description="List of issues encountered during verification",
    )
    evidence_excerpt: Optional[str] = Field(
        default=None,
        description="Best evidence excerpt found supporting or refuting the claim",
    )
    overall_reasoning: str = Field(
        ...,
        description="Summary of the verification reasoning",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="LLM-assigned confidence (0.0 to 1.0), if justified; None if not justified",
    )
    verified_at: constr(regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$") = Field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat(),
        description="ISO timestamp when this claim verification was performed",
    )
    limitations: str = Field(
        default="",
        description="Overall limitations of this verification",
    )
```

#### `CitationVerificationResult` — Overall Result

```python
class CitationVerificationResult(BaseModel):
    """Overall result from the Citation Verifier."""
    
    company_ticker: str = Field(
        ...,
        description="Company ticker the verification relates to",
    )
    research_question: str = Field(
        ...,
        description="The research question being verified",
    )
    verification_completed: bool = Field(
        ...,
        description="Whether verification was completed for all claims",
    )
    all_claims_evaluated: bool = Field(
        ...,
        description="Whether every synthesised claim was evaluated",
    )
    sources_independently_retrieved: bool = Field(
        ...,
        description="Whether evidence sources were independently retrieved (not just referenced)",
    )
    claims: list[ClaimVerification] = Field(
        default_factory=list,
        description="Per-claim verification results",
    )
    overall_outcome: VerificationOutcome = Field(
        ...,
        description="Overall assessment: supported if all claims supported, contradicted if any contradicted, etc.",
    )
    sources_retrieved_successfully: int = Field(
        default=0,
        description="Count of evidence sources successfully retrieved",
    )
    sources_total: int = Field(
        default=0,
        description="Total number of evidence references attempted",
    )
    verification_issues: list[VerificationIssue] = Field(
        default_factory=list,
        description="List of all issues encountered across all claims",
    )
    overall_limitations: str = Field(
        default="",
        description="Overall limitations of the verification process",
    )
    verified_at: constr(regex=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$") = Field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat(),
        description="ISO timestamp when verification was completed",
    )
```

#### `VerificationOutcome` — Enumeration

```python
from enum import Enum

class VerificationOutcome(str, Enum):
    """Typed verification outcome taxonomy."""
    
    supported = "supported"
    partially_supported = "partially_supported"
    contradicted = "contradicted"
    insufficient_evidence = "insufficient_evidence"
    unverifiable = "unverifiable"
```

### 8.2 How Milestone 6.1 Semantic Fields Remain Distinct

The Citation Verifier's outputs are explicitly independent from the five Milestone 6.1 semantic fields:

| Milestone 6.1 Field | What It Measures | Citation Verifier Relation |
|---|---|---|
| `evidence_preserved` | Whether original claims and provenance are traceable via `EvidenceReference(original_specialist, original_claim)` | The verifier may find `evidence_preserved=True` (complete lineage) but `verification_status = insufficient_evidence` (evidence doesn't support the claim) or `unverifiable` (source unretrievable). These are separate concerns. |
| `input_compatible` | Whether provided reports are suitable for synthesis (both non-None, matching tickers, compatible scopes) | The verifier operates on already-synthesized output; `input_compatibility` is irrelevant to verification outcomes. |
| `synthesis_complete` | Whether synthesized findings adequately address the research question | The verifier assesses claim-level support; `synthesis_complete` is a higher-level concern. A synthesis can be `complete` yet individual claims may be `contradicted` or `insufficient_evidence`. |
| `source_provenance_present` | Whether at least one source-locator field is populated across EvidenceReference entries | The verifier may find `source_provenance_present=True` but still assign `unverifiable` if retrieval fails, or `supported` if the retrievable evidence confirms the claim. |
| `source_provenance_complete` | Whether enough source-location information exists to independently locate evidence | The verifier may find `source_provenance_complete=True` (e.g., source_url populated) but still assign `unverifiable` if the retrieved filing doesn't contain the claimed evidence, or `supported` if it does. |

**Explicit rule:** The Citation Verifier must NOT retroactively change any of the five Milestone 6.1 semantic fields. It reports its own verification outcomes alongside (not atop) those fields.

## 9. LLM and Deterministic Verification

### 9.1 Prefer Deterministic Checks

The following must be deterministic (LLM-assisted verification is supplemental, not primary):

- **URL validation:** Constructing and validating SEC filing URLs from accession numbers and filing types must follow deterministic rules (per `_normalize_accession` in `models.py`).
- **Accession number normalization:** The `_normalize_accession` function must always produce the same output for the same input.
- **Filing metadata matching:** Matching `filing_type`, `filing_date`, `accession_number` combinations must follow deterministic patterns.
- **Evidence retrieval:** Downloading and reading a filing document is a deterministic operation (given the same URL and same document content).
- **Exact excerpt matching:** If the `evidence_text` from an `EvidenceReference` can be located as a substring in the retrieved filing text, this is deterministic.
- **Numerical consistency checks** where structured data is available (e.g., if the filing includes XBRL tags or structured data sections with explicit figures).
- **Required-field validation:** Validating that `EvidenceReference` has `original_specialist` and `original_claim` populated is a deterministic Pydantic check.

### 9.2 LLM-Assisted Verification

An LLM may assist with **semantic evidence-to-claim comparison** — assessing whether a natural-language evidence excerpt supports, contradicts, or does not address a claim. However:

- The LLM must not be the sole source of truth.
- Deterministic checks must run first; LLM results are supplemental.
- If deterministic checks already determine the outcome (e.g., excerpt found via exact match, numerical figure retrieved), the LLM should not override them.
- The LLM must operate through the existing provider-agnostic `LLMInferenceClient` protocol (`ChatCompletionRequest` → `ChatCompletionResponse`), not provider-specific SDKs.
- **Malformed LLM outputs:** If the LLM returns unexpected format, the verifier should fall back to the last deterministic outcome and record "LLM_output_malformed" as a verification issue.
- **Low-confidence judgments:** If the LLM's confidence is below a threshold (e.g., < 0.6), record as "low_confidence" verification issue and fall back to deterministic outcome.
- **Disagreement between deterministic and LLM checks:** Prioritize the deterministic outcome; record the LLM's assessment as a "disagreement" verification issue. The final outcome remains the deterministic one.

### 9.3 Returning `unverifiable` Without LLM

The verifier should be able to return `unverifiable` without invoking an LLM in these cases:

- No `EvidenceReference` exists (missing provenance).
- Required locator fields (`source_url`, `accession_number` + `filing_type` + `filing_date`) are all absent.
- SEC filing retrieval fails (HTTP error, 404, rate limit, network disabled).
- Evidence excerpt cannot be matched to the retrieved document and no deterministic basis for assessment exists.

In these cases, the verifier assigns `unverifiable` with a `retrieval_status = "retrieval_failed"` or `retrieval_status = "provenance_gap"` and records the specific reason in `verification_issues`. No LLM call is necessary.

## 10. Integration Strategy

### 10.1 Staged Integration

**Stage 1 — Standalone verifier on ResearchSynthesizerResult:**
- The `CitationVerifier` takes a `ResearchSynthesizerResult` as input and produces a `CitationVerificationResult`.
- No orchestrator changes required.
- Can be invoked as: `CitationVerifier.verify(synthesizer_result)`.
- Used for evaluation and quality-control workflows.

**Stage 2 — Orchestrator integration:**
- The Research Orchestrator optionally invokes the Citation Verifier after producing an `OrchestrationResult`.
- Verification outcomes are attached to the `OrchestrationResult` as an annotation field.
- Does NOT modify the `OrchestrationResult.tasks` or `OrchestrationResult.overall_status`; verification is purely additive/assessive.

**Stage 3 — End-to-end research workflow:**
- Full pipeline: Research Orchestrator → Specialist Agents → Research Synthesizer → Citation Verifier → Final annotated report.
- The final report includes the original synthesis plus claim-level verification statuses and unresolved issues.
- Used for research evaluation and iterative improvement.

**Stage 4 — Final report with claim-level verification:**
- Produces a output document that includes:
  - The synthesized research report (unchanged).
  - A claim-level verification appendix with `ClaimVerification` entries for each synthesized claim.
  - Summary metrics: percentage of claims supported, contradicted, partially supported, insufficient evidence, unverifiable.
  - Source retrieval success rate.
  - All unresolved issues and limitations.

### 10.2 What the Verifier Should NOT Do

- **NOT rewrite the synthesized research report.** The verifier annotates and assesses; the synthesis stands as-is.
- **NOT establish factual accuracy.** The verifier assesses evidence-support, not truth. A `supported` outcome means the evidence is present in the filing, not that the claim is true.
- **NOT automatically elevate agent permissions.** The verifier respects network authorization boundaries; if `allow_network=False`, no HTTP requests are made, and outcomes reflect `unverifiable` due to provenance gaps.
- **NOT collapse the five Milestone 6.1 semantic fields.** Each field retains its independent meaning.

### 10.3 Integration Points

| Integration Point | Input | Output | Modifies |
|---|---|---|---|
| `CitationVerifier.verify(result)` | `ResearchSynthesizerResult` | `CitationVerificationResult` | None (read-only) |
| Orchestrator post-processing | `OrchestrationResult` + `CitationVerificationResult` | Annotated `OrchestrationResult` | Adds `verification_annotation` field (optional) |
| End-to-end workflow | Full pipeline inputs | Final report with verification appendix | Generates appendices; does not alter core outputs |

## 11. Experimental Research Considerations

The Citation Verifier should generate evaluation data for FRIS's central research question: "Can coordinated teams of specialized AI agents produce more accurate, comprehensive and efficient financial research than a single AI researcher?"

**Recommended metrics:**

| Metric | Definition |
|---|---|
| **Claim verification rate** | Percentage of synthesized claims that receive a definitive outcome (supported, contradicted, or insufficient_evidence), excluding `unverifiable` due to retrieval failures. |
| **Support rate** | Percentage of claims with `verification_status = supported`. |
| **Contradiction rate** | Percentage of claims with `verification_status = contradicted`. |
| **Partial support rate** | Percentage of claims with `verification_status = partially_supported`. |
| **Unverifiable rate** | Percentage of claims with `verification_status = unverifiable`. Breakdown: retrieval_failed vs. provenance_gap. |
| **Source retrieval success rate** | Percentage of `EvidenceReference` objects for which the SEC filing was successfully retrieved. |
| **Citation precision** | Of claims with `supported` outcome, percentage where the evidence excerpt can be explicitly cited (not just "the evidence supports the claim"). |
| **Verification latency** | Average time from `CitationVerifier.verify()` invocation to `CitationVerificationResult` production. |
| **Token and API cost** | Total tokens consumed (if LLM-assisted) or compute time (if deterministic-only). |
| **False-positive rate** | Of claims with `supported` outcome, percentage where ground truth (manual review) shows the evidence does not actually support the claim. Requires manually labeled ground truth. |
| **False-negative rate** | Of claims with `insufficient_evidence` or `unverifiable` outcome, percentage where ground truth shows the claim is actually supported by the evidence. Requires ground truth. |

**Evaluating verifier quality against ground truth:**

- Create a manually labeled dataset of synthesized claims with ground truth verification outcomes.
- Compare the Citation Verifier's outcomes against the ground truth.
- Calculate precision/recall for each outcome type.
- Specifically evaluate: does `supported` correctly identify claims where evidence is present in the filing? does `unverifiable` correctly reflect retrieval/provenance issues rather than evidence-against? does the verifier distinguish `contradicted` from `insufficient_evidence` appropriately?

**Important:** Do not claim that agent agreement establishes factual accuracy. Agent agreement (both specialists making the same claim) is a separate concern from evidence support. The verifier must assess each claim against its evidence independently.

## 12. Deliverables

Four documentation files must be created:

1. **`docs/milestone6_2_citation_verifier_architecture.md`** — System architecture, component responsibilities, data flow, independence requirements, integration design.

2. **`docs/milestone6_2_citation_verifier_schema.md`** — Proposed Pydantic models, field definitions, enumerations, validation rules, output contracts.

3. **`docs/milestone6_2_citation_verifier_test_plan.md`** — Test scenarios, synthetic fixtures, expected outcomes, network authorization tests, failure handling, evaluation metrics.

4. **`docs/milestone6_2_citation_verifier_implementation_plan.md`** — Ordered implementation phases, existing modules to modify, new modules to create, dependencies (minimal, prefer reuse), test gates, acceptance criteria.

## 13. Quality Requirements

- ✅ Inspect the current repository before designing (completed — reviewed existing models, EDGAR client, LLM protocol, orchestrator).
- ✅ Reuse existing interfaces and models where appropriate (EdgarClient, EvidenceReference, ResearchSynthesizerResult, LLM protocol).
- ✅ Avoid unnecessary abstractions (verify against existing patterns before adding new ones).
- ✅ Avoid duplicating SEC retrieval infrastructure (reuse existing `EdgarClient` and `extract_sections_from_filing`).
- ✅ Keep implementation provider-agnostic (use existing `LLMInferenceClient` protocol; no provider-specific SDKs).
- ✅ Preserve evidence provenance (all `EvidenceReference` objects and their fields remain intact; verifier reads, does not modify).
- ✅ Make verification outcomes auditable and reproducible (deterministic checks, recorded reasoning, timestamps, issue tracking).
- ✅ Do not overstate what the verifier can establish (explicit about `unverifiable`, `insufficient_evidence`, distinctions between retrieval failure and evidence-support failure).
- ✅ Keep deterministic checks separate from semantic judgments (deterministic first, LLM supplemental).
- ✅ Make partial failures explicit (`partially_supported`, `insufficient_evidence`, issues list).
- ✅ Avoid adding unnecessary dependencies (prefer reuse; new dependencies only if absolutely required and justified).

## 14. Final Response

**After completing the design documentation, report:**
1. Files created.
2. Existing modules inspected.
3. Recommended architecture.
4. Important technical decisions.
5. Risks and limitations.
6. Proposed implementation sequence.
7. Exact tests and acceptance criteria.
8. Confirmation that no source code or dependencies were modified.

**Do not implement Milestone 6.2 yet. Stop after the four design documents are complete and ready for review.**

---

**Design philosophy:** The Citation Verifier is an independent, audit quality-control layer that evaluates synthesized claims against original evidence without substituting for or modifying the Synthesizer's output. It preserves the five Milestone 6.1 semantic fields as distinct concerns, provides a typed verification outcome taxonomy, and uses deterministic checks wherever possible with LLM assistance as supplemental. The design reuses existing FRIS infrastructure (EdgarClient, EvidenceReference, LLM protocol) and avoids unnecessary dependencies. The verifier annotates and assesses without rewriting research reports, making it suitable for both operational quality control and experimental research evaluation metrics.