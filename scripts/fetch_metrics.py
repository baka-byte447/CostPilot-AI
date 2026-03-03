#!/usr/bin/env python3
"""
CostPilot-AI Metrics Verification Script
Tests telemetry collection and Prometheus persistence.

Usage:
    python fetch_metrics.py [--check-prometheus] [--check-backend] [--all]

This script verifies:
1. Backend API health
2. Metrics collection functionality
3. Prometheus /metrics endpoint
4. Data persistence in Prometheus TSDB
5. System metrics collection
"""

import sys
import time
import json
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_status(message: str, status: str = "INFO"):
    """Print colored status message."""
    colors = {
        "OK": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARNING": Colors.YELLOW,
        "INFO": Colors.BLUE
    }
    color = colors.get(status, Colors.RESET)
    print(f"{color}[{status}]{Colors.RESET} {message}")


def check_backend_health(base_url: str = "http://localhost:8000") -> Tuple[bool, Dict]:
    """Check if backend is running and healthy."""
    print("\n" + "=" * 60)
    print("CHECKING BACKEND HEALTH")
    print("=" * 60)
    
    try:
        print_status(f"Connecting to backend: {base_url}/health", "INFO")
        response = requests.get(f"{base_url}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"Backend is healthy: {data['status']}", "OK")
            return True, data
        else:
            print_status(f"Backend returned status {response.status_code}", "ERROR")
            return False, {}
    except requests.exceptions.ConnectionError:
        print_status(f"Cannot connect to backend at {base_url}", "ERROR")
        return False, {}
    except Exception as e:
        print_status(f"Error checking backend health: {e}", "ERROR")
        return False, {}


def check_api_metrics(base_url: str = "http://localhost:8000") -> Tuple[bool, Dict]:
    """Check if API metrics endpoint is working."""
    print("\n" + "=" * 60)
    print("CHECKING API METRICS ENDPOINT")
    print("=" * 60)
    
    try:
        print_status("Fetching system metrics from /api/system-metrics", "INFO")
        response = requests.get(f"{base_url}/api/system-metrics", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status("System metrics retrieved successfully", "OK")
            
            # Display collected metrics
            print("\nCollected Metrics:")
            print(f"  Timestamp: {data.get('timestamp')}")
            print(f"  Hostname: {data.get('hostname')}")
            
            if 'cpu' in data:
                print(f"  CPU Usage: {data['cpu'].get('usage_percent')}%")
                print(f"  CPU Count: {data['cpu'].get('count')}")
            
            if 'memory' in data:
                mem = data['memory']
                print(f"  Memory Used: {mem.get('used_bytes', 0) / (1024**3):.2f} GB")
                print(f"  Memory Total: {mem.get('total_bytes', 0) / (1024**3):.2f} GB")
                print(f"  Memory Usage: {mem.get('percent')}%")
            
            if 'summary' in data:
                print(f"  Uptime: {data['summary'].get('uptime_seconds', 0):.2f} seconds")
            
            return True, data
        else:
            print_status(f"Metrics endpoint returned status {response.status_code}", "ERROR")
            return False, {}
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to backend for metrics", "ERROR")
        return False, {}
    except Exception as e:
        print_status(f"Error fetching metrics: {e}", "ERROR")
        return False, {}


def check_prometheus_metrics(base_url: str = "http://localhost:8000") -> Tuple[bool, str]:
    """Check if Prometheus /metrics endpoint is working."""
    print("\n" + "=" * 60)
    print("CHECKING PROMETHEUS METRICS ENDPOINT")
    print("=" * 60)
    
    try:
        print_status("Fetching Prometheus metrics from /metrics", "INFO")
        response = requests.get(f"{base_url}/metrics", timeout=10)
        
        if response.status_code == 200:
            metrics_text = response.text
            print_status("Prometheus metrics retrieved successfully", "OK")
            
            # Count metrics
            metric_lines = [line for line in metrics_text.split('\n') 
                          if line and not line.startswith('#')]
            print_status(f"Total metric entries: {len(metric_lines)}", "INFO")
            
            # Show sample metrics
            print("\nSample Metrics (first 10):")
            for line in metric_lines[:10]:
                if line and not line.startswith('#'):
                    # Parse and display metric
                    parts = line.split('{')
                    metric_name = parts[0]
                    print(f"  - {metric_name}")
            
            return True, metrics_text
        else:
            print_status(f"/metrics endpoint returned status {response.status_code}", "ERROR")
            return False, ""
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to backend /metrics endpoint", "ERROR")
        return False, ""
    except Exception as e:
        print_status(f"Error fetching Prometheus metrics: {e}", "ERROR")
        return False, ""


def check_prometheus_tsdb(prometheus_url: str = "http://localhost:9090") -> Tuple[bool, Dict]:
    """Check if Prometheus TSDB is running and has data."""
    print("\n" + "=" * 60)
    print("CHECKING PROMETHEUS TSDB")
    print("=" * 60)
    
    try:
        print_status(f"Connecting to Prometheus: {prometheus_url}", "INFO")
        
        # Check Prometheus API
        response = requests.get(f"{prometheus_url}/api/v1/targets", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_status("Prometheus TSDB is running", "OK")
            
            # Check targets
            targets = data.get('data', {}).get('activeTargets', [])
            print_status(f"Active targets: {len(targets)}", "INFO")
            
            for target in targets:
                labels = target.get('labels', {})
                job = labels.get('job', 'unknown')
                health = target.get('health', 'unknown')
                status_color = Colors.GREEN if health == 'up' else Colors.RED
                print(f"  {status_color}[{health.upper()}]{Colors.RESET} {job}")
            
            return True, data
        else:
            print_status(f"Prometheus returned status {response.status_code}", "ERROR")
            return False, {}
    except requests.exceptions.ConnectionError:
        print_status(f"Cannot connect to Prometheus at {prometheus_url}", "ERROR")
        print_status("Make sure Prometheus is running on port 9090", "WARNING")
        return False, {}
    except Exception as e:
        print_status(f"Error checking Prometheus: {e}", "ERROR")
        return False, {}


def query_prometheus_metrics(prometheus_url: str = "http://localhost:9090") -> Tuple[bool, Dict]:
    """Query Prometheus for specific metrics."""
    print("\n" + "=" * 60)
    print("QUERYING PROMETHEUS METRICS")
    print("=" * 60)
    
    queries = {
        "Up Status": "up",
        "CPU Usage": "system_cpu_usage_percent",
        "Memory Usage %": "system_memory_percent",
        "API Requests": "api_requests_total",
        "Uptime": "application_uptime_seconds"
    }
    
    results = {}
    
    for query_name, query in queries.items():
        try:
            print_status(f"Querying: {query_name}", "INFO")
            
            response = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                results_vec = data.get('data', {}).get('result', [])
                
                if results_vec:
                    print_status(f"{query_name}: Found {len(results_vec)} metric(s)", "OK")
                    for result in results_vec[:2]:  # Show first 2
                        labels = result.get('metric', {})
                        value = result.get('value', ['', '?'])
                        print(f"    Value: {value[1]} (Labels: {labels})")
                    results[query_name] = "Found"
                else:
                    print_status(f"{query_name}: No data found (verify metrics are being recorded)", "WARNING")
                    results[query_name] = "No data"
            else:
                print_status(f"{query_name}: Query failed", "ERROR")
                results[query_name] = "Failed"
        except requests.exceptions.ConnectionError:
            print_status(f"Cannot connect to Prometheus", "ERROR")
            results[query_name] = "No connection"
        except Exception as e:
            print_status(f"Error querying {query_name}: {e}", "ERROR")
            results[query_name] = "Error"
    
    return len([r for r in results.values() if r == "Found"]) > 0, results


def run_stress_test(base_url: str = "http://localhost:8000", count: int = 10):
    """Generate some load to test metric recording."""
    print("\n" + "=" * 60)
    print("RUNNING STRESS TEST (Generating API load)")
    print("=" * 60)
    
    print_status(f"Generating {count} API requests to record metrics", "INFO")
    
    successful = 0
    failed = 0
    
    for i in range(count):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                successful += 1
                print_status(f"Request {i+1}/{count}: OK", "OK")
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print_status(f"Request {i+1}/{count}: Failed - {e}", "ERROR")
        
        time.sleep(0.5)
    
    print_status(f"Stress test complete: {successful} successful, {failed} failed", "INFO")
    return successful > 0


def generate_report(all_checks: Dict[str, bool]) -> None:
    """Generate final verification report."""
    print("\n" + "=" * 60)
    print("VERIFICATION REPORT")
    print("=" * 60)
    
    passed = sum(1 for v in all_checks.values() if v)
    total = len(all_checks)
    
    print(f"\nResults: {passed}/{total} checks passed\n")
    
    for check_name, passed_check in all_checks.items():
        status = "✓ PASS" if passed_check else "✗ FAIL"
        color = Colors.GREEN if passed_check else Colors.RED
        print(f"{color}{status}{Colors.RESET} - {check_name}")
    
    if passed == total:
        print_status("\n🎉 All checks passed! Telemetry is working correctly.", "OK")
    elif passed >= (total * 0.7):
        print_status("\n⚠️  Most checks passed. Some issues to investigate.", "WARNING")
    else:
        print_status("\n❌ Multiple failures. Check the logs above for details.", "ERROR")


def main():
    """Main verification script."""
    parser = argparse.ArgumentParser(
        description="CostPilot-AI Telemetry Verification Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_metrics.py --all           # Run all checks
  python fetch_metrics.py --check-backend # Check only backend
  python fetch_metrics.py --check-prometheus # Check only Prometheus
        """
    )
    
    parser.add_argument("--all", action="store_true", help="Run all verification checks")
    parser.add_argument("--check-backend", action="store_true", help="Check backend health and metrics")
    parser.add_argument("--check-prometheus", action="store_true", help="Check Prometheus TSDB")
    parser.add_argument("--stress-test", action="store_true", help="Run stress test")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--prometheus-url", default="http://localhost:9090", help="Prometheus URL")
    
    args = parser.parse_args()
    
    # If no specific checks requested, default to all
    if not any([args.all, args.check_backend, args.check_prometheus, args.stress_test]):
        args.all = True
    
    checks_results = {}
    
    print("\n" + "=" * 60)
    print("COSTPILOT-AI TELEMETRY VERIFICATION")
    print("=" * 60)
    
    # Backend checks
    if args.all or args.check_backend:
        backend_ok, _ = check_backend_health(args.backend_url)
        checks_results["Backend Health"] = backend_ok
        
        if backend_ok:
            metrics_ok, _ = check_api_metrics(args.backend_url)
            checks_results["API Metrics Endpoint"] = metrics_ok
            
            prometheus_ok, _ = check_prometheus_metrics(args.backend_url)
            checks_results["Prometheus Format Metrics"] = prometheus_ok
    
    # Prometheus checks
    if args.all or args.check_prometheus:
        time.sleep(1)  # Give services time to settle
        
        tsdb_ok, _ = check_prometheus_tsdb(args.prometheus_url)
        checks_results["Prometheus TSDB"] = tsdb_ok
        
        if tsdb_ok:
            query_ok, results = query_prometheus_metrics(args.prometheus_url)
            checks_results["Prometheus Queries"] = query_ok
    
    # Stress test
    if args.stress_test or args.all:
        time.sleep(2)
        stress_ok = run_stress_test(args.backend_url)
        checks_results["Stress Test"] = stress_ok
    
    # Generate report
    generate_report(checks_results)
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("""
1. Access Prometheus UI: http://localhost:9090
   - Check "Status" -> "Targets" to see active targets
   - Use the query bar to test PromQL queries

2. Access Grafana (if available): http://localhost:3000
   - Add Prometheus as a data source
   - Create dashboards from the collected metrics

3. View backend metrics: http://localhost:8000/metrics
   - Shows all metrics in Prometheus text format

4. Check API health: http://localhost:8000/health
   - Shows backend health status and uptime
    """)


if __name__ == "__main__":
    main()

