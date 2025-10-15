#!/usr/bin/env python3
"""
External process monitor for SentimentAgent backend.

This script monitors the backend process health and can be run
as a separate service or cron job to ensure the backend remains running.

Usage:
    python3 process_monitor.py [--api-url http://localhost:8000]
"""
import sys
import time
import argparse
import requests
import psutil
from datetime import datetime


def check_backend_health(api_url: str) -> dict:
    """
    Check backend health via the /health endpoint.
    
    Args:
        api_url: Base URL of the API (e.g., http://localhost:8000)
    
    Returns:
        dict: Health check response data
    
    Raises:
        Exception: If health check fails
    """
    try:
        response = requests.get(f"{api_url}/api/v1/health", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            # Service unavailable but responding
            return response.json()
        else:
            raise Exception(f"Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to backend: {e}")


def find_backend_process():
    """
    Find the backend process by searching for uvicorn running src.main:app.
    
    Returns:
        psutil.Process or None if not found
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('uvicorn' in arg for arg in cmdline) and any('src.main:app' in arg for arg in cmdline):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return None


def monitor_backend(api_url: str, interval: int = 60, verbose: bool = True):
    """
    Continuously monitor the backend process.
    
    Args:
        api_url: Base URL of the API
        interval: Check interval in seconds
        verbose: Print verbose output
    """
    print(f"Starting backend monitor (checking every {interval}s)")
    print(f"API URL: {api_url}")
    print(f"Started at: {datetime.now().isoformat()}")
    print("-" * 80)
    
    consecutive_failures = 0
    
    while True:
        try:
            # Check backend health
            health_data = check_backend_health(api_url)
            status = health_data.get('status', 'unknown')
            
            # Find backend process
            proc = find_backend_process()
            
            if status == 'healthy':
                consecutive_failures = 0
                if verbose:
                    uptime = health_data.get('process', {}).get('uptime_seconds', 0)
                    memory_mb = health_data.get('process', {}).get('memory_mb', 0)
                    cpu_percent = health_data.get('process', {}).get('cpu_percent', 0)
                    
                    print(f"[{datetime.now().isoformat()}] HEALTHY - "
                          f"Uptime: {uptime:.0f}s, "
                          f"Memory: {memory_mb:.2f}MB, "
                          f"CPU: {cpu_percent:.1f}%")
            else:
                consecutive_failures += 1
                print(f"[{datetime.now().isoformat()}] {status.upper()} - "
                      f"Consecutive failures: {consecutive_failures}")
                
                if consecutive_failures >= 3:
                    print(f"WARNING: Backend has been {status} for {consecutive_failures} checks")
            
            if proc is None:
                print(f"[{datetime.now().isoformat()}] ERROR - Backend process not found!")
                consecutive_failures += 1
            
        except Exception as e:
            consecutive_failures += 1
            print(f"[{datetime.now().isoformat()}] ERROR - {e} "
                  f"(Consecutive failures: {consecutive_failures})")
        
        time.sleep(interval)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Monitor SentimentAgent backend health')
    parser.add_argument(
        '--api-url',
        default='http://localhost:8000',
        help='Backend API URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Only print errors and warnings'
    )
    
    args = parser.parse_args()
    
    try:
        monitor_backend(
            api_url=args.api_url,
            interval=args.interval,
            verbose=not args.quiet
        )
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
