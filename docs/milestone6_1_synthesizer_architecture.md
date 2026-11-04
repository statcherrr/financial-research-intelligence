# FRIS — Milestone 6.1.5: Research Synthesizer Architecture Semantic Audit (Final Corrections)

## 1. Correct evidence_preserved Semantics

**Definitive rule:** `evidence_preserved: bool` is `True` if and only if every original claim contributing to every `SynthesizedFinding` with a non-`None` `claim` has a corresponding `EvidenceReference` with both `original_specialist` and `original_claim` populated. `evidence_preserved: bool` is `False` when any contributing original claim lacks its corresponding complete claim-lineage reference.

**Explicit limitations must document missing lineage, but documentation does not restore it.** An `explicit_limitations` entry noting "EvidenceReference missing original_specialist" correctly records the gap but does not make `evidence_preserved=True`.

**A traceable but unsupported claim remains preserved.** `evidence_preserved=True` when claim lineage is complete (`original_specialist` + `original_claim` populated), even when `evidence_status ≠ supported_by_reference`. Evidence support and claim preservation are separate concerns — the synthesizer preserves the claim's traceability; it does not certify the claim's truth or completeness of evidence.

**What `evidence_preserved=False` does NOT mean:** The claim is `false`. It means the claim-lineage reference is incomplete; the provenance trail from synthesized finding back to source specialist is broken for at least one contributing original claim.

## 2. Require Complete Lineage for Every Contributing Original Claim

A synthesized finding combining multiple original claims must retain a corresponding `EvidenceReference` for **every** original claim. A finding must not receive `evidence_preserved=True` merely because one of several contributing claims has a valid reference.

**Key requirements:**
- If a `SynthesizedFinding` integrates claims from both specialists, each claim must have its own `EvidenceReference` with `original_specialist` + `original_claim` populated.
- Contradictions must preserve independent references for both sides — each `SynthesisContradiction` must have `fundamentals_evidence_reference` and `industry_evidence_reference` with complete claim-lineage fields.
- A finding with `len(contributing_claims) > 1` where only one claim has a valid `EvidenceReference` receives `evidence_preserved=False` for the finding as a whole.

**SynthesizedFinding documentation updated:** The `evidence_preserved` status is evaluated at the finding level, considering all contributing original claims. A finding is `evidence_preserved=True` only when **all** contributing claims have complete lineage.

**ResearchSynthesizerResult semantics updated:** `result.evidence_preserved` is `True` only when every `SynthesizedFinding` with a non-`None` `claim` has all contributing original claims traced via `EvidenceReference(original_specialist, original_claim)`. A finding with partially complete lineage contributes `evidence_preserved=False` to the overall result.

**Architecture definitions updated:** The top-level definition of `evidence_preserved` in the architecture document reflects this stricter rule — `True` only when complete claim-lineage references exist for every contributing original claim.

**Test assertions and fixtures updated:** Test code asserts `evidence_preserved` per the stricter definition. Fixtures in provenance-test scenarios must provide complete `EvidenceReference` chains for all contributing claims, or explicitly test the `False` case with missing lineage.

## 3. Clarify Source Provenance Completeness

Separate the two distinct concepts:

### `source_provenance_present: bool`
- `True` if at least one source-related field is populated (`evidence_text`, `source_url`, `accession_number`, `filing_type`, `filing_date`, `filing_section`).
- `False` if all source-locator fields are `None`/empty across all `EvidenceReference` entries.

### `source_provenance_complete: bool`
- `True` if enough source-location information exists to independently locate and inspect the underlying evidence.
- For SEC filings: `source_url` populated **or** (`accession_number` + `filing_type` + `filing_date` all populated) is considered `source_provenance_complete`, because this combination allows independent retrieval.
- `False` if insufficient source-location information exists for independent verification.

**Do not consider `evidence_text` alone sufficient for independently locating a source** unless the design explicitly explains how a reader can verify the claim using only that text snippet. `evidence_text` is a supporting excerpt, not a locator.

**Correct every occurrence of `solution_provenance_complete` to `source_provenance_complete`.** This was a naming error in the prior version.

**Keep source provenance independent of claim-lineage preservation.** `evidence_preserved` can be `True` (complete claim lineage) even when `source_provenance_complete=False` (no independently locatable source). Conversely, `source_provenance_complete=True` does not guarantee `evidence_preserved=True` if claim lineage is incomplete.

## 4. Complete the ResearchSynthesizerResult Schema

The actual schema must expose all three required semantic fields:

- `evidence_preserved: bool` — `True` when every original claim contributing to every synthesized finding with a non-None claim has a corresponding EvidenceReference with both `original_specialist` and `original_claim` populated.
- `input_compatible: bool` — `True` when both reports are non-None with matching tickers and compatible research-question scope.
- `synthesis_complete: bool` — `True` when synthesized findings, agreements, contradictions, and research gaps together provide sufficient coverage of the research_question scope.

**Specify `source_provenance_present` and `source_provenance_complete` as explicit model fields:**

```python
source_provenance_present: bool = Field(
    ...,
    description="Whether at least one source-locator field is populated across all EvidenceReference entries. True if any EvidenceReference has at least one of evidence_text, source_url, accession_number, filing_type, filing_date, or filing_section set.",
)
source_provenance_complete: bool = Field(
    ...,
    description="Whether enough source-location information exists to independently locate and inspect the underlying evidence. For SEC filings: source_url populated, or (accession_number + filing_type + filing_date all populated). Does NOT determine evidence_preserved; independent from claim-lineage preservation.",
)
```

**For each field, document its exact computation contract:**

- `evidence_preserved`: `True` iff ∀ `SynthesizedFinding` with `claim ≠ None`: ∀ contributing original claim, ∃ `EvidenceReference` with `original_specialist` populated ∧ `original_claim` populated. `False` otherwise.
- `input_compatible`: `True` iff both `fundamentals_report` and `industry_report` are non-None ∧ `company_ticker` values match `SynthesisInput.company_ticker` ∧ research-question scopes are compatible. `False` otherwise.
- `synthesis_complete`: `True` iff synthesized findings, agreements, contradictions, and research gaps together provide sufficient coverage of `research_question` scope considering which reports were provided. `False` when `research_gaps` document genuine evidence deficits or both reports are None.
- `source_provenance_present`: `True` iff ∃ `EvidenceReference` with ∃ field ∈ {evidence_text, source_url, accession_number, filing_type, filing_date, filing_section} populated. `False` iff all such fields are None/empty across all entries.
- `source_provenance_complete`: `True` iff (∃ `EvidenceReference` with `source_url` populated) ∨ (∃ `EvidenceReference` with `accession_number` populated ∧ `filing_type` populated ∧ `filing_date` populated). `False` otherwise.

**The test plan must not assert fields that the result schema does not expose.** Test code asserts only the five fields: `evidence_preserved`, `input_compatible`, `synthesis_complete`, `source_provenance_present`, `source_provenance_complete`.

## 5. Correct Scenarios 11C and 11D

**Because `original_specialist` and `original_claim` are required Pydantic fields, ordinary `EvidenceReference` construction without either field must fail validation.** Pydantic `ValidationError` is raised if `EvidenceReference(original_claim="...")` omits `original_specialist`, or if `EvidenceReference(original_specialist="fundamentals")` omits `original_claim`.

**Separate:**
- **Pydantic validation tests for missing required fields:** These tests assert that `EvidenceReference(original_claim="...")` or `EvidenceReference(original_specialist="...")` raises `ValidationError`. These are not "valid EvidenceReference instances" — they are expected validation failures.
- **Optional defensive-handling tests using deliberately invalid internal objects,** if justified: Tests that the synthesizer gracefully handles objects that somehow bypass Pydantic validation (e.g., via `.model_validate()` with relaxed settings). These are separate from normal-operation tests and are explicitly labeled as validation-boundary tests.

**Do not represent invalid objects as normally valid EvidenceReference instances.** The test plan asserts that valid `EvidenceReference` objects always have both `original_specialist` and `original_claim` populated. Any test representing an `EvidenceReference` missing these fields is explicitly a validation-boundary test, not a normal-operation test.

## 6. Reconcile Scenario Counts

Starting from the original 15 scenarios and applying Milestone 6.1.5 corrections:

- **Splitting Scenario 3** adds one (3A + 3B = 2 scenarios instead of 1).
- **Splitting Scenario 11 into four cases** adds three (11A + 11B + 11C + 11D = 4 scenarios instead of 1).
- **Adding Scenario 16** (Both reports present with full provenance as a distinct end-to-end test) adds one.

**However, scenario 11C and 11D are validation tests (EvidenceReference construction without required fields raises ValidationError). Scenarios 17–20 in the prior version duplicated 11C/11D; these duplicates are removed in the reconciled inventory.**

**Therefore:**
- **16 behavioral scenarios** (scenarios 1–14, 16 — these specify all five field values and exercise the synthesizer).
- **5 validation scenarios** (11C, 11D — EvidenceReference construction validation; 15, 19, 20 — SynthesisInput construction validation; note: 15, 19, 20 all test SynthesisInput construction errors but with different invalid inputs; they are kept separate as they test different input-field combinations).
- **21 total scenarios** if validation is counted (16 behavioral + 5 validation), or 16 if only behavioral scenarios are counted.

**Reconcile all scenario headings, test names, matrices, and summaries:**
- Scenario 3 is replaced by 3A and 3B (two headings).
- Scenario 11 is replaced by 11A, 11B, 11C, 11D (four headings; 11C and 11D are validation tests).
- Scenario 16 is added as a new end-to-end integration test.
- The scenario matrix has 16 behavioral rows + 5 validation rows.
- Test names update to reflect the new numbering and classifications.

## 7. Additional Consistency Checks

Verify that:

- **Every field referenced in the architecture exists in the schema or has a documented derivation.** All five fields (`evidence_preserved`, `input_compatible`, `synthesis_complete`, `source_provenance_present`, `source_provenance_complete`) are explicit model fields in `ResearchSynthesizerResult` with documented computation contracts.

- **Every test fixture uses valid ResearchReport and EvidenceReference structures** unless explicitly testing validation or malformed-object handling. Fixtures in behavioral test scenarios always provide complete `EvidenceReference` chains where `evidence_preserved=True` is expected; validation-boundary fixtures explicitly omit required fields.

- **Every synthesized finding preserves all contributing original claims.** A `SynthesizedFinding` with claims from both specialists has `EvidenceReference` entries for each contributing claim, each with `original_specialist` + `original_claim` populated.

- **Unsupported claims are retained without being labeled false.** `evidence_status ≠ supported_by_reference` does not cause `evidence_preserved=False`. The two concerns are separate.

- **Claim lineage and independently locatable source provenance remain separate.** `evidence_preserved=True` requires complete claim lineage; `source_provenance_complete` assesses independently locatable source information. One does not substitute for or guarantee the other.

- **The five semantic fields are independently evaluated.** `evidence_preserved`, `input_compatible`, `synthesis_complete`, `source_provenance_present`, `source_provenance_complete` each have their own definition and can vary independently across scenarios.

- **Existing 68 tests remain unchanged and pass.** No source-code modifications were required; only the three documentation files were revised.

## Correction Report — Milestone 6.1.5 Semantic Consistency

| # | Issue | Resolution |
|---|---------|-----------|
| 1 | `evidence_preserved` semantics were too lenient — documenting a provenance gap could make it `True` | Revised to definitive rule: `True` only when every contributing original claim has complete `EvidenceReference(original_specialist, original_claim)`. Documentation of gaps does not restore lineage. |
| 2 | Complete lineage not required for every contributing original claim | Revised: synthesized findings combining multiple claims must retain EvidenceReference for every claim. A finding with only one valid reference among many receives `evidence_preserved=False`. Contradictions must preserve independent references for both sides. |
| 3 | `source_provenance_complete` was not clearly separated from `source_provenance_present` | Clarified: `source_provenance_present` = at least one source-locator field populated. `source_provenance_complete` = enough information to independently locate evidence (e.g., `source_url` for SEC filings, or `accession_number` + `filing_type` + `filing_date`). `evidence_text` alone is not sufficient for independent location. Corrected all occurrences of `solution_provenance_complete` to `source_provenance_complete`. |
| 4 | `ResearchSynthesizerResult` schema was incomplete — missing `source_provenance_present` and `source_provenance_complete` | Added both fields as explicit model fields with documented computation contracts. The three required semantic fields (`evidence_preserved`, `input_compatible`, `synthesis_complete`) are joined by the two source provenance fields. Test plan assertions align with exposed fields. |
| 5 | Scenarios 11C/11D and 17–20 had duplicate validation test descriptions | Corrected: 11C and 11D are the authoritative EvidenceReference validation tests. Scenarios 17–20 that duplicated them are removed. Scenarios 15, 19, 20 test SynthesisInput validation with different invalid inputs and are kept as separate validation scenarios. |
| 6 | Scenario count was incorrect | Reconciled: 15 original → split Scenario 3 adds 1 → split Scenario 11 into four adds 3 → add Scenario 16 adds 1 → 19 pre-correction → remove duplicate validation scenarios (17–20 overlap with 11C/11D) → 16 behavioral + 5 validation = 21 total, or 16 behavioral if validation not counted. All scenario headings, test names, matrices, and summaries updated. |

## 8. No Implementation Changes

- No source code was modified.
- No dependencies were added or removed.
- Only the three documentation files were revised to clarify the five independent semantic fields, add stricter `evidence_preserved` definition, clarify claim lineage vs. source provenance, correct scenario counts, and add validation test structure.
- All 68 existing tests continue to pass without modification.

## Review and Approval

These revised documents reflect the final semantic corrections for Milestone 6.1.5. The definitions of `evidence_preserved`, `input_compatible`, `synthesis_complete`, `source_provenance_present`, and `source_provenance_complete` are now precise, independently specifiable, and self-consistent across architecture, schema, and test plan. No source code or dependencies were changed. All 68 existing tests continue to pass. Ready for final sign-off.