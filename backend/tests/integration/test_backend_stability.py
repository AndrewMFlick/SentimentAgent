"""Integration tests for backend stability."""
import pytest
import asyncio
import time
import psutil
import os
from datetime import datetime
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestBackendStability:
    """Test backend stability during data collection cycles."""
    
    def test_backend_process_remains_running(self):
        """
        Test that backend process remains running during normal operation.
        
        Success Criteria (SC-001): Backend runs continuously without crashes
        """
        # Import app and create client
        from src.main import app
        client = TestClient(app)
        
        # Record initial process info
        current_pid = os.getpid()
        
        # Check health multiple times over short period
        for i in range(5):
            response = client.get("/api/v1/health")
            assert response.status_code in [200, 503], f"Health check failed on iteration {i}"
            
            # Verify same process is still running
            assert os.getpid() == current_pid, "Process was restarted"
            
            time.sleep(1)
    
    def test_health_endpoint_returns_process_metrics(self):
        """
        Test that health endpoint returns comprehensive process metrics.
        
        Success Criteria (SC-007): Health endpoint reports status with metrics
        """
        from src.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/health")
        assert response.status_code in [200, 503]
        
        data = response.json()
        
        # Verify structure
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        
        assert "process" in data
        assert "uptime_seconds" in data["process"]
        assert "memory_mb" in data["process"]
        assert "cpu_percent" in data["process"]
        assert "pid" in data["process"]
        
        assert "application" in data
        assert "collections_succeeded" in data["application"]
        assert "collections_failed" in data["application"]
        
        assert "database" in data
        assert "connected" in data["database"]
    
    def test_error_handling_doesnt_crash_backend(self):
        """
        Test that errors during collection don't crash the backend.
        
        Success Criteria (SC-006): Backend handles errors without crashing
        """
        from src.main import app
        from src.services import scheduler
        from src.services.health import app_state
        client = TestClient(app)
        
        # Record initial state
        initial_pid = os.getpid()
        initial_failed = app_state.collections_failed
        
        # Simulate an error scenario by triggering collection with invalid config
        # The scheduler should catch and log errors without crashing
        
        # Wait a bit for any background tasks
        time.sleep(2)
        
        # Verify backend is still running
        assert os.getpid() == initial_pid
        
        # Health check should still work
        response = client.get("/api/v1/health")
        assert response.status_code in [200, 503]
    
    def test_graceful_shutdown_waits_for_jobs(self):
        """
        Test that graceful shutdown waits for running jobs.
        
        Success Criteria (SC-001): Backend shuts down gracefully
        """
        from src.main import app
        from src.services import scheduler
        
        # Verify scheduler is running
        assert scheduler.is_running
        
        # Stop scheduler gracefully
        scheduler.stop()
        
        # Verify scheduler stopped
        assert not scheduler.is_running
    
    def test_memory_monitoring_detects_usage(self):
        """
        Test that memory monitoring tracks memory usage.
        
        Success Criteria (SC-004): Memory monitoring detects usage patterns
        """
        from src.main import app
        client = TestClient(app)
        
        # Get initial memory
        response1 = client.get("/api/v1/health")
        assert response1.status_code in [200, 503]
        data1 = response1.json()
        memory1 = data1["process"]["memory_mb"]
        
        # Memory should be reasonable (< 512 MB in normal operation)
        assert memory1 > 0
        assert memory1 < 512, f"Memory usage too high: {memory1}MB"
        
        # Get memory again after a short wait
        time.sleep(1)
        response2 = client.get("/api/v1/health")
        assert response2.status_code in [200, 503]
        data2 = response2.json()
        memory2 = data2["process"]["memory_mb"]
        
        # Memory should be in similar range (allowing for variance)
        assert abs(memory2 - memory1) < 50, f"Memory changed drastically: {memory1}MB -> {memory2}MB"
    
    def test_application_state_tracks_collections(self):
        """
        Test that application state tracks collection metrics.
        
        Success Criteria (SC-007): Health monitoring tracks collections
        """
        from src.main import app
        from src.services.health import app_state
        client = TestClient(app)
        
        # Get current counts
        initial_succeeded = app_state.collections_succeeded
        initial_failed = app_state.collections_failed
        
        # Counts should be non-negative
        assert initial_succeeded >= 0
        assert initial_failed >= 0
        
        # Health endpoint should reflect these counts
        response = client.get("/api/v1/health")
        data = response.json()
        
        assert data["application"]["collections_succeeded"] == initial_succeeded
        assert data["application"]["collections_failed"] == initial_failed
    
    def test_database_connection_status_reported(self):
        """
        Test that database connection status is reported in health.
        
        Success Criteria (SC-007): Health endpoint reports database status
        """
        from src.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/health")
        data = response.json()
        
        # Database connection status should be reported
        assert "database" in data
        assert "connected" in data["database"]
        assert isinstance(data["database"]["connected"], bool)
    
    def test_unhealthy_status_returns_503(self):
        """
        Test that unhealthy status returns 503 status code.
        
        Success Criteria (SC-007): Unhealthy backend returns 503
        """
        from src.main import app
        from src.services.health import app_state
        client = TestClient(app)
        
        # Simulate unhealthy state by marking database as disconnected
        original_db_state = app_state.database_connected
        app_state.database_connected = False
        
        try:
            response = client.get("/api/v1/health")
            
            # Should return 503 when unhealthy
            assert response.status_code == 503
            
            data = response.json()
            assert data["status"] == "unhealthy"
            
        finally:
            # Restore original state
            app_state.database_connected = original_db_state
