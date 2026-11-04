"""Mock LLM client for testing and development.

This module provides a MockClient that can be used for testing without
making actual LLM API calls. It returns deterministic mock responses
that are useful for unit testing the agent logic.

MockClient now inherits from InferenceClient to maintain type compatibility.
"""

from __future__ import annotations

from typing import Any

from fris.llms.protocol import InferenceClient


class MockClient(InferenceClient):
    """A mock LLM client that returns deterministic responses for testing.

    All interactions through MockClient are local and make no external API calls.
    This is the default LLM client for both FundamentalsAnalyst and IndustryAnalyst
    when allow_network=False (the default).

    Network Authorization:
    - MockClient makes zero HTTP requests by design
    - It is the default LLM client for both analysts
    - Used when explicit SEC network access is not required
    """

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        """Initialize the MockClient.

        Args:
            model: Model name (used for identification only, not for actual API calls)
        """
        self.model = model
        super().__init__()

    async def achat(self, prompt: Any) -> Any:
        """Send a chat prompt and return a mock response.

        This method makes no external API calls. It returns a deterministic
        mock response based on the prompt content.

        Args:
            prompt: The chat completion request (messages, model, etc.)

        Returns:
            A mock response object with a .content attribute
        """
        # Extract the user message content for determining the response
        content = ""
        if hasattr(prompt, "messages"):
            for msg in prompt.messages:
                if msg.role == "user":
                    content = msg.content if hasattr(msg, "content") else ""
                    break

        # Determine response based on prompt content
        content_lower = content.lower() if content else ""

        if "unknown" in content_lower:
            response_text = '{"category": "unknown", "claim": "Unknown, insufficient evidence", "limitations": "No evidence provided", "evidence": null, "finding_type": "unknown", "source_url": null, "filing_type": null, "filing_date": null, "accession_number": null, "section": "1, 7", "confidence": null}'
        elif "reported fact" in content_lower or "fact:" in content_lower:
            response_text = '{"category": "reported_fact", "claim": "Reported fact from evidence", "limitations": "Based on extracted filing sections only", "evidence": null, "finding_type": "reported_fact", "source_url": null, "filing_type": null, "filing_date": null, "accession_number": null, "section": "1, 7", "confidence": null}'
        elif "management" in content_lower:
            response_text = '{"category": "interpretation", "claim": "Management commentary analysis", "limitations": "Based on Item 7 (MD&A) extraction only", "evidence": null, "finding_type": "interpretation", "source_url": null, "filing_type": null, "filing_date": null, "accession_number": null, "section": "7", "confidence": null}'
        else:
            response_text = '{"category": "interpretation", "claim": "Analysis based on available evidence", "limitations": "Items 1 and 7 only; does not encompass full financial statement analysis", "evidence": null, "finding_type": "interpretation", "source_url": null, "filing_type": null, "filing_date": null, "accession_number": null, "section": "1, 7", "confidence": null}'

        # Return a mock response object
        class _MockResponse:
            content = response_text

        return _MockResponse()

    async def aclose(self) -> None:
        """Close the mock client (no-op since there's no connection)."""
        pass