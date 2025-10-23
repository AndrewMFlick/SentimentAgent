"""Pytest configuration for all tests."""
import os
import sys
from unittest.mock import Mock, MagicMock, patch

# Set test environment variables before any imports
os.environ["REDDIT_CLIENT_ID"] = "test_client_id"
os.environ["REDDIT_CLIENT_SECRET"] = "test_client_secret"
os.environ["REDDIT_USER_AGENT"] = "TestAgent/1.0"
os.environ["COSMOS_ENDPOINT"] = "https://test.documents.azure.com:443/"
os.environ["COSMOS_KEY"] = "dGVzdF9jb3Ntb3Nfa2V5X2Zvcl91bml0X3Rlc3RzX29ubHlfbm90X3JlYWw="
os.environ["COSMOS_DATABASE"] = "test_db"
os.environ["HEALTH_CHECK_ENABLED"] = "false"
os.environ["SENTIMENT_METHOD"] = "VADER"
os.environ["USE_LLM_FOR_AMBIGUOUS"] = "false"
os.environ["LOG_LEVEL"] = "ERROR"  # Reduce noise in test output

# Mock CosmosClient before src modules are imported
mock_cosmos_client_class = MagicMock()
mock_cosmos_instance = MagicMock()
mock_database = MagicMock()
mock_container = MagicMock()

# Set up the mock chain
mock_cosmos_instance.get_database_client.return_value = mock_database
mock_database.get_container_client.return_value = mock_container

# Return the mock instance when CosmosClient is instantiated
mock_cosmos_client_class.return_value = mock_cosmos_instance

# Patch CosmosClient before it's imported by src modules
import azure.cosmos
azure.cosmos.CosmosClient = mock_cosmos_client_class

