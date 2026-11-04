"""Tests for the provider-agnostic LLM protocol interface."""

from fris.llms.protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    InferenceClient,
)


class TestChatMessage:
    """Test ChatMessage model."""

    def test_basic_creation(self):
        """ChatMessage can be created with required fields."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_with_all_fields(self):
        """ChatMessage with optional system prompt."""
        msg = ChatMessage(
            role="system",
            content="You are helpful",
            name="Assistant",
        )
        assert msg.role == "system"
        assert msg.content == "You are helpful"


class TestChatCompletionRequest:
    """Test ChatCompletionRequest model."""

    def test_basic_creation(self):
        """ChatCompletionRequest with minimal fields."""
        msg = ChatMessage(role="user", content="Hello")
        request = ChatCompletionRequest(messages=[msg], model="test-model")
        assert request.model == "test-model"
        assert len(request.messages) == 1

    def test_with_temperature_and_max_tokens(self):
        """ChatCompletionRequest with temperature and max_tokens."""
        msg = ChatMessage(role="user", content="Hello")
        request = ChatCompletionRequest(
            messages=[msg],
            model="test-model",
            temperature=0.5,
            max_tokens=100,
        )
        assert request.temperature == 0.5
        assert request.max_tokens == 100

    def test_system_prompt(self):
        """ChatCompletionRequest with system prompt."""
        msg_user = ChatMessage(role="user", content="Hello")
        msg_system = ChatMessage(role="system", content="You are helpful")
        request = ChatCompletionRequest(
            messages=[msg_system, msg_user],
            model="test-model",
            system_prompt="You are a helpful assistant",
        )
        assert len(request.messages) == 2


class TestChatCompletionResponse:
    """Test ChatCompletionResponse model."""

    def test_basic_creation(self):
        """ChatCompletionResponse can be created."""
        response = ChatCompletionResponse(
            choices=[{"message": {"role": "assistant", "content": "Hi"}}]
        )
        assert len(response.choices) == 1


class TestInferenceClient:
    """Test InferenceClient ABC."""

    def test_abstract_method(self):
        """InferenceClient defines abstract achat method."""
        assert InferenceClient is not None

    def test_mock_client_implementation(self):
        """MockClient implements the InferenceClient interface."""
        from fris.llms.mock import MockClient

        client = MockClient()
        assert hasattr(client, "achat")
        assert hasattr(client, "aclose")

    async def test_mock_chat(self):
        """MockClient returns deterministic response."""
        from fris.llms.mock import MockClient

        client = MockClient()
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="test-model",
        )
        response = await client.achat(request)
        assert response is not None
        assert hasattr(response, "content")
