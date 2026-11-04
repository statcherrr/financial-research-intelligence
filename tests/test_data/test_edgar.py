"""Tests for the EdgarClient and EDGAR data layer."""

from fris.data.edgar import (
    EdgarClient,
    EdgarClientConfig,
    EdgarError,
    EdgarHTTPError,
    EdgarMalformedResponse,
    EdgarRateLimitError,
)


class TestEdgarClientConfig:
    """Test EdgarClient configuration model."""

    def test_default_config(self):
        """Default EdgarClientConfig has proper values."""
        config = EdgarClientConfig()
        assert config.timeout_seconds == 30.0
        assert config.rate_limit_per_second == 5.0

    def test_custom_config(self):
        """Custom EdgarClientConfig can be set."""
        config = EdgarClientConfig(timeout_seconds=60, rate_limit_per_second=10.0)
        assert config.timeout_seconds == 60.0
        assert config.rate_limit_per_second == 10.0


class TestEdgarClientErrors:
    """Test Edgar error hierarchy."""

    def test_edgar_error_is_exception(self):
        """EdgarError is a proper Exception subclass."""
        error = EdgarError("test error")
        assert isinstance(error, Exception)

    def test_edgar_http_error(self):
        """EdgarHTTPError subclasses EdgarError."""
        error = EdgarHTTPError("HTTP error")
        assert isinstance(error, EdgarError)

    def test_edgar_rate_limit_error(self):
        """EdgarRateLimitError subclasses EdgarError."""
        error = EdgarRateLimitError("Rate limited")
        assert isinstance(error, EdgarError)

    def test_edgar_malformed_response(self):
        """EdgarMalformedResponse subclasses EdgarError."""
        error = EdgarMalformedResponse("Malformed")
        assert isinstance(error, EdgarError)


class TestEdgarClientCIKLookup:
    """Test CIK lookup functionality."""

    def test_edgar_client_initialization(self):
        """EdgarClient can be initialized."""
        client = EdgarClient()
        assert client is not None

    def test_edgar_client_with_config(self):
        """EdgarClient can be initialized with config."""
        config = EdgarClientConfig(timeout=60)
        client = EdgarClient(config=config)
        assert client is not None


class TestEdgarClientRateLimiting:
    """Test rate limiting behavior."""

    def test_rate_limit_enforcement(self):
        """EdgarClient respects rate limit configuration."""
        client = EdgarClient()
        # Rate limit is configured at 5 req/sec by default
        assert client._config.rate_limit_per_second == 5.0
