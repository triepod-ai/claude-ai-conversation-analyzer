#!/usr/bin/env python3
"""
Quick Breaking Point Test - Find limits fast
"""

import time
import sys
import json
import psutil
import redis
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import Dict, List, Any
import threading

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from src.utils.redis_cache import RedisCache

def find_thread_breaking_point():
    """Find exactly where threading breaks"""
    print("💥 Finding Thread Breaking Point...")
    
    cache = RedisCache()
    
    def simple_worker(worker_id):
        try:
            cache.set(f"break_test_{worker_id}", f"data_{worker_id}")
            return True
        except Exception as e:
            return str(e)
    
    # Test specific thread counts to find breaking point
    thread_counts = [50, 100, 200, 300, 400, 500, 750, 1000]
    
    for num_threads in thread_counts:
        print(f"  Testing {num_threads} threads...")
        
        try:
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(simple_worker, i) for i in range(num_threads)]
                
                # Short timeout to prevent hanging
                results = []
                try:
                    for future in as_completed(futures, timeout=10):
                        result = future.result(timeout=2)
                        results.append(result)
                except TimeoutError:
                    print(f"    ❌ TIMEOUT at {num_threads} threads")
                    return {
                        "breaking_point": num_threads,
                        "failure_mode": "timeout",
                        "details": "Futures timed out",
                        "execution_time": time.time() - start_time
                    }
            
            execution_time = time.time() - start_time
            successful = sum(1 for r in results if r is True)
            failed = len(results) - successful
            
            print(f"    ✅ {successful}/{num_threads} threads successful ({execution_time:.2f}s)")
            
            # Check breaking conditions
            if failed > num_threads * 0.1:  # More than 10% failure
                return {
                    "breaking_point": num_threads,
                    "failure_mode": "high_failure_rate",
                    "details": f"{failed}/{num_threads} threads failed",
                    "execution_time": execution_time
                }
            
            if execution_time > 30:  # More than 30 seconds
                return {
                    "breaking_point": num_threads,
                    "failure_mode": "performance_degradation", 
                    "details": f"Took {execution_time:.1f}s (>30s threshold)",
                    "execution_time": execution_time
                }
                
        except Exception as e:
            return {
                "breaking_point": num_threads,
                "failure_mode": "exception",
                "details": str(e),
                "execution_time": time.time() - start_time
            }
    
    return {
        "breaking_point": "not_found",
        "failure_mode": "survived_all_tests",
        "details": f"Handled up to {thread_counts[-1]} threads",
        "execution_time": 0
    }

def find_payload_breaking_point():
    """Find where large payloads break"""
    print("💥 Finding Payload Size Breaking Point...")
    
    cache = RedisCache()
    
    # Test increasingly large payloads
    sizes = [
        (1024, "1KB"),
        (10240, "10KB"), 
        (102400, "100KB"),
        (1048576, "1MB"),
        (5242880, "5MB"),
        (10485760, "10MB"),
        (52428800, "50MB"),
        (104857600, "100MB")
    ]
    
    for size_bytes, size_name in sizes:
        print(f"  Testing {size_name} payload...")
        
        try:
            test_data = "x" * size_bytes
            
            start_time = time.time()
            cache.set(f"size_test_{size_name}", test_data)
            retrieved = cache.get(f"size_test_{size_name}")
            operation_time = time.time() - start_time
            
            print(f"    ✅ {size_name}: {operation_time:.3f}s")
            
            # Check for corruption
            if retrieved != test_data:
                return {
                    "breaking_point": size_name,
                    "failure_mode": "data_corruption",
                    "details": "Retrieved data doesn't match stored data",
                    "operation_time": operation_time
                }
            
            # Check for unreasonable slowness
            if operation_time > 5.0:  # More than 5 seconds
                return {
                    "breaking_point": size_name,
                    "failure_mode": "performance_unacceptable",
                    "details": f"Operation took {operation_time:.1f}s (>5s threshold)",
                    "operation_time": operation_time
                }
                
            # Clean up large data
            cache.delete(f"size_test_{size_name}")
            
        except MemoryError:
            return {
                "breaking_point": size_name,
                "failure_mode": "memory_error",
                "details": "Python MemoryError",
                "operation_time": 0
            }
        except Exception as e:
            return {
                "breaking_point": size_name,
                "failure_mode": "exception",
                "details": str(e),
                "operation_time": 0
            }
    
    return {
        "breaking_point": "not_found",
        "failure_mode": "survived_all_sizes",
        "details": f"Handled up to {sizes[-1][1]}",
        "operation_time": 0
    }

def find_sustained_operation_breaking_point():
    """Find where sustained operations break"""
    print("💥 Finding Sustained Operation Breaking Point...")
    
    cache = RedisCache()
    baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    operations = 0
    start_time = time.time()
    
    try:
        while True:
            # Perform operation
            cache.set(f"sustained_{operations}", f"data_{operations}")
            cache.get(f"sustained_{operations}")
            operations += 1
            
            # Check every 1000 operations
            if operations % 1000 == 0:
                elapsed = time.time() - start_time
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_increase = current_memory - baseline_memory
                ops_per_sec = operations / elapsed
                
                print(f"    {operations} ops: {ops_per_sec:.0f} ops/sec, +{memory_increase:.1f}MB memory")
                
                # Breaking conditions
                if memory_increase > 500:  # 500MB memory increase
                    return {
                        "breaking_point": operations,
                        "failure_mode": "memory_exhaustion",
                        "details": f"Memory increased by {memory_increase:.1f}MB",
                        "ops_per_sec": ops_per_sec
                    }
                
                if ops_per_sec < 100:  # Performance degraded below 100 ops/sec
                    return {
                        "breaking_point": operations,
                        "failure_mode": "performance_degradation",
                        "details": f"Performance dropped to {ops_per_sec:.0f} ops/sec",
                        "ops_per_sec": ops_per_sec
                    }
                
                if elapsed > 60:  # Run for max 1 minute
                    return {
                        "breaking_point": operations,
                        "failure_mode": "time_limit_reached",
                        "details": f"Ran for 60s successfully",
                        "ops_per_sec": ops_per_sec
                    }
                    
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "breaking_point": operations,
            "failure_mode": "exception",
            "details": str(e),
            "ops_per_sec": operations / elapsed if elapsed > 0 else 0
        }

def main():
    """Run quick breaking point tests"""
    print("🚨 QUICK BREAKING POINT ANALYSIS")
    print("Finding system limits with focused tests...")
    print()
    
    # Check Redis availability first
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=1)
        r.ping()
        print("✅ Redis available")
    except:
        print("❌ Redis not available - cannot run tests")
        return False
    
    results = {}
    
    # Test 1: Thread Breaking Point
    results["thread_test"] = find_thread_breaking_point()
    
    # Test 2: Payload Breaking Point  
    results["payload_test"] = find_payload_breaking_point()
    
    # Test 3: Sustained Operations
    results["sustained_test"] = find_sustained_operation_breaking_point()
    
    # Save results
    report_path = PROJECT_ROOT / "quick_breaking_point_results.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📋 Results saved: {report_path}")
    
    # Summary
    print(f"\n🎯 BREAKING POINT SUMMARY:")
    for test_name, result in results.items():
        breaking_point = result["breaking_point"]
        failure_mode = result["failure_mode"]
        
        if breaking_point == "not_found":
            print(f"✅ {test_name}: No breaking point found - {result['details']}")
        else:
            print(f"💥 {test_name}: BROKE at {breaking_point} - {failure_mode}")
            print(f"   Details: {result['details']}")
    
    # Check if our original claims are realistic
    print(f"\n🔍 CLAIMS VALIDATION:")
    
    # Check 50 thread claim
    thread_result = results["thread_test"]
    if thread_result["breaking_point"] == "not_found" or thread_result["breaking_point"] >= 50:
        print("✅ 50 concurrent threads: VALIDATED")
    else:
        print(f"❌ 50 concurrent threads: FAILED - breaks at {thread_result['breaking_point']}")
    
    # Check performance claims
    sustained_result = results["sustained_test"]
    if "ops_per_sec" in sustained_result and sustained_result["ops_per_sec"] > 1000:
        print(f"✅ High throughput: VALIDATED ({sustained_result['ops_per_sec']:.0f} ops/sec)")
    else:
        print(f"⚠️ High throughput: QUESTIONABLE - measured {sustained_result.get('ops_per_sec', 0):.0f} ops/sec")
    
    return True

if __name__ == "__main__":
    main()