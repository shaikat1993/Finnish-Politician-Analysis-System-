#!/usr/bin/env python3
"""
API Performance Benchmarks

Measures API endpoint response times and throughput
"""

import time
import statistics
import requests
import concurrent.futures
from typing import List, Dict
import json


class APIBenchmark:
    """Benchmark API performance"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
    
    def benchmark_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        data: Dict = None,
        iterations: int = 100
    ) -> Dict:
        """Benchmark a single API endpoint"""
        latencies = []
        errors = 0
        
        for _ in range(iterations):
            start = time.perf_counter()
            try:
                if method == "GET":
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        timeout=10
                    )
                elif method == "POST":
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json=data,
                        timeout=10
                    )

                if response.status_code != 200:
                    errors += 1
            except Exception:
                errors += 1
            
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
        
        sorted_latencies = sorted(latencies)
        mean_latency = statistics.mean(latencies)

        return {
            'endpoint': endpoint,
            'method': method,
            'iterations': iterations,
            'mean_latency_ms': round(mean_latency, 2),
            'p95_latency_ms': round(
                sorted_latencies[int(len(sorted_latencies) * 0.95)], 2
            ),
            'p99_latency_ms': round(
                sorted_latencies[int(len(sorted_latencies) * 0.99)], 2
            ),
            'error_rate': round((errors / iterations) * 100, 2),
            'throughput_req_per_sec': round(1000 / mean_latency, 2)
        }
    
    def benchmark_concurrent_load(
        self,
        endpoint: str,
        concurrent_users: int = 10,
        requests_per_user: int = 10
    ) -> Dict:
        """Benchmark API under concurrent load"""
        def make_request():
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    timeout=10
                )
                return response.status_code == 200
            except Exception:
                return False
        
        start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=concurrent_users
        ) as executor:
            futures = [
                executor.submit(make_request)
                for _ in range(concurrent_users * requests_per_user)
            ]
            results = [
                f.result() for f in concurrent.futures.as_completed(futures)
            ]
        
        end = time.perf_counter()
        duration = end - start
        
        return {
            'concurrent_users': concurrent_users,
            'total_requests': len(results),
            'successful_requests': sum(results),
            'failed_requests': len(results) - sum(results),
            'total_duration_sec': round(duration, 2),
            'throughput_req_per_sec': round(len(results) / duration, 2),
            'avg_latency_ms': round((duration / len(results)) * 1000, 2)
        }


def main():
    """Run API benchmarks"""
    print("🌐 API Performance Benchmarks")
    print("=" * 60)
    
    benchmark = APIBenchmark()
    
    # Test if API is running
    try:
        requests.get(f"{benchmark.base_url}/health", timeout=5)
    except Exception:
        print("❌ API is not running. Start the API first:")
        print("   uvicorn api.main:app --reload")
        return
    
    # Benchmark key endpoints
    endpoints = [
        ("/api/v1/health", "GET"),
        ("/api/v1/politicians", "GET"),
        ("/api/v1/security/metrics", "GET"),
    ]
    
    for endpoint, method in endpoints:
        print(f"\n📊 Benchmarking {method} {endpoint}")
        result = benchmark.benchmark_endpoint(
            endpoint,
            method,
            iterations=50
        )
        print(f"  Mean Latency: {result['mean_latency_ms']}ms")
        print(f"  P95 Latency: {result['p95_latency_ms']}ms")
        print(f"  Throughput: {result['throughput_req_per_sec']} req/s")
    
    # Concurrent load test
    print("\n🔥 Concurrent Load Test")
    load_result = benchmark.benchmark_concurrent_load(
        "/api/v1/health",
        concurrent_users=10,
        requests_per_user=10
    )
    print(f"  Concurrent Users: {load_result['concurrent_users']}")
    print(f"  Total Requests: {load_result['total_requests']}")
    success_rate = (
        load_result['successful_requests'] /
        load_result['total_requests']
    ) * 100
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Throughput: {load_result['throughput_req_per_sec']} req/s")
    
    print("\n✅ API Benchmark complete!")


if __name__ == "__main__":
    main()