#!/usr/bin/env python3
"""
Breaking Point Analysis - Stress Test Until Failure
Find the exact limits where our system breaks down
"""

import time
import sys
import json
import psutil
import threading
import redis
import statistics
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import gc
import resource

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from src.utils.redis_cache import RedisCache

@dataclass
class BreakingPoint:
    """Records where and how the system broke"""
    test_name: str
    break_threshold: int
    failure_mode: str
    last_successful_metric: float
    error_details: str
    system_state: Dict[str, Any]

class BreakingPointAnalyzer:
    """Systematically find where the system breaks"""
    
    def __init__(self):
        self.breaking_points = []
        self.redis_available = self._check_redis()
        self.baseline_memory = psutil.Process().memory_info().rss
        self.failure_log = []
        
    def _check_redis(self) -> bool:
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=1)
            r.ping()
            return True
        except:
            return False
    
    def _get_system_state(self) -> Dict[str, Any]:
        """Capture current system state for analysis"""
        process = psutil.Process()
        return {
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "open_files": len(process.open_files()),
            "threads": process.num_threads(),
            "connections": len(process.connections()) if hasattr(process, 'connections') else 0
        }
    
    def test_thread_explosion(self) -> BreakingPoint:
        """Find how many concurrent threads break the system"""
        print("💥 Testing Thread Explosion - Finding the breaking point...")
        
        if not self.redis_available:
            return BreakingPoint("thread_explosion", 0, "redis_unavailable", 0, "Redis not available", {})
        
        cache = RedisCache()
        successful_threads = 0
        last_successful_time = 0
        
        # Start with reasonable number and exponentially increase
        thread_counts = [10, 25, 50, 100, 200, 400, 800, 1600, 3200]
        
        for num_threads in thread_counts:
            print(f"  Testing {num_threads} threads...")
            
            try:
                def stress_worker(worker_id):
                    try:
                        for i in range(10):  # Reduced ops per thread for stress testing
                            cache.set(f"stress_{worker_id}_{i}", f"data_{i}" * 100)
                            cache.get(f"stress_{worker_id}_{i}")
                        return True
                    except Exception as e:
                        return f"Worker error: {e}"
                
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = [executor.submit(stress_worker, i) for i in range(num_threads)]
                    results = []
                    
                    # Add timeout to prevent hanging
                    for future in as_completed(futures, timeout=30):
                        try:
                            result = future.result(timeout=5)
                            results.append(result)
                        except Exception as e:
                            results.append(f"Future error: {e}")
                
                execution_time = time.time() - start_time
                successful_results = sum(1 for r in results if r is True)
                
                print(f"    {successful_results}/{num_threads} threads successful ({execution_time:.2f}s)")
                
                # Check if we had significant failures
                failure_rate = 1 - (successful_results / num_threads)
                if failure_rate > 0.1:  # More than 10% failure rate
                    return BreakingPoint(
                        "thread_explosion",
                        successful_threads,
                        f"high_failure_rate_{failure_rate:.1%}",
                        last_successful_time,
                        f"{num_threads - successful_results} threads failed",
                        self._get_system_state()
                    )
                
                # Check if execution time is unreasonable
                if execution_time > 60:  # More than 1 minute
                    return BreakingPoint(
                        "thread_explosion", 
                        successful_threads,
                        "timeout_exceeded",
                        last_successful_time,
                        f"Execution took {execution_time:.1f}s (>60s threshold)",
                        self._get_system_state()
                    )
                
                # Success - record this level
                successful_threads = num_threads
                last_successful_time = execution_time
                
            except Exception as e:
                return BreakingPoint(
                    "thread_explosion",
                    successful_threads, 
                    "exception_thrown",
                    last_successful_time,
                    str(e),
                    self._get_system_state()
                )
        
        # If we got through all tests without breaking
        return BreakingPoint(
            "thread_explosion",
            successful_threads,
            "no_breaking_point_found", 
            last_successful_time,
            f"Survived up to {successful_threads} threads",
            self._get_system_state()
        )
    
    def test_memory_exhaustion(self) -> BreakingPoint:
        """Find how much data breaks the memory"""
        print("💥 Testing Memory Exhaustion - Loading until system breaks...")
        
        if not self.redis_available:
            return BreakingPoint("memory_exhaustion", 0, "redis_unavailable", 0, "Redis not available", {})
        
        cache = RedisCache()
        successful_operations = 0
        last_memory_usage = 0
        
        # Test increasingly large payloads
        data_sizes = [
            (1024, "1KB"),           # 1KB
            (10240, "10KB"),         # 10KB  
            (102400, "100KB"),       # 100KB
            (1048576, "1MB"),        # 1MB
            (10485760, "10MB"),      # 10MB
            (104857600, "100MB"),    # 100MB
        ]
        
        for data_size, size_name in data_sizes:
            print(f"  Testing {size_name} payloads...")
            
            test_data = "x" * data_size
            operations_at_this_size = 0
            
            try:
                # Keep adding data until something breaks
                for i in range(100):  # Try up to 100 operations of this size
                    start_memory = psutil.Process().memory_info().rss
                    
                    cache.set(f"memory_test_{size_name}_{i}", test_data)
                    result = cache.get(f"memory_test_{size_name}_{i}")
                    
                    current_memory = psutil.Process().memory_info().rss
                    memory_increase = current_memory - start_memory
                    
                    operations_at_this_size += 1
                    
                    # Check if memory is growing unsustainably
                    if current_memory > self.baseline_memory + (2 * 1024 * 1024 * 1024):  # 2GB increase
                        return BreakingPoint(
                            "memory_exhaustion",
                            successful_operations,
                            "memory_limit_exceeded",
                            last_memory_usage,
                            f"Memory grew to {current_memory / 1024 / 1024:.1f}MB",
                            self._get_system_state()
                        )
                    
                    # Check for memory allocation errors
                    if result != test_data:
                        return BreakingPoint(
                            "memory_exhaustion",
                            successful_operations,
                            "data_corruption",
                            last_memory_usage,
                            f"Data corruption detected at {size_name}",
                            self._get_system_state()
                        )
                    
                    last_memory_usage = current_memory / 1024 / 1024
                
                print(f"    Successfully completed {operations_at_this_size} operations with {size_name} data")
                successful_operations += operations_at_this_size
                
            except MemoryError:
                return BreakingPoint(
                    "memory_exhaustion",
                    successful_operations,
                    "python_memory_error",
                    last_memory_usage,
                    f"Python MemoryError at {size_name}",
                    self._get_system_state()
                )
            except Exception as e:
                return BreakingPoint(
                    "memory_exhaustion", 
                    successful_operations,
                    "unexpected_exception",
                    last_memory_usage,
                    f"Exception at {size_name}: {e}",
                    self._get_system_state()
                )
        
        return BreakingPoint(
            "memory_exhaustion",
            successful_operations,
            "no_breaking_point_found",
            last_memory_usage,
            f"Survived all data sizes up to 100MB",
            self._get_system_state()
        )
    
    def test_sustained_load_endurance(self) -> BreakingPoint:
        """Run sustained load until something breaks"""
        print("💥 Testing Sustained Load Endurance - Running until failure...")
        
        if not self.redis_available:
            return BreakingPoint("sustained_load", 0, "redis_unavailable", 0, "Redis not available", {})
        
        cache = RedisCache()
        operations_completed = 0
        start_time = time.time()
        last_successful_rate = 0
        
        def sustained_worker():
            worker_ops = 0
            worker_errors = 0
            while True:
                try:
                    cache.set(f"sustained_{worker_ops}", f"data_{worker_ops}")
                    cache.get(f"sustained_{worker_ops}")
                    worker_ops += 1
                    
                    # Artificial small delay to prevent CPU melting
                    if worker_ops % 1000 == 0:
                        time.sleep(0.001)  # 1ms pause every 1000 ops
                        
                except Exception as e:
                    worker_errors += 1
                    if worker_errors > 10:  # Too many errors
                        break
            return worker_ops
        
        num_workers = 10  # Sustained load with fewer threads
        
        try:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(sustained_worker) for _ in range(num_workers)]
                
                # Monitor for breaking points
                monitor_start = time.time()
                while True:
                    time.sleep(5)  # Check every 5 seconds
                    
                    elapsed = time.time() - monitor_start
                    current_state = self._get_system_state()
                    
                    print(f"    Running for {elapsed:.1f}s - Memory: {current_state['memory_mb']:.1f}MB")
                    
                    # Check for breaking conditions
                    if current_state['memory_mb'] > 2000:  # 2GB memory usage
                        # Cancel all futures
                        for future in futures:
                            future.cancel()
                        
                        return BreakingPoint(
                            "sustained_load",
                            operations_completed,
                            "memory_exhaustion",
                            last_successful_rate,
                            f"Memory usage exceeded 2GB after {elapsed:.1f}s",
                            current_state
                        )
                    
                    if elapsed > 300:  # 5 minutes - that's enough sustained testing
                        # Cancel futures and get results
                        for future in futures:
                            future.cancel()
                        
                        total_ops = sum(f.result() for f in futures if f.done())
                        rate = total_ops / elapsed
                        
                        return BreakingPoint(
                            "sustained_load",
                            total_ops,
                            "time_limit_reached",
                            rate,
                            f"Ran successfully for 5 minutes",
                            current_state
                        )
                    
        except Exception as e:
            return BreakingPoint(
                "sustained_load",
                operations_completed,
                "executor_exception", 
                last_successful_rate,
                str(e),
                self._get_system_state()
            )
    
    def test_rapid_connection_cycling(self) -> BreakingPoint:
        """Test rapid Redis connection creation/destruction"""
        print("💥 Testing Rapid Connection Cycling - Breaking connection limits...")
        
        successful_connections = 0
        last_successful_time = 0
        
        try:
            for i in range(1000):  # Try to create 1000 connections rapidly
                start = time.time()
                
                try:
                    # Create new Redis connection each time
                    r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=1)
                    r.ping()
                    r.set(f"conn_test_{i}", f"data_{i}")
                    result = r.get(f"conn_test_{i}")
                    r.close()  # Explicit close
                    
                    connection_time = time.time() - start
                    successful_connections += 1
                    last_successful_time = connection_time
                    
                    if i % 100 == 0:
                        print(f"    {i} connections created successfully")
                    
                    # Check if connections are getting slow
                    if connection_time > 1.0:  # More than 1 second per connection
                        return BreakingPoint(
                            "connection_cycling",
                            successful_connections,
                            "connection_slowdown",
                            last_successful_time,
                            f"Connection time exceeded 1s: {connection_time:.2f}s",
                            self._get_system_state()
                        )
                        
                except redis.ConnectionError as e:
                    return BreakingPoint(
                        "connection_cycling",
                        successful_connections,
                        "redis_connection_error",
                        last_successful_time,
                        str(e),
                        self._get_system_state()
                    )
                    
        except Exception as e:
            return BreakingPoint(
                "connection_cycling",
                successful_connections,
                "unexpected_error",
                last_successful_time,
                str(e),
                self._get_system_state()
            )
        
        return BreakingPoint(
            "connection_cycling",
            successful_connections,
            "no_breaking_point_found",
            last_successful_time,
            f"Successfully created {successful_connections} connections",
            self._get_system_state()
        )

    def run_all_breaking_point_tests(self) -> List[BreakingPoint]:
        """Run all breaking point tests and collect results"""
        print("🚨 BREAKING POINT ANALYSIS - Finding System Limits")
        print("=" * 60)
        
        tests = [
            ("Thread Explosion", self.test_thread_explosion),
            ("Memory Exhaustion", self.test_memory_exhaustion), 
            ("Sustained Load", self.test_sustained_load_endurance),
            ("Connection Cycling", self.test_rapid_connection_cycling)
        ]
        
        breaking_points = []
        
        for test_name, test_func in tests:
            print(f"\n🔥 {test_name}")
            try:
                breaking_point = test_func()
                breaking_points.append(breaking_point)
                
                if breaking_point.failure_mode == "no_breaking_point_found":
                    print(f"✅ {test_name}: No breaking point found")
                else:
                    print(f"💥 {test_name}: BROKE at {breaking_point.break_threshold}")
                    print(f"   Failure mode: {breaking_point.failure_mode}")
                    print(f"   Details: {breaking_point.error_details}")
                    
            except Exception as e:
                print(f"❌ {test_name}: Test crashed - {e}")
                breaking_points.append(BreakingPoint(
                    test_name.lower().replace(" ", "_"),
                    0,
                    "test_crash",
                    0,
                    str(e),
                    self._get_system_state()
                ))
        
        return breaking_points
    
    def generate_breaking_point_report(self, breaking_points: List[BreakingPoint]) -> Dict[str, Any]:
        """Generate comprehensive breaking point analysis"""
        return {
            "timestamp": time.time(),
            "test_environment": {
                "redis_available": self.redis_available,
                "python_version": sys.version,
                "platform": sys.platform,
                "baseline_memory_mb": self.baseline_memory / 1024 / 1024
            },
            "breaking_points": [
                {
                    "test_name": bp.test_name,
                    "breaking_threshold": bp.break_threshold,
                    "failure_mode": bp.failure_mode,
                    "last_successful_metric": bp.last_successful_metric,
                    "error_details": bp.error_details,
                    "system_state_at_failure": bp.system_state
                }
                for bp in breaking_points
            ],
            "summary": {
                "tests_run": len(breaking_points),
                "systems_broken": sum(1 for bp in breaking_points if bp.failure_mode != "no_breaking_point_found"),
                "most_vulnerable_area": max(breaking_points, key=lambda bp: 0 if bp.failure_mode == "no_breaking_point_found" else 1).test_name
            }
        }

def main():
    """Run breaking point analysis"""
    print("🚨 SYSTEM BREAKING POINT ANALYSIS")
    print("Finding where our performance claims break down...")
    print("")
    
    analyzer = BreakingPointAnalyzer()
    breaking_points = analyzer.run_all_breaking_point_tests()
    
    # Generate report
    report = analyzer.generate_breaking_point_report(breaking_points)
    report_path = PROJECT_ROOT / "breaking_point_analysis.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Breaking point analysis saved: {report_path}")
    
    # Summary
    broken_systems = [bp for bp in breaking_points if bp.failure_mode != "no_breaking_point_found"]
    
    print(f"\n🎯 BREAKING POINT SUMMARY:")
    print(f"   Tests run: {len(breaking_points)}")
    print(f"   Systems broken: {len(broken_systems)}")
    
    if broken_systems:
        print(f"\n💥 BREAKING POINTS FOUND:")
        for bp in broken_systems:
            print(f"   - {bp.test_name}: Failed at {bp.break_threshold} ({bp.failure_mode})")
    else:
        print(f"\n✅ NO BREAKING POINTS FOUND - System is robust!")
    
    return len(broken_systems) == 0

if __name__ == "__main__":
    sys.exit(0 if main() else 1)