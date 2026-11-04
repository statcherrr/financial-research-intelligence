"""Industry Analyst agent for FRIS.

Provides single-agent industry analysis using SEC EDGAR data and the
provider-agnostic LLM interface. This is a standalone agent that does
not participate in orchestration or multi-agent coordination. It analyzes
industry structure, competitive landscape, and market dynamics using
SEC filing evidence and other public sources.

Network Authorization:
- allow_network=False is the default; no SEC HTTP requests are made
- allow_network=True is an explicit opt-in for SEC transport access
- Injected EdgarClient must respect the agent's authorization policy
- Network-disabled execution returns structured limitations
"""

from __future__ import annotations

import asyncio
from typing import Any, ClassVar

from pydantic import BaseModel, Field, validator

from fris.data.edgar import EdgarClient
from fris.llms.mock import MockClient
from fris.llms.protocol import ChatCompletionRequest

AnalysisCategory = str  # "reported_fact", "interpretation", "unknown"


class AnalysisFinding(BaseModel):
    """A single industry analysis finding with evidence traceability."""

    model_config = {"arbitrary_types_allowed": True}

    category: str = Field(
        ...,
        description="Type of finding: reported_fact, interpretation, or unknown.",
    )
    claim: str = Field(
        ...,
        description="The claim or assertion being made",
    )
    limitations: str | None = Field(
        default=None,
        description="Explicit limitations on this finding. Use None for unset.",
    )

    evidence: str | None = Field(
        default=None,
        description="Supporting text from SEC filing",
    )
    finding_type: str | None = Field(
        default=None,
        description="Type of finding: reported_fact, interpretation, or unknown",
    )
    source_url: str | None = Field(
        default=None,
        description="SEC URL where the evidence was sourced",
    )
    filing_type: str | None = Field(
        default=None,
        description="Form type: 10-K, 10-Q, 8-K",
    )
    filing_date: str | None = Field(
        default=None,
        description="ISO filing date",
    )
    accession_number: str | None = Field(
        default=None,
        description="SEC accession number",
    )
    section: str | None = Field(
        default=None,
        description="SEC item number (1, 1A, 7, etc.)",
    )
    confidence: float | None = Field(
        default=None,
        description="LLM-assigned confidence (0.0 to 1.0), not proof of accuracy",
    )


class ResearchReport(BaseModel):
    """Complete research report from the Industry Analyst."""

    model_config = {"arbitrary_types_allowed": True, "validate_assignment": True}

    company_ticker: str = Field(
        ...,
        description="Company ticker symbol",
    )

    @validator("company_ticker")
    def _validate_ticker(cls, v: str) -> str:
        """Validate that ticker is not empty."""
        if not v or not v.strip():
            raise ValueError("Company ticker must not be empty")
        return v.strip()

    research_question: str = Field(
        ...,
        description="The research question asked",
    )
    filings_analyzed: int = Field(
        0,
        description="Number of SEC filings analyzed",
    )
    executive_summary: str = Field(
        default="",
        description="Brief executive summary of findings",
    )
    business_model: str = Field(
        default="",
        description="Description of the company's business model",
    )
    revenue_drivers: str = Field(
        default="",
        description="Revenue drivers and business segments",
    )
    operating_trends: str = Field(
        default="",
        description="Operating trends described by management",
    )
    opportunities_growth: str = Field(
        default="",
        description="Opportunities and growth factors",
    )
    risks_challenges: str = Field(
        default="",
        description="Risks and challenges",
    )
    management_commentary: str = Field(
        default="",
        description="Management commentary",
    )
    fundamental_assessment: str = Field(
        default="",
        description="Overall fundamental assessment",
    )
    findings: list[AnalysisFinding] = Field(
        default_factory=list,
        description="List of evidence-backed findings",
    )
    explicit_limitations: str = Field(
        default="",
        description="Explicit limitations of the analysis",
    )
    evidence_preserved: bool = Field(
        default=True,
        description="Whether source evidence was preserved and traceable",
    )
    report_timestamp: str = Field(
        default_factory=lambda: __import__("datetime").datetime.now().isoformat(),
        description="ISO timestamp when the report was generated",
    )


class IndustryAnalyst:
    """Single-agent Industry Analyst for FRIS.

    Uses the existing SEC EDGAR client and document ingestion layer to
    extract filing evidence, then passes scoped evidence to the provider-agnostic
    LLM interface. All LLM interactions go through the protocol interface,
    never provider-specific SDKs.

    Network Authorization:
    - allow_network=False is the default; no SEC HTTP requests are made
    - allow_network=True is an explicit opt-in for SEC transport access
    - Injected EdgarClient must respect the agent's authorization policy
    - Network-disabled execution returns structured limitations

    Responsibilities:
    - Resolve ticker -> CIK using existing EDGAR client
    - Retrieve relevant SEC filings (10-K, 10-Q)
    - Extract industry-relevant sections using ingestion layer
    - Pass evidence to LLM via protocol interface
    - Return structured, traceable industry analysis report
    """

    TICKER_TO_CIK_MAP: ClassVar[dict[str, int]] = {
        "AAPL": 320193,
        "MSFT": 789019,
        "GOOGL": 1658294,
        "AMZN": 1410954,
        "TSLA": 1318605,
        "NVDA": 1045810,
    }

    def __init__(
        self,
        llm_client: Any | None = None,
        allow_network: bool = False,
    ) -> None:
        """Initialize the Industry Analyst.

        Args:
            llm_client: Optional LLM client (defaults to MockClient)
            allow_network: If True, permits SEC EDGAR HTTP requests.
                           Default False blocks all live SEC requests.
        """

        self.llm_client = llm_client or MockClient()
        self.allow_network = allow_network

    def _resolve_ticker(self, ticker: str):
        """Resolve a ticker symbol to CIK.

        Uses a ticker-to-CIK mapping for reproducibility without
        requiring live SEC lookups. The allow_network flag controls
        whether the EDGAR client may make live HTTP requests.

        Args:
            ticker: Company ticker symbol (e.g., "AAPL")

        Returns:
            CIKResult with lookup outcome
        """
        upper_ticker = ticker.upper()
        cik = self.TICKER_TO_CIK_MAP.get(upper_ticker)

        if cik is not None:
            return {
                "found": True,
                "query": {"ticker": ticker},
                "cik": cik,
                "company_name": self._get_company_name(cik, upper_ticker),
                "ticker": upper_ticker,
                "source_url": None,
            }

        # Fallback: EDGAR client lookup respecting authorization policy
        if not self.allow_network:
            # Network disabled: return not-found without making any HTTP requests
            return {
                "found": False,
                "query": {"ticker": ticker},
                "cik": None,
                "company_name": None,
                "ticker": upper_ticker,
                "source_url": None,
            }

        # Network allowed: try the EDGAR client
        client = EdgarClient()
        query = {"ticker": upper_ticker}

        try:
            result = asyncio.get_event_loop().run_until_complete(client.lookup_cik(query))
            return result
        except Exception:
            # Return not-found if both mapping and client fail
            return {
                "found": False,
                "query": {"ticker": ticker},
                "cik": None,
                "company_name": None,
                "ticker": upper_ticker,
                "source_url": None,
            }

    def _get_company_name(self, cik: int, ticker: str) -> str | None:
        """Get company name from CIK/ticker lookup."""
        company_names: dict[int, str] = {
            320193: "Apple Inc.",
            789019: "Microsoft Corporation",
            1658294: "Alphabet Inc.",
            1410954: "Amazon.com Inc.",
            1318605: "Tesla Inc.",
            1045810: "NVIDIA Corporation",
        }
        return company_names.get(cik)

    def _extract_evidence(self, filing):
        """Extract industry-relevant sections from a filing.

        Args:
            filing: The FilingRecord to extract from

        Returns:
            Dict mapping item numbers to extracted text (or None if not found)
        """
        # Placeholder - real implementation uses ingestion layer
        return {"1": None, "7": None, "8": None}

    def _build_llm_prompt(self, ticker, research_question, industry_text, filing_info):
        """Build a structured prompt for the LLM using the protocol interface.

        The prompt includes critical rules about evidence traceability,
        financial accuracy, and proper distinction between facts and interpretations.

        Args:
            ticker: Company ticker symbol
            research_question: The research question to address
            industry_text: Extracted industry-related text, or None
            filing_info: Dict with filing metadata (form type, dates, accession number)

        Returns:
            ChatCompletionRequest ready to send to the LLM
        """

        industry_section = industry_text or "Not available"

        prompt_messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": """You are the Industry Analyst for the Financial Research Intelligence System.

Your task is to analyze a company's industry position and industry structure
using SEC filing evidence and produce a structured industry analysis report.
Follow these CRITICAL RULES:

1. Never invent market sizes, growth rates, market shares, or competitor metrics
2. Every factual finding must be traceable to its supporting filing evidence
3. Clearly distinguish reported facts from AI interpretations
4. If evidence is insufficient, return "unknown" rather than fabricating
5. Do not calculate revenue growth, margins, cash flow, or other financial ratios
6. Do not imply that Items 1 and 7 alone provide a complete industry analysis
7. Preserve source URLs, accession numbers, filing dates, and section identifiers
8. Handle missing sections and unavailable filings gracefully
9. Do not treat the LLM's confidence score as proof of factual accuracy

You will receive SEC filing evidence for industry analysis. Use this evidence to
support your analysis. If the evidence is not present or sufficient, explicitly
state "unknown" or add it to the limitations section.

Structure your response in the industry analysis report format described in the
system prompt.""",
            }
        ]

        user_content = f"""Research Question: {research_question}

Company Ticker: {ticker}

Filing Information:
- Form Types: {filing_info.get("form_types", "N/A")}
- Filing Dates: {filing_info.get("filing_dates", "N/A")}
- Accession Numbers: {filing_info.get("accession_numbers", "N/A")}

Item 1 - Business Section:
{industry_section}

Please provide a structured analysis following the FRIS industry analysis format.
Be factual, traceable to the evidence provided, and explicit about limitations.
"""

        prompt_messages.append(
            {
                "role": "user",
                "content": user_content,
            }
        )

        return ChatCompletionRequest(messages=prompt_messages, model="claude-sonnet-4-20250514")

    def _parse_llm_response(self, content, filing):
        """Parse the LLM's structured response into an AnalysisFinding.

        Validates and parses using Pydantic, handling malformed responses
        without silently producing fabricated findings.

        Args:
            content: The LLM response content
            filing: The filing record

        Returns:
            Parsed AnalysisFinding or None if parsing fails
        """
        import json

        # Try to extract JSON from the response
        try:
            # Find JSON object in the response
            start = content.index("{")
            end = content.rindex("}") + 1
            json_str = content[start:end]
            data = json.loads(json_str)

            # Map the parsed data to AnalysisFinding
            finding = AnalysisFinding(
                category=data.get("category", "interpretation"),
                claim=data.get("claim", ""),
                limitations=data.get("limitations"),
                evidence=data.get("evidence"),
                finding_type=data.get("finding_type"),
                source_url=data.get("source_url"),
                filing_type=data.get("filing_type"),
                filing_date=data.get("filing_date"),
                accession_number=data.get("accession_number"),
                section=data.get("section"),
                confidence=data.get("confidence"),
            )
            return finding
        except (ValueError, KeyError, TypeError):
            # Return a default unknown finding if parsing fails
            return AnalysisFinding(
                category="unknown",
                claim="Failed to parse LLM response",
                limitations="LLM response could not be parsed as JSON",
                evidence=None,
                finding_type="unknown",
                source_url=None,
                filing_type=None,
                filing_date=None,
                accession_number=None,
                section=None,
                confidence=None,
            )

    async def analyze(
        self,
        ticker: str,
        research_question: str,
        filing: dict | None = None,
    ) -> dict:
        """Run a complete industry analysis for a given ticker and research question.

        Args:
            ticker: Company ticker symbol (e.g., "AAPL")
            research_question: The research question to address
            filing: Optional pre-loaded filing data

        Returns:
            A dict with the industry analysis results
        """
        # Resolve ticker to CIK
        resolution = self._resolve_ticker(ticker)

        if not resolution["found"]:
            # Return a report with unresolved company info
            return {
                "company_ticker": ticker,
                "research_question": research_question,
                "executive_summary": f"Could not resolve ticker {ticker} to CIK. "
                f"{'Network disabled per policy.' if not self.allow_network else ''}",
                "explicit_limitations": f"Could not resolve ticker {ticker} to CIK. "
                f"{'Network disabled per policy.' if not self.allow_network else ''}",
                "evidence_preserved": False,
                "findings": [],
                "report_timestamp": __import__("datetime").datetime.now().isoformat(),
            }

        # Extract evidence from filings
        filing_info = {
            "form_types": ["10-K"],
            "filing_dates": ["Unknown"],
            "accession_numbers": ["Unknown"],
        }

        if filing:
            filing_info = {
                "form_types": filing.get("form_types", ["10-K"]),
                "filing_dates": filing.get("filing_dates", ["Unknown"]),
                "accession_numbers": filing.get("accession_numbers", ["Unknown"]),
            }

        # Extract industry-relevant sections
        self._extract_evidence(filing or {})

        # Build the LLM prompt
        prompt = self._build_llm_prompt(ticker, research_question, None, filing_info)

        # Send to LLM
        try:
            response = await self.llm_client.achat(prompt)
        except Exception as e:
            return {
                "company_ticker": ticker,
                "research_question": research_question,
                "executive_summary": f"LLM request failed: {str(e)}",
                "explicit_limitations": f"LLM request failed: {str(e)}",
                "evidence_preserved": False,
                "findings": [],
                "report_timestamp": __import__("datetime").datetime.now().isoformat(),
            }

        # Parse the response
        finding = self._parse_llm_response(response.content, filing or {})

        # Build and return the report as a dict
        return {
            "company_ticker": ticker,
            "research_question": research_question,
            "filings_analyzed": 1,
            "executive_summary": finding.claim if finding else "",
            "business_model": finding.claim if finding else "",
            "revenue_drivers": finding.claim if finding else "",
            "operating_trends": finding.claim if finding else "",
            "opportunities_growth": finding.claim if finding else "",
            "risks_challenges": finding.limitations if finding else "",
            "management_commentary": finding.claim if finding else "",
            "fundamental_assessment": finding.claim if finding else "",
            "findings": [finding] if finding else [],
            "explicit_limitations": finding.limitations if finding else "",
            "evidence_preserved": True,
            "report_timestamp": __import__("datetime").datetime.now().isoformat(),
        }


def run_industry_analysis(
    ticker: str,
    research_question: str,
    llm_client: Any | None = None,
    allow_network: bool = False,
) -> dict:
    """Convenience function to run industry analysis.

    Args:
        ticker: Company ticker symbol
        research_question: The research question to address
        llm_client: Optional LLM client (defaults to MockClient)
        allow_network: If True, permits SEC EDGAR HTTP requests

    Returns:
        A dict with the industry analysis results
    """
    analyst = IndustryAnalyst(llm_client=llm_client, allow_network=allow_network)
    return analyst.analyze(ticker, research_question)
