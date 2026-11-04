"""Tests for the Industry Analyst agent."""

from fris.agents.industry import IndustryAnalyst


class TestIndustryAnalystInitialization:
    """Test IndustryAnalyst construction and defaults."""

    def test_default_construction(self):
        """Default IndustryAnalyst has allow_network=False."""
        analyst = IndustryAnalyst()
        assert analyst.allow_network is False

    def test_custom_llm_client(self):
        """IndustryAnalyst accepts custom LLM client."""
        from fris.llms.mock import MockClient

        custom_client = MockClient(model="custom-model")
        analyst = IndustryAnalyst(llm_client=custom_client)
        assert analyst.llm_client is custom_client

    def test_allow_network_true(self):
        """IndustryAnalyst with allow_network=True."""
        analyst = IndustryAnalyst(allow_network=True)
        assert analyst.allow_network is True

    def test_ticker_map_coverage(self):
        """Ticker-to-CIK map covers all six supported tickers."""
        analyst = IndustryAnalyst()
        for ticker in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]:
            result = analyst._resolve_ticker(ticker)
            # All should resolve via static mapping
            assert result["found"] is True


class TestIndustryAnalystTickerResolution:
    """Test ticker-to-CIK resolution."""

    def test_known_ticker_resolves(self):
        """Known tickers resolve via static mapping."""
        analyst = IndustryAnalyst()
        result = analyst._resolve_ticker("AAPL")

        assert result["found"] is True
        assert result["cik"] == 320193
        assert result["company_name"] == "Apple Inc."

    def test_unknown_ticker_offline(self):
        """Unknown ticker with network disabled returns not-found."""
        analyst = IndustryAnalyst()
        result = analyst._resolve_ticker("UNKNOWN123")

        assert result["found"] is False
        assert result["cik"] is None
        assert result["company_name"] is None

    def test_tsla_cik(self):
        """TSLA resolves to correct CIK and company name."""
        analyst = IndustryAnalyst()
        result = analyst._resolve_ticker("TSLA")

        assert result["found"] is True
        assert result["cik"] == 1318605
        assert result["company_name"] == "Tesla Inc."

    def test_nvda_cik(self):
        """NVDA resolves to correct CIK and company name."""
        analyst = IndustryAnalyst()
        result = analyst._resolve_ticker("NVDA")

        assert result["found"] is True
        assert result["cik"] == 1045810
        assert result["company_name"] == "NVIDIA Corporation"


class TestIndustryAnalystAnalysis:
    """Test the analyze method."""

    async def test_analyze_with_known_ticker(self):
        """IndustryAnalyst.analyze works with known ticker."""
        analyst = IndustryAnalyst()
        result = await analyst.analyze("AAPL", "Test industry question")

        assert "company_ticker" in result
        assert result["company_ticker"] == "AAPL"
        assert "executive_summary" in result
        assert "findings" in result

    async def test_analyze_unknown_ticker(self):
        """IndustryAnalyst.analyze with unknown ticker."""
        analyst = IndustryAnalyst()
        result = await analyst.analyze("UNKNOWN123", "Test?")

        assert result["company_ticker"] == "UNKNOWN123"
        assert result["evidence_preserved"] is False
        assert "explicit_limitations" in result

    async def test_analyze_with_network_enabled(self):
        """IndustryAnalyst.analyze with allow_network=True."""
        analyst = IndustryAnalyst(allow_network=True)
        result = await analyst.analyze("AAPL", "Test?")

        assert "company_ticker" in result
        assert result["company_ticker"] == "AAPL"


class TestIndustryAnalystReportModel:
    """Test ResearchReport pydantic model."""

    async def test_research_report_creation(self):
        """ResearchReport can be created with all fields."""
        analyst = IndustryAnalyst()
        result = await analyst.analyze("AAPL", "Test?")

        assert "report_timestamp" in result
        assert "executive_summary" in result
        assert "findings" in result
        assert "explicit_limitations" in result
        assert "evidence_preserved" in result


class TestIndustryAnalystFindingModel:
    """Test AnalysisFinding pydantic model."""

    def test_finding_creation(self):
        """AnalysisFinding can be created with all fields."""
        from fris.agents.industry import AnalysisFinding

        finding = AnalysisFinding(
            category="reported_fact",
            claim="Apple designs smartphones",
            evidence="iPhone sales data",
            source_url="https://www.apple.com",
            filing_type="10-K",
            filing_date="2023-11-02",
            accession_number="0000320193-23-000069",
            section="1",
            confidence=0.9,
        )
        assert finding.category == "reported_fact"
        assert finding.claim == "Apple designs smartphones"
        assert finding.evidence == "iPhone sales data"
        assert finding.filing_type == "10-K"
        assert finding.confidence == 0.9

    def test_finding_with_minimal_fields(self):
        """AnalysisFinding works with minimal required fields."""
        from fris.agents.industry import AnalysisFinding

        finding = AnalysisFinding(
            category="unknown",
            claim="Insufficient evidence",
        )
        assert finding.category == "unknown"
        assert finding.claim == "Insufficient evidence"
        assert finding.limitations is None
