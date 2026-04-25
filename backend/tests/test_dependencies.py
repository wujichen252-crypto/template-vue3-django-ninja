"""Test that all required dependencies are installed correctly."""
import os
import pytest


class TestDependencies:
    """Test cases for dependency imports."""

    def test_core_dependencies(self):
        """Test that core dependencies can be imported."""
        # Set DJANGO_SETTINGS_MODULE to avoid import issues
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
        
        # Django and related
        import django
        import psycopg2
        import redis
        import jwt  # pyjwt is imported as jwt
        import pydantic
        import dotenv
        import bcrypt
        import django_redis
        import django_ratelimit

        # Verify versions (optional)
        assert django.VERSION[0] >= 5

    def test_development_dependencies(self):
        """Test that development dependencies can be imported."""
        import pytest
        import pytest_django
        import pytest_cov
        import factory
        import freezegun
        import ruff

        # Verify ruff is available
        assert hasattr(ruff, "find_ruff_bin")

    def test_optional_dependencies(self):
        """Test that optional dependencies can be imported when installed."""
        try:
            import gunicorn
            import whitenoise
            assert gunicorn.__version__ >= "21.2"
            assert whitenoise.__version__ >= "6.6"
        except ImportError:
            # Optional dependencies might not be installed in dev environment
            pass

    def test_django_settings(self):
        """Test that Django settings can be loaded."""
        import os
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
        from django.conf import settings

        assert settings.SECRET_KEY is not None
        assert "django.contrib.auth" in settings.INSTALLED_APPS

    def test_ninja_router(self):
        """Test that Django Ninja router can be initialized."""
        import os
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
        from ninja import NinjaAPI

        api = NinjaAPI()
        assert api is not None
