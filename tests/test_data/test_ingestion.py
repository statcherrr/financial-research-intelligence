"""Tests for the filing document ingestion and section extraction layer."""

from fris.data.edgar_ingestion import _ITEMS_OF_INTEREST, extract_sections_from_filing


class TestItemsOfInterest:
    """Test the items of interest constant."""

    def test_items_defined(self):
        """_ITEMS_OF_INTEREST contains expected item numbers."""
        # Should contain at least Items 1, 7, and other relevant items
        assert "1" in _ITEMS_OF_INTEREST
        assert "7" in _ITEMS_OF_INTEREST


class TestSectionExtraction:
    """Test section extraction from filings."""

    async def test_extract_sections_from_filing(self):
        """extract_sections_from_filing works with sample filing."""
        # Create a minimal filing record
        from fris.data.models import FilingRecord

        filing = FilingRecord(
            accession_number="0000320193-23-000069",
            cik=320193,
            company_name="Apple Inc.",
            form_type="10-K",
            filing_date="2023-11-02",
            period_of_report="2023-09-30",
            primary_document=None,
            documents=[],
            accession_url="https://www.sec.gov/edgar",
            primary_document_url=None,
            raw_metadata={},
        )

        # Extract sections - this uses the ingestion layer
        results = await extract_sections_from_filing(filing)

        # Should return a dict mapping item numbers to extracted text
        assert isinstance(results, dict)

    async def test_extract_sections_empty_filing(self):
        """extract_sections_from_filing handles empty filing gracefully."""
        from fris.data.models import FilingRecord

        filing = FilingRecord(
            accession_number="0000320193-23-000069",
            cik=320193,
            company_name="Apple Inc.",
            form_type="10-K",
            filing_date="2023-11-02",
            period_of_report="2023-09-30",
            primary_document=None,
            documents=[],
            accession_url="https://www.sec.gov/edgar",
            primary_document_url=None,
            raw_metadata={},
        )

        results = await extract_sections_from_filing(filing)
        assert results is not None


class TestExtractedSectionModel:
    """Test ExtractedSection pydantic model."""

    def test_basic_extracted_section(self):
        """ExtractedSection can be created with required fields."""
        from fris.data.models import ExtractedSection

        section = ExtractedSection(
            item_number="1",
            title="Business",
            text="Apple Inc. designs, makes, and sells...",
            source_url="https://www.sec.gov/edgar",
            filing_date="2023-11-02",
            accession_number="0000320193-23-000069",
        )
        assert section.item_number == "1"
        assert section.title == "Business"
        assert "Apple" in section.text


class TestExtractedFilingModel:
    """Test ExtractedFiling pydantic model."""

    def test_basic_extracted_filing(self):
        """ExtractedFiling can be created with required fields."""
        from datetime import date

        from fris.data.models import ExtractedFiling, FilingRecord

        filing_record = FilingRecord(
            accession_number="0000320193-23-000069",
            cik=320193,
            company_name="Apple Inc.",
            form_type="10-K",
            filing_date=date(2023, 11, 2),
            period_of_report=date(2023, 9, 30),
            primary_document=None,
            documents=[],
            accession_url="https://www.sec.gov/edgar",
            primary_document_url=None,
            raw_metadata={},
        )
        filing = ExtractedFiling(
            filing=filing_record,
            sections={},
        )
        assert filing.filing.accession_number == "0000320193-23-000069"
        assert filing.filing.company_name == "Apple Inc."
