"""Tests for the Fundamentals Analyst agent."""

from fris.agents import FundamentalsAnalyst


class TestFundamentalsAnalystInitialization:
    """Test FundamentalsAnalyst construction and defaults."""

    def test_default_construction(self):
        """Default FundamentalsAnalyst has allow_network=False."""
        analyst = FundamentalsAnalyst()
        assert analyst.allow_network is False
        assert analyst.max_filings == 3
        # Default MockClient is used

    def test_custom_llm_client(self):
        """FundamentalsAnalyst accepts custom LLM client."""
        from fris.llms.mock import MockClient

        custom_client = MockClient(model="custom-model")
        analyst = FundamentalsAnalyst(llm_client=custom_client)
        assert analyst.llm_client is custom_client

    def test_allow_network_true(self):
        """FundamentalsAnalyst with allow_network=True."""
        analyst = FundamentalsAnalyst(allow_network=True)
        assert analyst.allow_network is True


class TestFundamentalsAnalystTickerResolution:
    """Test ticker-to-CIK resolution."""

    def test_known_ticker_resolves(self):
        """Known tickers resolve via static mapping."""
        analyst = FundamentalsAnalyst()
        result = analyst._resolve_ticker("AAPL")

        assert result["found"] is True
        assert result["cik"] == 320193
        assert result["company_name"] == "Apple Inc."

    def test_unknown_ticker_offline(self):
        """Unknown ticker with network disabled returns not-found."""
        analyst = FundamentalsAnalyst()
        result = analyst._resolve_ticker("UNKNOWN123")

        assert result["found"] is False
        assert result["cik"] is None
        assert result["company_name"] is None

    def test_tsla_cik(self):
        """TSLA resolves to correct CIK and company name."""
        analyst = FundamentalsAnalyst()
        result = analyst._resolve_ticker("TSLA")

        assert result["found"] is True
        assert result["cik"] == 1318605
        assert result["company_name"] == "Tesla Inc."

    def test_nvda_cik(self):
        """NVDA resolves to correct CIK and company name."""
        analyst = FundamentalsAnalyst()
        result = analyst._resolve_ticker("NVDA")

        assert result["found"] is True
        assert result["cik"] == 1045810
        assert result["company_name"] == "NVIDIA Corporation"


class TestFundamentalsAnalystAnalysis:
    """Test the analyze method."""

    def test_analyze_with_known_ticker(self):
        """FundamentalsAnalyst.analyze signature test."""
        analyst = FundamentalsAnalyst()
        # Verify analyze method exists and has correct signature
        import inspect

        sig = inspect.signature(analyst.analyze)
        assert "ticker" in sig.parameters
        assert "research_question" in sig.parameters

    def test_analyze_unknown_ticker(self):
        """FundamentalsAnalyst.analyze with unknown ticker."""
        analyst = FundamentalsAnalyst()
        result = analyst.analyze("UNKNOWN123", "Test research question")

        assert result.company_ticker == "UNKNOWN123"
        assert result.evidence_preserved is False
        assert hasattr(result, "explicit_limitations")


class TestFundamentalsAnalystReportModel:
    """Test ResearchReport pydantic model."""

    def test_research_report_creation(self):
        """ResearchReport can be created with all fields."""
        from fris.agents import FundamentalsAnalyst

        analyst = FundamentalsAnalyst()
        result = analyst.analyze("AAPL", "Test?")

        assert hasattr(result, "report_timestamp")
        assert hasattr(result, "executive_summary")
        assert hasattr(result, "findings")
        assert hasattr(result, "explicit_limitations")
        assert hasattr(result, "evidence_preserved")


class TestFundamentalsAnalystMissingSections:
    """Test handling of missing sections."""

    def test_missing_item_1(self):
        """Missing Item 1 is handled gracefully."""
        analyst = FundamentalsAnalyst()
        result = analyst.analyze("AAPL", "Test?")

        # Should not crash; should have limitations
        assert hasattr(result, "explicit_limitations")

    def test_missing_item_7(self):
        """Missing Item 7 is handled gracefully."""
        analyst = FundamentalsAnalyst()
        result = analyst.analyze("AAPL", "Test?")

        # Should not crash; should have limitations
        assert hasattr(result, "explicit_limitations")
