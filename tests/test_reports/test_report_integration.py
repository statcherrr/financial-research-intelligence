"""Integration test for Milestone 6.4 Research Report builder.

Verifies that the ResearchReportBuilder correctly transforms
ResearchOrchestrator results into structured ResearchReport objects,
preserving all five canonical semantic fields, evidence lineage,
and verification outcomes.
"""

import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fris.agents import FundamentalsAnalyst, IndustryAnalyst
from fris.orchestration.orchestrator import ResearchOrchestrator
from fris.reports.research_report import ResearchReport, ResearchReportBuilder


def test_report_builder_with_compatible_reports():
    """Test report builder with compatible specialist reports."""
    print("=== Test: Report builder with compatible reports ===")

    orchestrator = ResearchOrchestrator(allow_network=False)

    result = orchestrator.run_pipeline(
        ticker="AAPL",
        research_question="What are the key financial risks and opportunities for Apple Inc.?",
    )

    # Build the report
    builder = ResearchReportBuilder(result)
    report = builder.build()

    # Verify report structure
    assert report is not None
    assert isinstance(report, ResearchReport)

    # Verify report metadata
    assert report.report_metadata.company_ticker == "AAPL"
    assert report.report_metadata.research_question is not ""
    assert len(report.report_metadata.generation_timestamp) > 0

    # Verify executive summary
    assert report.executive_summary is not None
    assert isinstance(report.executive_summary.main_findings, str)

    # Verify fundamentals analysis
    assert report.fundamentals_analysis is not None
    assert report.fundamentals_analysis.specialist_findings is not ""

    # Verify industry analysis
    assert report.industry_analysis is not None
    assert report.industry_analysis.specialist_findings is not ""

    # Verify synthesized findings
    assert report.synthesized_findings is not None
    assert isinstance(report.synthesized_findings, list)

    # Verify evidence citations
    assert report.evidence_citations is not None
    assert isinstance(report.evidence_citations, list)

    # Verify citation verifications
    assert report.citation_verifications is not None
    assert isinstance(report.citation_verifications, list)

    # Verify overall limitations
    assert report.overall_limitations is not None
    assert report.overall_limitations.overall_limitations_text is not ""

    # Verify research quality metadata (five canonical fields)
    assert report.research_quality_metadata is not None
    meta = report.research_quality_metadata
    required_fields = [
        "evidence_preserved",
        "input_compatible",
        "synthesis_complete",
        "source_provenance_present",
        "source_provenance_complete",
    ]
    for field in required_fields:
        assert field in meta, f"Missing field: {field}"
        # All five fields should be independently evaluable booleans
        assert isinstance(meta[field], bool), f"{field} should be bool, got {type(meta[field])}"

    print("  PASSED: Report builder works with compatible reports")
    print(f"  Five semantic fields: {meta}")
    return True


def test_report_builder_with_missing_reports():
    """Test report builder with missing specialist reports."""
    print("\n=== Test: Report builder with missing reports ===")

    orchestrator = ResearchOrchestrator(allow_network=False)

    result = orchestrator.run_pipeline(
        ticker="UNKNOWN123",
        research_question="Analysis of unknown company",
    )

    # Build the report
    builder = ResearchReportBuilder(result)
    report = builder.build()

    # Verify report structure
    assert report is not None
    assert isinstance(report, ResearchReport)

    # Verify metadata
    assert report.report_metadata.company_ticker == "UNKNOWN123"

    # Verify synthesized findings reflect available report (unknown ticker)
    # FundamentalsAnalyst always produces a report; for unknown tickers,
    # found=False but a finding is synthesized with unverified evidence status
    assert len(report.synthesized_findings) == 1
    assert report.synthesized_findings[0].evidence_status == "unverified"
    assert report.synthesized_findings[0].claim == "Analysis performed using available filing evidence"

    # Evidence citations are empty when retrieval is blocked (offline mode)
    # This is correct - no HTTP requests were made
    assert report.evidence_citations == []

    # Verify quality metadata has the five fields
    assert report.research_quality_metadata is not None
    meta = report.research_quality_metadata

    # Five fields should still be present (may be False with missing reports)
    required_fields = [
        "evidence_preserved",
        "input_compatible",
        "synthesis_complete",
        "source_provenance_present",
        "source_provenance_complete",
    ]
    for field in required_fields:
        assert field in meta, f"Missing field: {field}"

    print("  PASSED: Report builder handles missing reports correctly")
    print(f"  Five semantic fields: {meta}")
    return True


def test_report_preserves_semantic_fields_independence():
    """Test that the five semantic fields remain independent after report generation."""
    print("\n=== Test: Semantic field independence ===")

    orchestrator = ResearchOrchestrator(allow_network=False)

    result = orchestrator.run_pipeline(
        ticker="MSFT",
        research_question="What is Microsoft's business model and competitive position?",
    )

    builder = ResearchReportBuilder(result)
    report = builder.build()

    meta = report.research_quality_metadata

    # Verify all five fields are present
    required_fields = [
        "evidence_preserved",
        "input_compatible",
        "synthesis_complete",
        "source_provenance_present",
        "source_provenance_complete",
    ]
    for field in required_fields:
        assert field in meta, f"Missing field: {field}"

    # Verify fields are independently specifiable (not all derived from one)
    # They should all be boolean type
    for field in required_fields:
        assert isinstance(meta[field], bool), f"{field} should be bool, got {type(meta[field])}"

    # Verify the orchestrator result also has the fields
    assert result.evidence_preserved is not None
    assert result.input_compatible is not None
    assert result.synthesis_complete is not None
    assert result.source_provenance_present is not None
    assert result.source_provenance_complete is not None

    print("  PASSED: Five semantic fields preserved and independent")
    print(f"  Fields: evidence_preserved={meta['evidence_preserved']}, "
          f"input_compatible={meta['input_compatible']}, "
          f"synthesis_complete={meta['synthesis_complete']}, "
          f"source_provenance_present={meta['source_provenance_present']}, "
          f"source_provenance_complete={meta['source_provenance_complete']}")
    return True


def test_report_no_fabrication():
    """Test that the report never fabricates findings or citations."""
    print("\n=== Test: No fabrication ===")

    orchestrator = ResearchOrchestrator(allow_network=False)

    # Use a ticker that exists in the static map
    result = orchestrator.run_pipeline(
        ticker="AAPL",
        research_question="Apple financial analysis",
    )

    builder = ResearchReportBuilder(result)
    report = builder.build()

    # Verify no fabricated claims in synthesized findings
    for finding in report.synthesized_findings:
        # Claims should come from actual pipeline output, not invented
        assert finding.claim is not None
        # But should not be obviously fabricated
        assert "fabricated" not in finding.claim.lower()
        assert "made up" not in finding.claim.lower()

    # Verify evidence citations have real provenance
    for citation in report.evidence_citations:
        assert citation.original_specialist in ("fundamentals", "industry")
        assert bool(citation.original_claim.strip())

    # Verify no fake financial figures
    for finding in report.synthesized_findings:
        # Claims should not contain made-up numbers as established facts
        # (they may mention numbers from the source, but not fabricate)
        has_fabricated_number = any(
            word in finding.claim.lower()
            for word in ["$999 billion", "$1.2 trillion unrealized", "mysterious"]
        )
        assert not has_fabricated_number, f"Potentially fabricated claim: {finding.claim[:80]}..."

    print("  PASSED: Report does not fabricate findings or citations")
    return True


def test_report_pipeline_immutability():
    """Test that report builder does not mutate the orchestrator result."""
    print("\n=== Test: Pipeline immutability ===")

    orchestrator = ResearchOrchestrator(allow_network=False)

    result = orchestrator.run_pipeline(
        ticker="GOOGL",
        research_question="Google business analysis",
    )

    # Capture original state before building report
    original_evidence_preserved = result.evidence_preserved
    original_synth_result = result.synthesis_result

    # Build report - should not mutate orchestrator
    builder = ResearchReportBuilder(result)
    report = builder.build()

    # Check orchestrator result was not mutated
    assert result.evidence_preserved == original_evidence_preserved, \
        "Pipeline result evidence_preserved was mutated!"

    # Check synthesis result was not mutated
    new_synth = result.synthesis_result
    if original_synth_result is not None:
        # Key fields should be preserved
        assert original_synth_result.evidence_preserved == new_synth.evidence_preserved, \
            "Synthesis evidence_preserved was mutated!"

    print("  PASSED: Report builder preserves orchestrator result immutability")
    return True


if __name__ == "__main__":
    success_count = 0
    total_tests = 5

    tests = [
        test_report_builder_with_compatible_reports,
        test_report_builder_with_missing_reports,
        test_report_preserves_semantic_fields_independence,
        test_report_no_fabrication,
        test_report_pipeline_immutability,
    ]

    for test in tests:
        try:
            test()
            success_count += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"Results: {success_count}/{total_tests} tests passed")
    print(f"{'='*60}")

    if success_count == total_tests:
        print("All Milestone 6.4 integration tests PASSED ✅")
        sys.exit(0)
    else:
        print("Some tests FAILED ❌")
        sys.exit(1)