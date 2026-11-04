# FRIS — Milestone 6.2: Citation Verifier Test Plan

## 1. Test Scenario Inventory

### 21 Total Scenarios: 16 Behavioral + 5 Validation

**Behavioral scenarios (16):** Each exercises the CitationVerifier with specific input fixtures and specifies all applicable field values. No scenario uses `N/A` for any field.

**Validation scenarios (5):** Each asserts that `ValidationError` is raised during model construction; field values are N/A for these scenarios.

### Behavioral Scenarios (1–16)

| Scenario | Description | Key Fixtures | Expected Key Fields |
|---|---|---|---|
| **1** | Both specialist reports present with full provenance | Two `ResearchReport` objects with matching tickers, complete `EvidenceReference` objects (original_specialist + original_claim + source locators) | `sources_independently_retrieved=True`, `overall_outcome` depends on evidence support, `verification_completed=True`, `all_claims_evaluated=True` |
| **2** | One report missing (only fundamentals report) | One `ResearchReport` (fundamentals), `source_reports = {'fundamentals': report, 'industry': None}` | `sources_independently_retrieved=True` (available report retrieved), `overall_outcome` based on available claims, `verification_completed=True`, `all_claims_evaluated=True`, `research_limitations` documents missing industry coverage |
| **3** | Both reports exist but have empty findings | Two `ResearchReport` objects with findings = [] (empty lists), matching tickers | `sources_independently_retrieved=True` (retrieval attempted), `overall_outcome = "unverifiable"` (no findings to assess), `verification_completed=True`, `all_claims_evaluated=True`, `overall_limitations` = "no available findings to synthesize" |
| **4** | Ticker mismatch between input and reports | `ResearchSynthesizerResult` with ticker="AAPL" but reports have ticker="MSFT", complete provenance | `sources_independently_retrieved=True` (retrieval attempted for both), `overall_outcome = "insufficient_evidence"` (ticker mismatch prevents claim assessment), `verification_completed=True`, `all_claims_evaluated=True`, `overall_limitations` = "ticker mismatch: reports reference MSFT, question targets AAPL" |
| **5** | Different research-question scopes | Reports address "revenue analysis" but question asks "risk factor analysis"; complete provenance | `sources_independently_retrieved=True`, `overall_outcome = "insufficient_evidence"` (scope mismatch), `verification_completed=True`, `all_claims_evaluated=True`, `overall_limitations` = "research-question scope: available findings address revenue, question targets risk" |
| **6** | Direct factual contradiction between specialists | Fundamentals claims "revenue increased" while industry claims "revenue decreased" with supporting evidence; matching tickers | `sources_independently_retrieved=True`, `overall_outcome = "contradicted"`, `verification_completed=True`, `all_claims_evaluated=True`, `verification_issues` includes "specialist contradiction: fundamentals vs industry", `overall_limitations` documents both claims |
| **7** | Interpretive disagreement between specialists | Both specialists agree on reported fact but differ on interpretation; matching tickers, complete provenance | `sources_independently_retrieved=True`, `overall_outcome = "partially_supported"` (facts supported, interpretations differ), `verification_completed=True`, `all_claims_evaluated=True`, `verification_issues` documents interpretation gap, `overall_limitations` distinguishes fact from interpretation |
| **8** | Different time horizons in claims | Claim states "revenue for fiscal year 2023"; evidence from "Q3 2024 quarterly filing"; matching tickers, otherwise complete provenance | `sources_independently_retrieved=True`, `overall_outcome = "insufficient_evidence"` (period mismatch), `verification_completed=True`, `all_claims_evaluated=True`, `overall_limitations` = "period mismatch: claimed FY 2023, evidence from Q3 2024" |
| **9** | Compatible considerations across specialists | Both specialists identify related but distinct considerations (e.g., one identifies revenue growth, other identifies margin pressure); matching tickers, compatible scopes | `sources_independently_retrieved=True`, `overall_outcome = "partially_supported"` (compatible but separate considerations), `verification_completed=True`, `all_claims_evaluated=True`, `overall_limitations` = "compatible considerations: revenue growth and margin pressure are related but distinct" |
| **10** | Unsupported numerical claim | Claim states "revenue of $10B for FY 2023"; evidence from filing states "revenue of $9.8B for FY 2023" (close but not exact match); matching tickers | `sources_independently_retrieved=True`, `overall_outcome = "partially_supported"` (numerical close but not exact; per numerical verification rules), `verification_completed=True`, `all_claims_evaluated=True`, `verification_issues` includes "numerical mismatch: claimed $10B vs. filing $9.8B", `overall_limitations` documents the discrepancy and that "exact numerical verification requires structured data" |
| **11A** | Source metadata missing but claim lineage retained | `EvidenceReference` with `original_specialist` and `original_claim` populated, but all source-locator fields (`source_url`, `accession_number`, `filing_type`, `filing_date`) are None; other metadata empty | `sources_independently_retrieved=False` (no locator fields → retrieval not attempted), `overall_outcome = "unverifiable"`, `verification_completed=True`, `all_claims_evaluated=True`, `verification_issues` includes "provenance_gap: no source-locator fields populated", `source_location` = "provenance_gap", `retrieval_status` = "not_attempted" |
| **11B** | Empty evidence references list | `ClaimVerification` with `evidence_references = []`; `synthesized_claim` present | `sources_independently_retrieved=False` (no references to retrieve), `overall_outcome = "unverifiable"`, `verification_completed=True`, `all_claims_evaluated=True`, `overall_limitations` = "no evidence references provided", `evidence_excerpt` = None |
| **11C** | EvidenceReference missing `original_specialist` | Construction of `EvidenceReference` without `original_specialist` field | **ValidationError raised** (this is a validation test; field values are N/A) |
| **11D** | EvidenceReference missing `original_claim` | Construction of `EvidenceReference` without `original_claim` field | **ValidationError raised** (this is a validation test; field values are N/A) |
| **12** | Provenance preservation (all references have complete lineage) | Multiple `EvidenceReference` objects, all with `original_specialist` + `original_claim` populated, some with source locators present | `sources_independently_retrieved=True` (locators present + retrieval attempted), `overall_outcome` depends on evidence content, `verification_completed=True`, `all_claims_evaluated=True`, `evidence_preserved` context from Milestone 6.1 (not directly measured by verifier) |
| **13** | Partial specialist failure (one report unavailable) | One report available with complete provenance, one report raises HTTP error 503 during retrieval; question targets available report's company | `sources_independently_retrieved=True` (available report retrieved successfully), `overall_outcome` based on available claims, `verification_completed=True`, `all_claims_evaluated=True`, `verification_issues` includes "retrieval_failed for industry report (HTTP 503)", `overall_limitations` = "industry report unavailable (HTTP 503); verification based on fundamentals only" |
| **14** | Deterministic behavior (same input → same output) | Same `ResearchSynthesizerResult` invoked twice with `allow_network=False`; both invocations should produce identical `CitationVerificationResult` (same `verification_status` per claim, same `overall_outcome`, same `verification_issues` sorted by issue_id) | First invocation: full results. Second invocation: identical results. Document: "deterministic behavior confirmed: identical inputs produce identical outputs across runs" |
| **15** | Invalid top-level Pydantic inputs | Construction of `CitationVerificationResult` with invalid `company_ticker` (e.g., empty string) or `research_question` (empty) | **ValidationError raised** (this is a validation test; field values are N/A) |
| **16** | Both reports present with full provenance (end-to-end) | Two `ResearchReport` objects with matching tickers, complete `EvidenceReference` objects, claims that are explicitly supported by the evidence | `sources_independently_retrieved=True`, `overall_outcome = "supported"`, `verification_completed=True`, `all_claims_evaluated=True`, `sources_retrieved_successfully` = total count, `verification_issues` = [], `overall_limitations` = "" (no limitations) |

### Validation Scenarios (17–21)

| Scenario | Model Constructed | Expected Error |
|---|---|---|
| **17** | `EvidenceReference` without `original_specialist` | `ValidationError` raised |
| **18** | `EvidenceReference` without `original_claim` | `ValidationError` raised |
| **19** | `ClaimVerification` with invalid `evidence_references` (entries missing `original_specialist`) | `ValidationError` raised |
| **20** | `ClaimVerification` with invalid `synthesized_claim` (empty string) | `ValidationError` raised |
| **21** | `CitationVerificationResult` with empty `claims` list and `overall_outcome` not matching | **ValidationError raised** (at least one claim required when `overall_outcome` is specified; or `overall_outcome` must be justifiable from claims distribution) |

**Note on validation scenario counts:** Old scenarios 17–20 from prior drafts that overlapped with 11C/11D/15 have been eliminated/renumbered. The current validation set (17–21) covers distinct construction validation boundaries: EvidenceReference missing required fields (17–18), ClaimVerification construction validation (19–20), and CitationVerificationResult construction validation (21). Each tests a different model construction boundary.

## 2. Synthetic Fixtures

### 2.1 ResearchReport Fixture (Minimal)

```python
# tests/test_citation/fixtures.py

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
```

### 2.2 EvidenceReference Fixtures

```python
# Fully specified EvidenceReference (with source locators)
ref_full = EvidenceReference(
    original_specialist="fundamentals",
    original_claim="Apple reported revenue of $94.8B for Q3 2024",
    source_url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000012/index.html",
    accession_number="0000320193-24-000012",
    filing_type="10-Q",
    filing_date="2024-08-08",
    filing_section="7",
    evidence_text="Revenue of $94.8 billion, up 2.1% year-over-year",
)

# EvidenceReference with only lineage (no source locators)
ref_lineage_only = EvidenceReference(
    original_specialist="industry",
    original_claim="Competitive pressure may limit future growth"
    # All source-locator fields are None
)

# EvidenceReference with partial provenance
ref_partial = EvidenceReference(
    original_specialist="fundamentals",
    original_claim="Revenue growth driven by iPhone sales",
    source_url="https://www.sec.gov/Archives/edgar/data/320193/000032019324000012/index.html",
    # accession_number, filing_type, filing_date are None
)
```

### 2.3 SynthesizedFinding Fixtures

```python
# Both specialists present, claim supported by evidence
findings_supported = SynthesizedFinding(
    claim="Apple demonstrated strong financial performance in Q3 2024",
    category="reported_fact",
    source_specialists=["fundamentals", "industry"],
    original_claims=[
        "Apple reported revenue of $94.8B for Q3 2024",
        "Competitive pressure may limit future growth"
    ],
    evidence_references=[ref_full, ref_lineage_only]
)

# One report missing scenario
findings_missing_report = SynthesizedFinding(
    claim="Apple's risk factors include regulatory uncertainty",
    category="interpretive",
    source_specialists=["fundamentals"],
    original_claims=[
        "Apple's risk factors include regulatory uncertainty"
    ],
    evidence_references=[ref_full]
)

# Ticker mismatch scenario
findings_ticker_mismatch = SynthesizedFinding(
    claim="Microsoft's revenue growth driven by cloud",
    category="reported_fact",
    source_specialists=["industry"],
    original_claims=[
        "Microsoft Azure revenue grew 25% in Q3 2024"
    ],
    evidence_references=[ref_msft_10q]  # ref_msft_10q has ticker="MSFT"
)
```

### 2.4 ResearchSynthesizerResult Fixtures

```python
# Full provenance result
result_full = ResearchSynthesizerResult(
    company_ticker="AAPL",
    research_question="What are Apple's main revenue drivers and risk factors?",
    executive_summary="Apple demonstrated strong revenue driven by iPhone, with risk factors including regulatory uncertainty.",
    synthesized_findings=[findings_supported, findings_missing_report],
    contradictions=[],
    agreements=["Both specialists identify iPhone as key revenue driver"],
    opportunities=["Expanding services revenue"],
    risks=["Regulatory scrutiny"],
    research_gaps=[],
    explicit_limitations="",
    evidence_preserved=True,
    report_timestamp="2025-01-15T10:30:00-05:00",
    source_reports={"fundamentals": fundamentals_report, "industry": industry_report}
)
```

## 3. Expected Outcomes Per Scenario

### 3.1 Outcome Table

| Scenario | `sources_independently_retrieved` | `overall_outcome` | `verification_completed` | `all_claims_evaluated` | `sources_retrieved_successfully` | `verification_issues` | `overall_limitations` |
|---|---|---|---|---|---|---|---|
| 1 | True | (depends on evidence) | True | True | count | [] | "" |
| 2 | True | (based on available claims) | True | True | partial | ["missing industry report"] | "no industry report provided" |
| 3 | True | "unverifiable" | True | True | 0 | ["no findings to assess"] | "no available findings to synthesize" |
| 4 | True | "insufficient_evidence" | True | True | count | ["ticker mismatch"] | "ticker mismatch: reports reference MSFT, question targets AAPL" |
| 5 | True | "insufficient_evidence" | True | True | count | ["scope mismatch"] | "research-question scope: available findings address revenue, question targets risk" |
| 6 | True | "contradicted" | True | True | count | ["specialist contradiction"] | "fundamentals and industry claims contradict with supporting evidence" |
| 7 | True | "partially_supported" | True | True | count | ["interpretation gap"] | "facts supported, interpretations differ" |
| 8 | True | "insufficient_evidence" | True | True | count | ["period mismatch"] | "claimed FY 2023, evidence from Q3 2024" |
| 9 | True | "partially_supported" | True | True | count | ["compatible considerations"] | "revenue growth and margin pressure are related but distinct" |
| 10 | True | "partially_supported" | True | True | count | ["numerical mismatch"] | "claimed $10B vs. filing $9.8B; exact numerical verification requires structured data" |
| 11A | False | "unverifiable" | True | True | 0 | ["provenance_gap: no source-locator fields"] | "no source-locator fields populated; retrieval not attempted" |
| 11B | False | "unverifiable" | True | True | 0 | ["no evidence references"] | "no evidence references provided; nothing to assess" |
| 11C | N/A (validation) | N/A | N/A | N/A | N/A | N/A | ValidationError raised |
| 11D | N/A (validation) | N/A | N/A | N/A | N/A | N/A | ValidationError raised |
| 12 | True | (depends on evidence) | True | True | count | [] | "" |
| 13 | True | (based on available) | True | True | partial | ["retrieval_failed for unavailable report"] | "report unavailable (HTTP 503); verification based on available report" |
| 14 | True | True across both runs | True | True | count | [] | "" |
| 15 | N/A (validation) | N/A | N/A | N/A | N/A | N/A | ValidationError raised |
| 16 | True | "supported" | True | True | count | [] | "" |

### 3.2 Detailed Per-Claim Outcome Expectations

**Scenario 1 (both reports, full provenance):** Each claim is evaluated against its EvidenceReference. If the evidence_excerpt explicitly confirms the claim → `verification_status = supported` for that claim. If evidence contradicts → `contradicted`. If evidence exists but doesn't clearly address → `insufficient_evidence`. If no EvidenceReference has source locators → `unverifiable` for that claim.

**Scenario 6 (contradiction between specialists):** Both claims are evaluated independently. The fundamentals claim gets its own `verification_status`, the industry claim gets its own. The `overall_outcome` for the `CitationVerificationResult` is `contradicted` because any contradicted claim pulls the overall outcome to `contradicted`. Both individual `verification_status` values are recorded (likely one `supported` and one `contradicted`, or both `contradicted` depending on exact evidence).

**Scenario 10 (unsupported numerical claim):** The numerical claim is verified per the numerical methodology: metric name matches, value is close but not exact ($10B claimed vs. $9.8B in filing), currency/unit matches, reporting period matches (FY 2023 for both), fiscal vs. calendar period matches. Outcome: `partially_supported` because the value is close but not exact, and per the rules "do not assume numerical verification is possible from a text excerpt alone" — the close match is noted but the exact mismatch means the numerical aspect is only partially supported.

**Scenario 11A (missing source metadata):** Since no `source_url`, `accession_number`, `filing_type`, or `filing_date` are populated, `retrieval_status = "not_attempted"`, `sources_independently_retrieved = False` at the result level (no sources could be independently retrieved). `overall_outcome = "unverifiable"` because the claim cannot be evaluated without retrievable evidence. `verification_issues` includes "provenance_gap: no source-locator fields populated". `source_location` = "provenance_gap".

**Scenario 13 (partial specialist failure):** The available report's evidence is retrieved successfully (`retrieval_status = "retrieved"` for that report). The unavailable report's retrieval fails with HTTP 503 (`retrieval_status = "retrieval_failed"`, `retrieval_reason = "HTTP 503"`). At the result level, `sources_independently_retrieved = True` because at least one source was successfully retrieved. `overall_outcome` is based on the available claims. `verification_issues` includes "retrieval_failed for industry report (HTTP 503)". `overall_limitations` = "industry report unavailable (HTTP 503); verification based on fundamentals only".

## 4. Network Authorization Tests

### 4.1 Test Configuration

All network authorization tests must respect the existing FRIS network boundaries:

- **`allow_network=True`**: HTTP transport is enabled; real (mocked) SEC requests may be made.
- **`allow_network=False`**: Network access is disabled; the CitationVerifier must NOT attempt HTTP requests. Outcomes for any claim without complete provenance (no source_url, no accession_number+filing_type+filing_date) must be `unverifiable` with `retrieval_status = "not_attempted"`.

### 4.2 Network Authorization Scenario

**Scenario NLA-1:** CitationVerifier invoked with `allow_network=False` and a `ResearchSynthesizerResult` where all `EvidenceReference` objects have complete provenance (`source_url` populated).

- **Expected:** `sources_independently_retrieved = False` (network disabled, retrieval not attempted despite complete provenance).
- **Expected:** `overall_outcome = "unverifiable"` (cannot retrieve evidence without network).
- **Expected:** `verification_issues` includes "network_access_disabled: retrieval not attempted per network authorization boundary".
- **Expected:** `retrieval_status = "not_attempted"` for all claims.

**Scenario NLA-2:** CitationVerifier invoked with `allow_network=False` and `ResearchSynthesizerResult` where some `EvidenceReference` objects have incomplete provenance (no source-locator fields).

- **Expected:** Same as NLA-1: `sources_independently_retrieved = False`, `overall_outcome = "unverifiable"`, `retrieval_status = "not_attempted"`.
- **Rationale:** The verifier must not circumvent network authorization boundaries. Even if provenance is complete, without `allow_network=True`, retrieval is not attempted.

**Scenario NLA-3:** CitationVerifier invoked with `allow_network=True` and a mock `httpx.MockTransport` that returns a 404 for the SEC filing URL.

- **Expected:** `sources_independently_retrieved = False` (retrieval attempted but returned 404).
- **Expected:** `overall_outcome = "unverifiable"` with `retrieval_status = "retrieval_failed"` and `retrieval_reason = "HTTP 404"`.
- **Expected:** `verification_issues` includes "retrieval_failed: HTTP 404 for SEC filing URL".
- **Critical:** This must be distinguished from "evidence-support failure." The source was attempted but not found; outcome is `unverifiable`, NOT `insufficient_evidence`.

**Scenario NLA-4:** CitationVerifier invoked with `allow_network=True` and a mock `httpx.MockTransport` that returns a valid filing but the evidence excerpt cannot be matched.

- **Expected:** `sources_independently_retrieved = True` (retrieval succeeded).
- **Expected:** `overall_outcome = "insufficient_evidence"` (evidence retrieved but doesn't address the claim).
- **Expected:** `verification_issues` includes "evidence_mismatch: excerpt not found in retrieved filing".
- **Distinction:** This is an evidence-support failure (retrieval succeeded, but evidence doesn't support the claim), not a retrieval failure.

### 4.3 No Live SEC Requests During Tests

**Mandatory:** No test should make a live SEC request unless explicitly authorized through the test infrastructure's `allow_network=True` flag with explicit user consent. All SEC request mocking must use `httpx.MockTransport` or equivalent.

**Verification:** Each test must either:
- Use `httpx.MockTransport` with predefined responses, OR
- Be explicitly marked with `network_authorization: True` and run only when the user has consented to live network access.

**The verifier must not equate an LLM MockClient with disabled SEC HTTP access.** Network authorization is verified at the HTTP transport boundary (httpx client configuration), not at the MockClient level. The `allow_network` flag controls the httpx client used by `EdgarClient`, not the LLM client.

## 5. Failure Handling

### 5.1 Error Classes the Verifier Must Handle

| Error Type | Verifier Response | Outcome Assignment |
|---|---|---|
| **HTTP 404 (filing not found)** | `retrieval_failed` → `unverifiable` | `unverifiable` with `retrieval_reason = "HTTP 404"` |
| **HTTP 410 (gone)** | `retrieval_failed` → `unverifiable` | `unverifiable` with `retrieval_reason = "HTTP 410"` |
| **HTTP 429 (rate limit)** | Retry once; on persistent: `retrieval_failed` → `unverifiable` | `unverifiable` with `retrieval_reason = "HTTP 429 rate limit"` |
| **HTTP 500 (server error)** | `retrieval_failed` → `unverifiable` | `unverifiable` with `retrieval_reason = "HTTP 500"` |
| **HTTP 503 (unavailable)** | `retrieval_failed` → `unverifiable` | `unverifiable` with `retrieval_reason = "HTTP 503"` |
| **Malformed XML/HTML in filing** | Attempt best-effort extraction; if extraction fails: `retrieval_failed` → `unverifiable` | `unverifiable` with `retrieval_reason = "malformed_filing"` |
| **Empty filing document** | `retrieval_failed` → `unverifiable` | `unverifiable` with `retrieval_reason = "empty_filing"` |
| **Evidence excerpt not found in retrieved filing** | `evidence_mismatch` → `insufficient_evidence` or `contradicted` depending on content | `insufficient_evidence` if excerpt context doesn't address claim; `contradicted` if filing says opposite |
| **Invalid accession number** (cannot be normalized) | `retrieval_failed` → `unverifiable` | `unverifiable` with `retrieval_reason = "invalid_accession_number"` |
| **Missing source_url** + incomplete accession metadata | `retrieval_failed` → `unverifiable` (provenance_gap) | `unverifiable` with `retrieval_reason = "provenance_gap"` |
| **LLM output malformed** | Fall back to deterministic outcome; record "LLM_output_malformed" issue | Maintain last deterministic outcome; add verification issue |
| **Low-confidence LLM judgment** | Fall back to deterministic outcome; record "low_confidence" issue | Maintain deterministic outcome; add verification issue |

### 5.2 Distinguishing Retrieval Failure from Evidence-Support Failure

**The verifier must never conflate these two categories.**

**Retrieval failure examples (outcome = `unverifiable`):**
- SEC filing URL returns HTTP 404 → `unverifiable`, reason "HTTP 404"
- Rate limiting prevents retrieval after retries → `unverifiable`, reason "HTTP 429 rate limit"
- Network disabled (`allow_network=False`) → `unverifiable`, reason "network_access_disabled"
- Accession number cannot be normalized → `unverifiable`, reason "invalid_accession_number"
- Source URL is None and no accession metadata → `unverifiable`, reason "provenance_gap"

**Evidence-support failure examples (outcome = `insufficient_evidence` or `contradicted`):**
- Filing retrieved successfully (HTTP 200) but relevant section not included → `insufficient_evidence`
- Filing retrieved and section found, but evidence excerpt says opposite of claim → `contradicted`
- Filing retrieved, excerpt found, but covers different time period → `insufficient_evidence` (period mismatch) or `contradicted` (if period explicitly contradicts)
- Numerical figure claimed is not present in filing, but qualitative statement is → `insufficient_evidence` for the numerical aspect

**Key indicator:** If the HTTP request completed (even with errors), it's a retrieval issue. If the request completed and the content was read but doesn't support the claim, it's an evidence-support issue.

## 6. Evaluation Metrics

The Citation Verifier should generate evaluation data for FRIS's central research question. Recommended metrics (computed from test runs):

| Metric | Formula | Description |
|---|---|---|
| **Claim verification rate** | `(count of claims with definitive outcome) / (total claims evaluated)` | Definitive = supported, contradicted, or insufficient_evidence. Excludes unverifiable due to retrieval failures. |
| **Support rate** | `count(claims with verification_status = supported) / (total claims)` | Percentage of claims where evidence explicitly confirms the claim. |
| **Contradiction rate** | `count(claims with verification_status = contradicted) / (total claims)` | Percentage of claims where evidence directly contradicts the claim. |
| **Partial support rate** | `count(claims with verification_status = partially_supported) / (total claims)` | Percentage of claims with partial confirmation. |
| **Unverifiable rate** | `count(claims with verification_status = unverifiable) / (total claims)` | Percentage of claims that cannot be evaluated. Breakdown: retrieval_failed vs. provenance_gap. |
| **Source retrieval success rate** | `count(sources with retrieval_status = retrieved) / (sources total)` | Of attempted retrievers, what percentage succeeded. |
| **Citation precision** | `count(supported claims with explicit evidence_excerpt) / (count(supported claims))` | Of supported claims, what percentage have a citable evidence excerpt. |
| **Verification latency** | `sum(time.per_result) / (count results)` | Average time from invoke to result production. |
| **False-positive rate** | `(count supported claims where ground truth says insufficient/contradicted) / (count supported claims)` | Requires manually labeled ground truth. |
| **False-negative rate** | `(count insufficient_evidence/unverifiable claims where ground truth says supported) / (count insufficient_evidence/unverifiable)` | Requires manually labeled ground truth. |

**Evaluating verifier quality against ground truth:**

- Create a manually labeled dataset of synthesized claims with ground truth verification outcomes.
- Compare the Citation Verifier's outcomes against the ground truth.
- Calculate precision/recall for each outcome type.
- Specifically evaluate: does `supported` correctly identify claims where evidence is present in the filing? does `unverifiable` correctly reflect retrieval/provenance issues rather than evidence-against? does the verifier distinguish `contradicted` from `insufficient_evidence` appropriately?

**Important constraint:** Do not claim that agent agreement establishes factual accuracy. Agent agreement (both specialists making the same claim) is a separate concern from evidence support. The verifier must assess each claim against its evidence independently.

## 7. Test Gates and Acceptance Criteria

### 7.1 Test Gates (must all pass before Milestone 6.2 approval)

1. **All 21 test scenarios execute without unhandled exceptions.**
2. **Validation scenarios (17–21) raise `ValidationError` as expected.**
3. **Network authorization tests pass with `allow_network=True` and `allow_network=False`.**
4. **No test makes a live SEC request unless `allow_network=True` with explicit consent.**
5. **Deterministic behavior: identical inputs produce identical outputs across at least 3 consecutive runs.**
6. **Retrieval failure vs. evidence-support failure distinction is correct in ≥ 95% of test cases.**
7. **Milestone 6.1 semantic fields remain unchanged and pass without modification.**

### 7.2 Acceptance Criteria

- **Per-claim accuracy:** For synthetic fixtures with known ground truth, the Citation Verifier assigns the correct `verification_status`.
- **Outcome taxonomy compliance:** All `verification_status` values are from the set {supported, partially_supported, contradicted, insufficient_evidence, unverifiable}.
- **No retroactive field modification:** The five Milestone 6.1 semantic fields are not altered by the Citation Verifier.
- **Read-only invocation:** `CitationVerifier.verify()` does not modify input `ResearchSynthesizerResult` or any nested objects.
- **Network boundary respect:** `allow_network=False` prevents all HTTP transport attempts; `allow_network=True` enables them.
- **Retrieval failure distinction:** Tests confirm that retrieval failures (HTTP errors, 404, rate limits) produce `unverifiable` outcomes, while evidence-support failures (content retrieved but doesn't support claim) produce `insufficient_evidence` or `contradicted` outcomes.
- **Numerical claim handling:** Numerical claims are assessed per the defined methodology (metric, value, currency, period, fiscal/calendar, reported/calculated/estimated). Close but non-exact values receive `partially_supported`.
- **Incomplete provenance handling:** Claims with missing `EvidenceReference.original_specialist` or `original_claim` are handled via validation errors; claims with missing source-locator fields receive `unverifiable` with documented provenance gap.
- **Contradiction between specialists:** When specialists make contradictory claims with supporting evidence, both are evaluated independently and the overall outcome reflects the contradiction.
- **Interpretive disagreement handling:** When specialists agree on facts but differ on interpretations, outcome is `partially_supported` with explicit distinction between fact and interpretation in `overall_limitations` and `verification_issues`.
- **Partial specialist failure:** When one report is unavailable, verification proceeds on available reports; the unavailability is documented in `verification_issues` and `overall_limitations`.
- **Deterministic behavior confirmed:** Same inputs produce same outputs across multiple runs; variance only due to non-deterministic LLM calls (which are supplemental, not deterministic).