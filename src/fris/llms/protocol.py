"""Provider-agnostic LLM protocol interface.

This module defines the protocol for LLM communication, ensuring that
the agent code is independent of any particular LLM provider. All LLM
interactions go through this interface, never provider-specific SDKs.

The protocol supports both real API calls (when configured) and mock
responses (for testing and offline mode).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message in the conversation."""

    role: str = Field(..., description="Role of the message sender (system, user, assistant)")
    content: str = Field(..., description="The message content")


class ChatCompletionRequest(BaseModel):
    """A request to complete a chat conversation."""

    model_config = {"arbitrary_types_allowed": True}

    messages: list[ChatMessage] = Field(..., description="The conversation messages")
    model: str = Field(description="The LLM model to use")
    temperature: float = Field(0.0, description="Sampling temperature (0.0 to 1.0)")
    max_tokens: int | None = Field(None, description="Maximum number of tokens to generate")
    system_prompt: str | None = Field(None, description="Optional system prompt to prepend")
    extra: dict[str, Any] = Field(default_factory=dict, description="Extra parameters for the API")


class ChatCompletionResponse(BaseModel):
    """A response from the LLM completion."""

    model_config = {"arbitrary_types_allowed": True}

    choices: list[dict[str, Any]] = Field(..., description="The response choices")
    usage: dict[str, Any] | None = Field(None, description="Token usage information")
    id: str | None = Field(None, description="Request ID")
    object: str | None = Field(None, description="Object type identifier")


class InferenceClient(ABC):
    """Abstract base class for LLM inference clients.

    Subclasses must implement the achat method to send chat completion requests.
    """

    @abstractmethod
    async def achat(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Send a chat completion request.

        Args:
            request: The chat completion request

        Returns:
            The LLM response
        """
        ...  # pragma: no cover
