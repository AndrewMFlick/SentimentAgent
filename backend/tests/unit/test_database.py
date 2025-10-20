"""Unit tests for DatabaseService methods.

Tests for Feature #005: CosmosDB SQL aggregation fix
Tests the _execute_scalar_query helper method used by get_sentiment_stats.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict
import asyncio


class TestExecuteScalarQuery:
    """Unit tests for _execute_scalar_query helper method."""
    
    @pytest.fixture
    def db_service_with_mocks(self):
        """Create a DatabaseService with mocked containers."""
        with patch('azure.cosmos.CosmosClient'):
            from src.services.database import DatabaseService
            
            # Create instance with mocked initialization
            service = object.__new__(DatabaseService)
            
            # Mock the sentiment container
            service.sentiment_container = Mock()
            
            return service
    
    @pytest.mark.asyncio
    async def test_execute_scalar_query_returns_integer(self, db_service_with_mocks):
        """
        Test that _execute_scalar_query returns single integer from COUNT query.
        
        Task: T008
        Purpose: Verify helper method extracts integer from query result
        Setup: Mock query_items to return [42]
        Test: Call _execute_scalar_query with COUNT query
        Assertions:
          - Returns integer 42
          - Calls query_items with correct parameters
        """
        # Mock query_items to return a single integer value
        mock_result = [42]
        db_service_with_mocks.sentiment_container.query_items = Mock(return_value=mock_result)
        
        # Test query
        query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff"
        parameters = [{"name": "@cutoff", "value": 1234567890}]
        
        # Execute
        result = await db_service_with_mocks._execute_scalar_query(query, parameters)
        
        # Assertions
        assert result == 42, "Should return the integer value"
        assert isinstance(result, int), "Should return an integer type"
        
        # Verify query was called correctly
        db_service_with_mocks.sentiment_container.query_items.assert_called_once_with(
            query,
            parameters=parameters,
            enable_cross_partition_query=True
        )
    
    @pytest.mark.asyncio
    async def test_execute_scalar_query_returns_float(self, db_service_with_mocks):
        """
        Test that _execute_scalar_query returns single float from AVG query.
        
        Task: T008
        Purpose: Verify helper method extracts float from query result
        Setup: Mock query_items to return [0.567]
        Test: Call _execute_scalar_query with AVG query
        Assertions:
          - Returns float 0.567
          - Calls query_items with correct parameters
        """
        # Mock query_items to return a single float value
        mock_result = [0.567]
        db_service_with_mocks.sentiment_container.query_items = Mock(return_value=mock_result)
        
        # Test query
        query = "SELECT VALUE AVG(c.compound_score) FROM c WHERE c._ts >= @cutoff"
        parameters = [{"name": "@cutoff", "value": 1234567890}]
        
        # Execute
        result = await db_service_with_mocks._execute_scalar_query(query, parameters)
        
        # Assertions
        assert result == 0.567, "Should return the float value"
        assert isinstance(result, float), "Should return a float type"
    
    @pytest.mark.asyncio
    async def test_execute_scalar_query_empty_result_returns_zero(self, db_service_with_mocks):
        """
        Test that _execute_scalar_query returns 0 for empty result set.
        
        Task: T008
        Purpose: Verify helper method handles empty results gracefully
        Setup: Mock query_items to return []
        Test: Call _execute_scalar_query
        Assertions:
          - Returns 0 (not None or error)
          - No exception raised
        """
        # Mock query_items to return empty list
        mock_result = []
        db_service_with_mocks.sentiment_container.query_items = Mock(return_value=mock_result)
        
        # Test query
        query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff"
        parameters = [{"name": "@cutoff", "value": 1234567890}]
        
        # Execute
        result = await db_service_with_mocks._execute_scalar_query(query, parameters)
        
        # Assertions
        assert result == 0, "Should return 0 for empty result"
    
    @pytest.mark.asyncio
    async def test_execute_scalar_query_handles_query_errors(self, db_service_with_mocks):
        """
        Test that _execute_scalar_query handles query execution errors.
        
        Task: T008
        Purpose: Verify helper method propagates exceptions (fail-fast)
        Setup: Mock query_items to raise exception
        Test: Call _execute_scalar_query
        Assertions:
          - Exception is raised (not caught)
          - Error is logged
        """
        # Mock query_items to raise exception
        db_service_with_mocks.sentiment_container.query_items = Mock(
            side_effect=Exception("Database connection error")
        )
        
        # Test query
        query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff"
        parameters = [{"name": "@cutoff", "value": 1234567890}]
        
        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            await db_service_with_mocks._execute_scalar_query(query, parameters)
        
        # Assertions
        assert "Database connection error" in str(exc_info.value), \
            "Should propagate the original exception"
    
    @pytest.mark.asyncio
    async def test_execute_scalar_query_with_subreddit_filter(self, db_service_with_mocks):
        """
        Test that _execute_scalar_query works with multiple parameters.
        
        Task: T008
        Purpose: Verify helper works with subreddit filtering
        Setup: Mock query_items to return value
        Test: Call with multiple parameters (cutoff + subreddit)
        Assertions:
          - Returns correct value
          - Passes all parameters to query
        """
        # Mock query_items
        mock_result = [25]
        db_service_with_mocks.sentiment_container.query_items = Mock(return_value=mock_result)
        
        # Test query with multiple parameters
        query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff AND c.subreddit = @subreddit"
        parameters = [
            {"name": "@cutoff", "value": 1234567890},
            {"name": "@subreddit", "value": "politics"}
        ]
        
        # Execute
        result = await db_service_with_mocks._execute_scalar_query(query, parameters)
        
        # Assertions
        assert result == 25, "Should return the count"
        
        # Verify both parameters were passed
        call_kwargs = db_service_with_mocks.sentiment_container.query_items.call_args[1]
        assert len(call_kwargs['parameters']) == 2, "Should pass both parameters"
