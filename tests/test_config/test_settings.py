"""Tests for FRIS application settings configuration."""

from fris.config.settings import Settings, get_settings


class TestSettingsInitialization:
    """Test that settings initialize correctly."""

    def test_default_settings(self):
        """Default settings have proper values."""
        settings = Settings()
        assert settings.llm_provider == "mock"
        assert settings.testing is False
        assert settings.sec_user_agent == "FRIS research example.com"
        assert settings.sec_edgar_rate_limit == 5.0
        assert settings.sec_edgar_timeout_seconds == 30

    def test_custom_user_agent(self):
        """Custom User-Agent can be configured."""
        settings = Settings(sec_user_agent="MyCompany research@example.com")
        assert settings._get_sec_user_agent() == "MyCompany research@example.com"

    def test_default_model(self):
        """Default mock model is set."""
        settings = Settings()
        assert settings.mock_model == "claude-sonnet-4-20250514"

    def test_provider_validation(self):
        """Provider validation works correctly."""
        # Mock provider should be valid
        Settings(llm_provider="mock")
        # Should not raise

    def test_testing_mode(self):
        """Testing mode can be enabled."""
        settings = Settings(testing=True)
        assert settings.testing is True


class TestGetSettings:
    """Test the get_settings cached function."""

    def test_returns_settings_instance(self):
        """get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_cached(self):
        """get_settings returns the same instance."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
