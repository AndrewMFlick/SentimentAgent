"""Performance tests using Locust for load testing during data collection.

These tests verify that the API maintains performance requirements
under concurrent load while data collection is running.

Run with:
    locust -f test_load_during_collection.py --headless -u 50 -r 10 -t 60s --host http://localhost:8000
"""
from locust import HttpUser, task, between, events
import time


class SentimentAPIUser(HttpUser):
    """Simulated user making API requests during data collection."""
    
    # Wait 0.5-2 seconds between requests
    wait_time = between(0.5, 2.0)
    
    @task(5)
    def get_health(self):
        """Task: Request health endpoint (highest priority).
        
        Success Criteria SC-001: <1 second response time, 100% of the time
        """
        with self.client.get(
            "/api/v1/health",
            catch_response=True,
            name="GET /health"
        ) as response:
            if response.status_code == 200:
                # Check response time requirement
                if response.elapsed.total_seconds() < 1.0:
                    response.success()
                else:
                    response.failure(
                        f"Health endpoint took {response.elapsed.total_seconds()}s, "
                        f"required <1s"
                    )
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(3)
    def get_sentiment_stats(self):
        """Task: Request sentiment statistics.
        
        Success Criteria SC-002: <3 seconds during active collection
        """
        with self.client.get(
            "/api/v1/sentiment/stats",
            catch_response=True,
            name="GET /sentiment/stats"
        ) as response:
            if response.status_code == 200:
                # Check response time requirement
                if response.elapsed.total_seconds() < 3.0:
                    response.success()
                else:
                    response.failure(
                        f"Sentiment stats took {response.elapsed.total_seconds()}s, "
                        f"required <3s"
                    )
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def get_recent_posts(self):
        """Task: Request recent posts.
        
        Success Criteria SC-002: <3 seconds during active collection
        """
        with self.client.get(
            "/api/v1/posts/recent?limit=50",
            catch_response=True,
            name="GET /posts/recent"
        ) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() < 3.0:
                    response.success()
                else:
                    response.failure(
                        f"Recent posts took {response.elapsed.total_seconds()}s, "
                        f"required <3s"
                    )
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def get_trending(self):
        """Task: Request trending topics.
        
        Success Criteria: <3 seconds during active collection
        """
        with self.client.get(
            "/api/v1/trending?limit=20",
            catch_response=True,
            name="GET /trending"
        ) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() < 3.0:
                    response.success()
                else:
                    response.failure(
                        f"Trending took {response.elapsed.total_seconds()}s, "
                        f"required <3s"
                    )
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def get_subreddits(self):
        """Task: Request monitored subreddits list.
        
        Success Criteria: Instant response (already fast, should remain so)
        """
        with self.client.get(
            "/api/v1/subreddits",
            catch_response=True,
            name="GET /subreddits"
        ) as response:
            if response.status_code == 200:
                if response.elapsed.total_seconds() < 1.0:
                    response.success()
                else:
                    response.failure(
                        f"Subreddits took {response.elapsed.total_seconds()}s, "
                        f"should be instant"
                    )
            else:
                response.failure(f"Got status code {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test information when starting."""
    print("\n" + "="*60)
    print("Performance Test: API Response During Data Collection")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count}")
    print(f"Spawn Rate: {environment.runner.spawn_rate} users/second")
    print("="*60)
    print("\nSuccess Criteria:")
    print("  - Health endpoint: <1s (100% of requests)")
    print("  - Data endpoints: <3s (P95)")
    print("  - Zero HTTP 500/504 errors (SC-006)")
    print("  - 50 concurrent requests <2s average (SC-005)")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary when test completes."""
    stats = environment.stats
    
    print("\n" + "="*60)
    print("Performance Test Results Summary")
    print("="*60)
    
    # Overall stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Average Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"P95 Response Time: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"P99 Response Time: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    
    # Check success criteria
    print("\n" + "-"*60)
    print("Success Criteria Validation:")
    print("-"*60)
    
    passed = True
    
    # SC-001: Health endpoint <1s
    health_stats = stats.get("GET /health", None)
    if health_stats:
        health_p99 = health_stats.get_response_time_percentile(0.99)
        health_pass = health_p99 < 1000
        status = "✓ PASS" if health_pass else "✗ FAIL"
        print(f"SC-001 (Health <1s P99): {health_p99:.0f}ms - {status}")
        passed = passed and health_pass
    
    # SC-002: Dashboard <3s P95
    stats_endpoint = stats.get("GET /sentiment/stats", None)
    if stats_endpoint:
        stats_p95 = stats_endpoint.get_response_time_percentile(0.95)
        stats_pass = stats_p95 < 3000
        status = "✓ PASS" if stats_pass else "✗ FAIL"
        print(f"SC-002 (Stats <3s P95): {stats_p95:.0f}ms - {status}")
        passed = passed and stats_pass
    
    # SC-005: 50 concurrent <2s average
    avg_pass = stats.total.avg_response_time < 2000
    status = "✓ PASS" if avg_pass else "✗ FAIL"
    print(f"SC-005 (Avg <2s): {stats.total.avg_response_time:.0f}ms - {status}")
    passed = passed and avg_pass
    
    # SC-006: Zero errors
    error_pass = stats.total.num_failures == 0
    status = "✓ PASS" if error_pass else "✗ FAIL"
    print(f"SC-006 (Zero errors): {stats.total.num_failures} failures - {status}")
    passed = passed and error_pass
    
    print("-"*60)
    
    if passed:
        print("\n✓ ALL SUCCESS CRITERIA MET")
    else:
        print("\n✗ SOME SUCCESS CRITERIA FAILED")
    
    print("="*60 + "\n")


# Configuration for running test
if __name__ == "__main__":
    import sys
    print("\nTo run this performance test:")
    print("  locust -f test_load_during_collection.py --headless -u 50 -r 10 -t 60s --host http://localhost:8000")
    print("\nOptions:")
    print("  -u 50: 50 concurrent users")
    print("  -r 10: Spawn 10 users per second")
    print("  -t 60s: Run for 60 seconds")
    print("  --host: Target API URL")
    print("\nAlternatively, remove --headless to use web UI at http://localhost:8089\n")
