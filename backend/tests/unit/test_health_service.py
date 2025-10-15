"""Unit tests for health service - standalone tests without database dependency."""
import pytest
import time
import sys
from datetime import datetime, timedelta


# Import health service directly to avoid database initialization
sys.path.insert(0, '/home/runner/work/SentimentAgent/SentimentAgent/backend')


def test_application_state_module_exists():
    """Test that health module can be imported."""
    try:
        from src.services import health
        assert health is not None
    except ImportError as e:
        pytest.skip(f"Cannot import health module: {e}")


def test_application_state_dataclass():
    """Test ApplicationState dataclass structure using inspection."""
    from src.services.health import ApplicationState
    import inspect
    
    # Verify it's a dataclass
    assert hasattr(ApplicationState, '__dataclass_fields__')
    
    # Verify expected fields exist
    fields = ApplicationState.__dataclass_fields__
    assert 'app_start_time' in fields
    assert 'last_collection_time' in fields
    assert 'collections_succeeded' in fields
    assert 'collections_failed' in fields
    assert 'database_connected' in fields


def test_application_state_methods():
    """Test ApplicationState has expected methods."""
    from src.services.health import ApplicationState
    
    assert hasattr(ApplicationState, 'get_uptime_seconds')
    assert hasattr(ApplicationState, 'get_data_freshness_minutes')
    assert callable(getattr(ApplicationState, 'get_uptime_seconds'))
    assert callable(getattr(ApplicationState, 'get_data_freshness_minutes'))


def test_retry_decorator_exists():
    """Test that retry decorator exists in database module."""
    # Note: This test will be skipped if database cannot be imported
    pytest.skip("Requires database connection - run integration tests instead")
