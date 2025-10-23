"""Pytest configuration for all tests.

This file provides common fixtures and configuration for unit and integration tests.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture(scope="session", autouse=True)
def mock_cosmos_client():
    """Mock CosmosClient for all tests to avoid database connection attempts.
    
    This prevents tests from trying to connect to CosmosDB during import/initialization.
    Individual tests can override this by creating their own more specific mocks.
    """
    with patch('azure.cosmos.CosmosClient') as mock_client:
        # Create a mock that returns mock containers
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Mock database and container methods
        mock_database = MagicMock()
        mock_instance.get_database_client.return_value = mock_database
        
        mock_container = MagicMock()
        mock_database.get_container_client.return_value = mock_container
        
        yield mock_client
