# FRIS — Milestone 6.2: Citation Verifier Implementation Plan

## 1. Implementation Phases (Ordered)

### Phase 1: Repository Inspection and Model Reuse (Completed)
**Objective:** Inspect existing FRIS repository structure, models, and interfaces before designing.
**Completed activities:**
- Reviewed `src/fris/data/models.py` — `EvidenceReference`, `FilingRecord`, `CompanyCIK`, `ExtractedFiling`, `ExtractedSection`
- Reviewed `src/fris/llms/protocol.py` — `ChatCompletionRequest`, `ChatCompletionResponse`, `InferenceClient` abstract base
- Reviewed `src/fris/llms/mock.py` — `MockClient` for testing
- Reviewed `src/fris/data/edgar.py` — `EdgarClient`, `EdgarClientConfig`, error classes
- Reviewed `src/fris/data/edgar_ingestion.py` — `extract_sections_from_filing`, section extraction logic
- Reviewed `src/fris/orchestration/orchestrator.py` — `ResearchOrchestrator`, `TaskResult`, `OrchestrationResult`
- Reviewed `docs/milestone6_1_*` — `EvidenceReference`, `SynthesizedFinding`, `ResearchSynthesizerResult`, `VerificationOutcome` taxonomy
- Verified existing test structure and network authorization boundaries

**Outcome:** Design is grounded in existing infrastructure; no need to invent new models from scratch. All Citation Verifier models reuse or extend existing ones.

### Phase 2: Core CitationVerifier Implementation
**Objective:** Implement the `CitationVerifier.verify()` method as a read-only function that takes a `ResearchSynthesizerResult` and produces a `CitationVerificationResult`.

**Key tasks:**
1. **Create `src/fris/verification/citation_verifier.py`** — Main verifier module containing:
   - `CitationVerifier` class (or standalone functions) with `verify(synthesizer_result, allow_network=True)` method.
   - Verification pipeline implementation (extract claim → identify original claims → resolve EvidenceReferences → retrieve evidence → compare → assign outcome).
   - Deterministic evidence retrieval using existing `EdgarClient` and `extract_sections_from_filing`.
   - `VerificationOutcome` enum definition.
   - `EvidenceVerification`, `ClaimVerification`, `CitationVerificationResult`, `VerificationIssue` model construction.

2. **Implement evidence retrieval workflow:**
   - Use existing `EdgarClient` for HTTP transport.
   - Construct SEC filing URLs from `EvidenceReference.accession_number`, `filing_type`, `filing_date`.
   - Handle URL construction edge cases (per `_normalize_accession` in `models.py`).
   - Handle HTTP errors (404, 429, 503), rate limits, timeouts.
   - Distinguish retrieval failures from evidence-support failures.

3. **Implement claim comparison logic:**
   - Exact excerpt matching (substring search in retrieved filing text).
   - Numerical claim verification (metric name, value, currency/unit, reporting period, fiscal vs. calendar, reported/calculated/estimated).
   - Time period assessment (claim period vs. evidence reporting period).
   - Interpretation vs. reported fact distinction.
   - Company-reported information assessment (presence in filing, not truth verification).

4. **Implement outcome taxonomy assignment:**
   - `supported`: evidence explicitly confirms claim.
   - `partially_supported`: evidence partially confirms (close numerical match, compatible but distinct considerations).
   - `contradicted`: evidence directly contradicts claim.
   - `insufficient_evidence`: evidence cannot definitively support or contradict.
   - `unverifiable`: claim cannot be evaluated (missing source, retrieval failed, insufficient provenance).

5. **Implement read-only guarantee:**
   - `verify()` must not modify `ResearchSynthesizerResult` or any nested objects.
   - Must not modify any `EvidenceReference` objects.
   - Must not persist any data.
   - Must not make side effects.

6. **Implement network authorization respect:**
   - `allow_network=True`: enable httpx client transport; attempt retrieval.
   - `allow_network=False`: skip all HTTP transport; set `retrieval_status = "not_attempted"`; outcomes for unretrievable claims = `unverifiable`.

7. **Implement issue tracking:**
   - Populate `verification_issues` list with typed `VerificationIssue` entries for each encountered issue (retrieval failure, provenance gap, evidence mismatch, period mismatch, numerical mismatch, LLM malformed, low confidence, etc.).

### Phase 3: Schema and Model Extensions
**Objective:** Ensure all required Pydantic models are properly defined and validated.

**Key tasks:**
1. **Add models to `src/fris/verification/models.py`** (or appropriate location):
   - `VerificationOutcome` enum.
   - `EvidenceVerification` model.
   - `VerificationIssue` model.
   - `ClaimVerification` model.
   - `CitationVerificationResult` model.

2. **Ensure validation rules are enforced:**
   - `EvidenceReference` construction without `original_specialist` or `original_claim` raises `ValidationError` (per Milestone 6.1.5).
   - `ClaimVerification` with `evidence_references` entries missing required fields raises `ValidationError`.
   - `CitationVerificationResult` validation cross-field constraints.
   - `confidence` must be `None` unless `verification_status = VerificationOutcome.supported`.

3. **Add `source_provenance_present` and `source_provenance_complete` computation:**
   - If model doesn't include these as explicit fields, add computed properties or ensure they're available from the reused `EvidenceReference` model.
   - Per Milestone 6.1.5: `source_provenance_present` = `source_url` populated ∨ (`accession_number` ∧ `filing_type` ∧ `filing_date` all populated).
   - `source_provenance_complete` = same as `source_provenance_present` (can be the same definition; if different, document the distinction).

### Phase 4: Test Infrastructure Setup
**Objective:** Set up test fixtures, mock transports, and test scenarios.

**Key tasks:**
1. **Create `tests/test_verification/` directory** with:
   - `__init__.py`
   - `test_citation_verifier.py` — Main test file with all 21 scenarios.
   - `fixtures.py` — Synthetic fixtures (ResearchReport, EvidenceReference, SynthesizedFinding, ResearchSynthesizerResult).

2. **Create `httpx.MockTransport` fixtures** for SEC filing mock responses:
   - Successful filing retrieval with extractable sections.
   - HTTP 404 responses.
   - HTTP 503 responses (rate limit/unavailable).
   - Empty filing documents.
   - Malformed filing HTML.
   - Numerical figures in filing text.

3. **Implement test scenarios** per the test plan:
   - Scenarios 1–16 (behavioral): each exercises specific input fixture and verifies expected output field values.
   - Scenarios 17–21 (validation): each asserts `ValidationError` is raised.

4. **Implement network authorization tests:**
   - `allow_network=True` with MockTransport.
   - `allow_network=False` should prevent all HTTP attempts and produce `unverifiable` outcomes.

5. **Implement deterministic behavior tests:**
   - Same `ResearchSynthesizerResult` invoked 3+ times with `allow_network=False`.
   - Verify identical `CitationVerificationResult` output (same `verification_status` per claim, same `overall_outcome`, same sorted `verification_issues`).

### Phase 5: Integration and Evaluation
**Objective:** Integrate the Citation Verifier into the existing workflow and generate evaluation data.

**Key tasks:**
1. **Integration with Research Orchestrator:**
   - Optional post-processing step after `OrchestrationResult` production.
   - Attach `CitationVerificationResult` as an annotation field on `OrchestrationResult` (e.g., `verification_annotation`).
   - Do NOT modify `OrchestrationResult.tasks` or `OrchestrationResult.overall_status`.

2. **End-to-end workflow:**
   - Research Orchestrator → Specialist Agents → Research Synthesizer → Citation Verifier → Final annotated report.
   - The final output includes the original synthesis plus the verification appendix.

3. **Evaluation metrics generation:**
   - From test runs, compute the recommended metrics (claim verification rate, support rate, contradiction rate, partial support rate, unverifiable rate, source retrieval success rate, citation precision, verification latency).
   - Generate a summary report from test suite execution.

4. **Acceptance criteria verification:**
   - Run all 21 test scenarios; all must pass.
   - Verify no retroactive modification of Milestone 6.1 fields.
   - Verify read-only invocation.
   - Verify network boundary respect.
   - Verify retrieval failure vs. evidence-support failure distinction.

### Phase 6: Documentation and Final Sign-off
**Objective:** Produce final documentation and confirm no source code modifications beyond the new implementation.

**Key tasks:**
1. **Verify all four documentation files are complete and self-consistent:**
   - `docs/milestone6_2_citation_verifier_architecture.md`
   - `docs/milestone6_2_citation_verifier_schema.md`
   - `docs/milestone6_2_citation_verifier_test_plan.md`
   - `docs/milestone6_2_citation_verifier_implementation_plan.md`

2. **Run existing test suite to confirm no regressions:**
   - `python -m pytest --collect-only -q`
   - `python -m pytest -q`
   - `python -m ruff check .`
   - `python -m ruff format --check .`
   - `python -m pip check`

3. **Produce final verification report:**
   - Files created.
   - Existing modules inspected.
   - Recommended architecture.
   - Important technical decisions.
   - Risks and limitations.
   - Proposed implementation sequence.
   - Exact tests and acceptance criteria.
   - Confirmation that no source code or dependencies were modified (only new files added).

## 2. Existing Modules Inspected

### 2.1 `src/fris/data/models.py`
- `EvidenceReference` — reused directly; `original_specialist` and `original_claim` are required; other fields optional.
- `_normalize_accession()` — deterministic accession number normalization; used for URL construction.
- `FilingRecord`, `CompanyCIK`, `CompanyLookupResult`, `CIKQuery`, `CIKResult` — reused for data models.
- `EXTRACTION_ITEM_MAP` — section item number to title mapping for EDGAR ingestion.

### 2.2 `src/fris/llms/protocol.py`
- `ChatCompletionRequest` — provider-agnostic LLM request model; includes `model` field (currently hardcoded to "claude-sonnet-4-20250514" per Milestone 6.1 audit, but the protocol itself is agnostic).
- `ChatCompletionResponse` — LLM response model.
- `InferenceClient` — abstract base class for LLM clients; `achat()` method.
- `MockClient` (from `llms/mock.py`) — testing-only client; does NOT make real HTTP requests.

### 2.3 `src/fris/llms/mock.py`
- `MockClient` — async context manager; provides canned responses for testing; used with `httpx.AsyncClient`; does not make live requests.

### 2.4 `src/fris/data/edgar.py`
- `EdgarClientConfig` — configuration for EDGAR client (CIK, user-agent, rate limits).
- `EdgarClient` — main EDGAR client with methods for company lookup, submission fetching, filing retrieval.
- `EdgarError`, `EdgarHTTPError`, `EdgarRateLimitError`, `EdgarMalformedResponse` — error hierarchies.
- Key methods: `get_company_cik()`, `get_submissions()`, `get_filing()`, `fetch_document()`.

### 2.5 `src/fris/data/edgar_ingestion.py`
- `extract_sections_from_filing()` — async function that fetches a filing and extracts specified sections (item numbers 1, 1A, 7, 7A, 8).
- `_find_section_boundaries()`, `_extract_section_text()` — internal helpers for section extraction.
- `_normalize_accession()` — same function as in `models.py` (replicated for consistency).

### 2.6 `src/fris/orchestration/orchestrator.py`
- `ResearchOrchestrator` — coordinates specialist agent execution; produces `OrchestrationResult`.
- `TaskStatus` (enum: pending, running, completed, failed).
- `TaskType` (enum: fundamentals, industry).
- `TaskResult` — per-task result with status, error information.
- `OrchestrationResult` — overall result with tasks, timestamps, source reports.

### 2.7 `docs/milestone6_1_*`
- `EvidenceReference` model — confirmed field definitions and semantic clarifications (Milestone 6.1.5).
- `SynthesizedFinding` model — confirmed `evidence_references: list[EvidenceReference]`, `evidence_status`, `confidence` constraints.
- `ResearchSynthesizerResult` model — confirmed five semantic fields (`evidence_preserved`, `input_compatible`, `synthesis_complete`, `source_provenance_present`, `source_provenance_complete`).
- `VerificationOutcome` enum — confirmed five-valued taxonomy.
- Test plan scenarios and semantic definitions.

## 3. Recommended Architecture

### 3.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ResearchSynthesizerResult                      │
│  (input: 5 semantic fields, synthesized_findings, source_reports)     │
└─────────────────────▲───────────────────────────────────────────────┘
                      │
                      │ verify() — read-only invocation
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CitationVerifier (core)                         │
│  ├─ extract synthesized claims from synthesized_findings             │
│  ├─ for each claim: identify contributing original claims            │
│  ├─ for each: resolve EvidenceReference objects                     │
│  ├─ for each: attempt evidence retrieval (if allow_network)         │
│  ├─ for each: compare evidence with claim (deterministic first)      │
│  ├─ for each: assign VerificationOutcome                            │
│  ├─ for each: record EvidenceVerification, VerificationIssue entries │
│  ├─ aggregate per-claim results into CitationVerificationResult        │
│  ├─ compute sources_retrieved_successfully, sources_total            │
│  ├─ compute verification_completed, all_claims_evaluated             │
│  └─ return CitationVerificationResult (read-only)                   │
└─────────────────────▲───────────────────────────────────────────────┘
                      │
                      │ (optional) annotate OrchestrationResult
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Research Orchestrator Integration                  │
│  (optional: attach CitationVerificationResult as verification_annotation│
│   on OrchestrationResult; does NOT modify overall_status)             │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Key Design Decisions

| Decision | Rationale |
|---|---|
| **Reuse existing `EvidenceReference`** | No need to redefine; Milestone 6.1.5 already established field semantics and validation rules. |
| **Reuse existing `EdgarClient`** | Avoid duplicating SEC retrieval infrastructure; the Citation Verifier should use the same client the specialist agents use, ensuring consistent network authorization behavior. |
| **Deterministic first, LLM supplemental** | URL validation, accession normalization, filing metadata matching, evidence retrieval, exact excerpt matching, and numerical consistency checks where structured data is available must all be deterministic. LLM may assist with semantic evidence-to-claim comparison but must not be the sole source of truth. |
| **Read-only verification** | The verifier annotates and assesses without modifying the synthesized research report. This preserves the experimental research data flow and prevents unintended side effects. |
| **Network authorization at HTTP transport boundary** | The `allow_network` flag controls the httpx client used by `EdgarClient`, not the LLM MockClient. This ensures consistent behavior with the rest of FRIS. |
| **Five-valued outcome taxonomy** | `supported`, `partially_supported`, `contradicted`, `insufficient_evidence`, `unverifiable` provides granularity for experimental evaluation without collapsing into a single boolean. |
| **Incomplete provenance → `unverifiable`** | Claims missing `EvidenceReference.original_specialist` or `original_claim` raise `ValidationError`; claims missing source-locator fields receive `unverifiable` with documented provenance gap. This distinguishes retrieval failure from evidence-against. |
| **Numerical claims: close but not exact → `partially_supported`** | Per the methodology, if value, currency/unit, and period all match but the exact figure differs slightly, the outcome is `partially_supported` with the discrepancy documented. "Do not assume numerical verification is possible from a text excerpt alone" means if no explicit figure is present, it's `insufficient_evidence` for the numerical aspect. |
| **Interpretive disagreement → `partially_supported`** | When specialists agree on reported facts but differ on interpretations, the outcome is `partially_supported` with explicit distinction between fact and interpretation in `overall_limitations` and `verification_issues`. |
| **Contradictions between specialists → `contradicted`** | When specialists make incompatible claims with supporting evidence, both are evaluated independently; the overall outcome is `contradicted`. Both individual `verification_status` values are recorded. |

## 4. Important Technical Decisions

### 4.1 `allow_network` Flag Behavior

The `allow_network` flag in `CitationVerifier.verify()` controls whether HTTP transport is attempted:

- **`allow_network=True`**: The verifier's `EvidenceRetriever` uses the existing `EdgarClient` with an `httpx.AsyncClient` that has transport enabled. SEC filing requests are made (or mocked via `httpx.MockTransport` in tests). Outcomes reflect actual retrieval success or failure.

- **`allow_network=False`**: The verifier skips all HTTP transport. For any claim:
  - If the `EvidenceReference` has complete provenance (`source_url` populated ∨ `accession_number` ∧ `filing_type` ∧ `filing_date`), `retrieval_status = "not_attempted"` and the outcome is `unverifiable` with reason "network_access_disabled".
  - If the `EvidenceReference` has incomplete provenance (no source-locator fields), `retrieval_status = "not_attempted"` and the outcome is `unverifiable` with reason "provenance_gap + network_disabled".

**Critical:** The `allow_network` flag must NOT be bypassed by using the LLM `MockClient`. Network authorization is verified at the HTTP transport boundary (the `EdgarClient`/`httpx` layer), not at the `MockClient` level.

### 4.2 `confidence` Field Constraint

`confidence: Optional[float]` in `ClaimVerification` must be `None` unless `verification_status = VerificationOutcome.supported`. This prevents assigning confidence to unsupported or unverifiable claims. If the verifier uses LLM assistance, the LLM may suggest a confidence value, but the model constraint enforces that it's only stored when the claim is `supported`.

### 4.3 `source_provenance_present` vs. `source_provenance_complete`

Per Milestone 6.1.5:
- `source_provenance_present`: At least one source-related field is populated (`source_url` ∨ (`accession_number` ∧ `filing_type` ∧ `filing_date`)).
- `source_provenance_complete`: Enough source-location information exists to independently locate and inspect the underlying evidence.

**Implementation decision:** These are included as explicit fields on `EvidenceReference` (confirmed from Milestone 6.1.5 schema). The Citation Verifier reads these fields but does not recompute them; they remain as documented in Milestone 6.1. However, the verifier may document `source_location` in `EvidenceVerification` based on which fields are populated.

### 4.4 Numerical Claim Verification Constraints

- **Do not assume numerical verification is possible from a text excerpt alone.** If the filing only mentions "revenue grew" without stating a specific figure, the numerical claim cannot be verified — outcome for the numerical aspect is `insufficient_evidence`.
- **If figure is present:** Verify metric name, value, currency/unit, reporting period, fiscal vs. calendar period, and whether the figure is reported, calculated, or estimated.
- **Close but non-exact values:** If the claimed value is within a reasonable range of the filing value (e.g., claimed $10B, filing $9.8B), outcome is `partially_supported` with the discrepancy documented in `verification_issues` and `limitations`.
- **Fiscal vs. calendar period:** If the company uses a fiscal year ending August 31, and the claim references "FY 2023", verify that FY 2023 corresponds to the correct calendar period (e.g., Sep 1, 2022 – Aug 31, 2023). Mismatch → `insufficient_evidence` (period mismatch) or `contradicted` (if the claimed period explicitly contradicts the evidence period).

### 4.5 Read-Only Guarantee Enforcement

The `CitationVerifier.verify()` method is designed as a read-only operation:

- **No input modification:** The method signature takes `synthesizer_result: ResearchSynthesizerResult` and returns `CitationVerificationResult`. The input is never modified.
- **No nested modification:** Even nested objects (`synthesized_findings`, `evidence_references`, `EvidenceReference` objects) are not modified.
- **No persistence:** No file writes, no database updates, no network caching beyond the single invocation.
- **No agent state changes:** Specialist agent states are not affected.

This is enforced by:
1. Python's object model (no `__setattr__` on the input objects that would persist).
2. Documentation and code reviews.
3. Test validation (Scenario 16 confirms end-to-end with no modifications; tests verify input immutability).

### 4.6 Integration Strategy Staging

The Citation Verifier integrates in staged phases:

**Stage 1 — Standalone:** `CitationVerifier.verify(synthesizer_result)` produces `CitationVerificationResult` with no orchestrator changes.

**Stage 2 — Orchestrator annotation:** `OrchestrationResult.verification_annotation = CitationVerificationResult`. Does NOT modify `OrchestrationResult.overall_status` or `OrchestrationResult.tasks`.

**Stage 3 — End-to-end:** Full pipeline produces final report with verification appendix. Used for research evaluation.

**Stage 4 — Metrics generation:** Summary metrics computed from test runs and production invocations.

Each stage is optional; the verifier works standalone in Stage 1.

## 5. Risks and Limitations

| Risk | Mitigation |
|---|---|
| **Retrieval failure misclassified as evidence-support failure** | Strict separation: if HTTP request completed (even with errors), it's retrieval; if request completed and content read but doesn't support claim, it's evidence-support. Test scenarios NLA-1 through NLA-4 validate this distinction. |
| **Numerical claim over/under-verification** | Per methodology: only verify when explicit figure present in filing; close values → `partially_supported`; no explicit figure → `insufficient_evidence` for numerical aspect. Ground truth evaluation needed. |
| **Interpretive vs. factual confusion** | Explicit distinction in `overall_limitations` and `verification_reasoning`: state which claims are reported facts and which are interpretations. Test scenarios 6 and 7 validate. |
| **Agent agreement not equated with factual accuracy** | The verifier assesses evidence-support, not truth. Agent agreement is tracked in `agreements` list but does not influence `verification_status`. Explicit constraint in quality requirements. |
| **Network authorization bypass** | `allow_network` flag controls httpx transport, not MockClient. Tests NLA-1 through NLA-4 validate boundary respect. Code review ensures no circumvention. |
| **Incomplete provenance leading to false `unverifiable`** | Claims with `original_specialist`+`original_claim` but no source locators are `unverifiable` with documented provenance gap — this is correct per design, not a false negative. Test scenario 11A validates. |
| **LLM dependency introduction** | The verifier uses the existing provider-agnostic `LLMInferenceClient` protocol; no provider-specific SDKs added. LLM is supplemental only (deterministic first). Test scenarios without LLM calls (deterministic-only) validate. |
| **Test fixture coverage gap** | 21 scenarios cover major combinations but edge cases may exist. Ongoing evaluation and ground truth comparison recommended. |
| **Existing 68 tests may have collection errors** | Per Milestone 6.1.5 audit, clearly distinguish historical passing test results from current verification. The documentation revisions are self-contained; no source code modifications were made. |

## 6. Proposed Implementation Sequence

```
1. ✅ Phase 1: Repository inspection and model reuse (COMPLETED — documented in architecture/schema/test_plan)
2. □ Phase 2: Core CitationVerifier implementation (src/fris/verification/citation_verifier.py)
3. □ Phase 3: Schema and model extensions (src/fris/verification/models.py)
4. □ Phase 4: Test infrastructure setup (tests/test_verification/)
5. □ Phase 5: Integration and evaluation (orchestrator integration, metrics generation)
6. □ Phase 6: Documentation verification and final sign-off
   - Run all 21 test scenarios; all must pass
   - Verify no regressions in existing 68 tests
   - Verify no source code modifications beyond new files
   - Produce final verification report
```

**Each phase is independently addressable.** Phase 2 produces a runnable verifier even if later phases are not yet complete. Phase 4 can use synthetic fixtures without actual SEC retrieval. Phase 5 builds on Phase 4.

## 7. Exact Tests and Acceptance Criteria

### 7.1 Test Execution

Run: `python -m pytest tests/test_verification/ -v`

Expected: 21 test scenarios execute, all pass.

### 7.2 Acceptance Criteria Checklist

- [ ] All 21 test scenarios execute without unhandled exceptions.
- [ ] Validation scenarios (17–21) raise `ValidationError` as expected.
- [ ] Network authorization tests pass with `allow_network=True` and `allow_network=False`.
- [ ] No test makes a live SEC request unless `allow_network=True` with explicit consent.
- [ ] Deterministic behavior: identical inputs produce identical outputs across at least 3 consecutive runs.
- [ ] Retrieval failure vs. evidence-support failure distinction is correct in ≥ 95% of test cases.
- [ ] Milestone 6.1 semantic fields remain unchanged and pass without modification.
- [ ] `CitationVerifier.verify()` is read-only (input `ResearchSynthesizerResult` unchanged after invocation).
- [ ] `sources_independently_retrieved` is correctly True/False based on `allow_network` and actual retrieval success.
- [ ] `overall_outcome` is correctly assigned per the taxonomy for each scenario.
- [ ] `sources_retrieved_successfully` and `sources_total` have correct values.
- [ ] `verification_issues` list is populated with typed issues for scenarios that encounter them.
- [ ] `overall_limitations` documents relevant limitations for each scenario.
- [ ] Numerical claim handling: exact match → `supported`; close but not exact → `partially_supported`; no explicit figure → `insufficient_evidence` for numerical aspect.
- [ ] Interpretive disagreement → `partially_supported` with fact/interpretation distinction documented.
- [ ] Specialist contradiction → `contradicted` with both individual statuses recorded.
- [ ] Partial specialist failure → verification proceeds on available reports; unavailability documented.
- [ ] Incomplete provenance → `unverifiable` with provenance gap documented; no `ValidationError` for model construction (that's only for missing `original_specialist`/`original_claim`).
- [ ] `confidence` is `None` unless `verification_status = supported`.

### 7.3 Failure Case Sanity Checks

If any of the following occur, the implementation requires rework:

- A test scenario produces an outcome not in {supported, partially_supported, contradicted, insufficient_evidence, unverifiable}.
- `confidence` is set to a non-None value when `verification_status ≠ supported`.
- `allow_network=False` still enables HTTP transport (bypasses network authorization).
- `CitationVerificationResult` modifies the input `ResearchSynthesizerResult`.
- A retrieval failure (HTTP 404) produces `insufficient_evidence` instead of `unverifiable`.
- Evidence-support failure (content retrieved, doesn't support claim) produces `unverifiable` instead of `insufficient_evidence` or `contradicted`.
- `source_provenance_present` or `source_provenance_complete` are recomputed by the verifier (they should be read from `EvidenceReference` as established in Milestone 6.1.5).