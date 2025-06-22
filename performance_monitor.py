#!/usr/bin/env python3
"""
Performance Monitoring and Validation Framework
Continuous performance tracking with alerts and trend analysis
"""

import time
import json
import psutil
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
import subprocess
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceSnapshot:
    """Single performance measurement snapshot"""
    timestamp: float
    operation: str
    duration_us: float  # microseconds for precision
    memory_mb: float
    cpu_percent: float
    redis_ops_per_sec: Optional[float] = None
    cache_hit_rate: Optional[float] = None
    concurrent_operations: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class PerformanceAlert:
    """Performance alert when thresholds are exceeded"""
    timestamp: float
    alert_type: str
    metric: str
    value: float
    threshold: float
    severity: str  # 'warning', 'critical'
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class PerformanceMonitor:
    """Continuous performance monitoring with alerting"""
    
    def __init__(self, 
                 alert_thresholds: Optional[Dict[str, float]] = None,
                 sample_interval: float = 1.0,
                 history_size: int = 1000):
        self.alert_thresholds = alert_thresholds or {
            'max_response_time_us': 10000,  # 10ms
            'max_memory_increase_mb': 100,  # 100MB
            'min_cache_hit_rate': 0.7,      # 70%
            'max_cpu_percent': 80           # 80%
        }
        self.sample_interval = sample_interval
        self.history_size = history_size
        
        self.snapshots: List[PerformanceSnapshot] = []
        self.alerts: List[PerformanceAlert] = []
        self.baseline_memory = 0
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Performance metrics
        self.redis_available = self._check_redis()
        
    def _check_redis(self) -> bool:
        """Check if Redis is available for monitoring"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=1)
            r.ping()
            return True
        except:
            return False
    
    def start_monitoring(self):
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.baseline_memory = psutil.Process().memory_info().rss
        
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("🔍 Performance monitoring started")
        logger.info(f"📊 Baseline memory: {self.baseline_memory / 1024 / 1024:.1f} MB")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                snapshot = self._take_snapshot()
                self._process_snapshot(snapshot)
                time.sleep(self.sample_interval)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self.sample_interval)
    
    def _take_snapshot(self) -> PerformanceSnapshot:
        """Take a performance snapshot"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Calculate memory increase from baseline
        memory_mb = (memory_info.rss - self.baseline_memory) / 1024 / 1024
        
        # Get CPU usage
        cpu_percent = process.cpu_percent()
        
        # Get Redis stats if available
        redis_ops_per_sec = None
        cache_hit_rate = None
        
        if self.redis_available:
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=1)
                info = r.info()
                
                # Calculate ops per second (rough estimate)
                total_commands = info.get('total_commands_processed', 0)
                uptime = info.get('uptime_in_seconds', 1)
                redis_ops_per_sec = total_commands / uptime if uptime > 0 else 0
                
                # Calculate cache hit rate
                keyspace_hits = info.get('keyspace_hits', 0)
                keyspace_misses = info.get('keyspace_misses', 0)
                total_keys = keyspace_hits + keyspace_misses
                cache_hit_rate = keyspace_hits / total_keys if total_keys > 0 else 0
                
            except Exception as e:
                logger.debug(f"Redis monitoring error: {e}")
        
        return PerformanceSnapshot(
            timestamp=time.time(),
            operation="system_monitor",
            duration_us=0,  # Not applicable for system monitoring
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            redis_ops_per_sec=redis_ops_per_sec,
            cache_hit_rate=cache_hit_rate
        )
    
    def _process_snapshot(self, snapshot: PerformanceSnapshot):
        """Process snapshot and generate alerts if needed"""
        # Add to history
        self.snapshots.append(snapshot)
        
        # Maintain history size
        if len(self.snapshots) > self.history_size:
            self.snapshots = self.snapshots[-self.history_size:]
        
        # Check for alerts
        self._check_alerts(snapshot)
    
    def _check_alerts(self, snapshot: PerformanceSnapshot):
        """Check if any alert thresholds are exceeded"""
        alerts = []
        
        # Memory alert
        if snapshot.memory_mb > self.alert_thresholds['max_memory_increase_mb']:
            alerts.append(PerformanceAlert(
                timestamp=snapshot.timestamp,
                alert_type="memory_increase",
                metric="memory_mb",
                value=snapshot.memory_mb,
                threshold=self.alert_thresholds['max_memory_increase_mb'],
                severity="critical",
                message=f"Memory increased by {snapshot.memory_mb:.1f}MB (threshold: {self.alert_thresholds['max_memory_increase_mb']}MB)"
            ))
        
        # CPU alert
        if snapshot.cpu_percent > self.alert_thresholds['max_cpu_percent']:
            alerts.append(PerformanceAlert(
                timestamp=snapshot.timestamp,
                alert_type="cpu_usage",
                metric="cpu_percent",
                value=snapshot.cpu_percent,
                threshold=self.alert_thresholds['max_cpu_percent'],
                severity="warning",
                message=f"CPU usage: {snapshot.cpu_percent:.1f}% (threshold: {self.alert_thresholds['max_cpu_percent']}%)"
            ))
        
        # Cache hit rate alert
        if snapshot.cache_hit_rate is not None and snapshot.cache_hit_rate < self.alert_thresholds['min_cache_hit_rate']:
            alerts.append(PerformanceAlert(
                timestamp=snapshot.timestamp,
                alert_type="cache_performance",
                metric="cache_hit_rate",
                value=snapshot.cache_hit_rate,
                threshold=self.alert_thresholds['min_cache_hit_rate'],
                severity="warning",
                message=f"Cache hit rate: {snapshot.cache_hit_rate:.1%} (threshold: {self.alert_thresholds['min_cache_hit_rate']:.1%})"
            ))
        
        # Log and store alerts
        for alert in alerts:
            self.alerts.append(alert)
            severity_emoji = "🚨" if alert.severity == "critical" else "⚠️"
            logger.warning(f"{severity_emoji} {alert.message}")
    
    def record_operation(self, operation: str, duration_us: float, concurrent_ops: int = 1):
        """Record a specific operation performance"""
        process = psutil.Process()
        memory_mb = (process.memory_info().rss - self.baseline_memory) / 1024 / 1024
        
        snapshot = PerformanceSnapshot(
            timestamp=time.time(),
            operation=operation,
            duration_us=duration_us,
            memory_mb=memory_mb,
            cpu_percent=process.cpu_percent(),
            concurrent_operations=concurrent_ops
        )
        
        self._process_snapshot(snapshot)
        
        # Check for operation-specific alerts
        if duration_us > self.alert_thresholds['max_response_time_us']:
            alert = PerformanceAlert(
                timestamp=snapshot.timestamp,
                alert_type="slow_operation",
                metric="duration_us",
                value=duration_us,
                threshold=self.alert_thresholds['max_response_time_us'],
                severity="warning",
                message=f"Slow operation '{operation}': {duration_us:.0f}μs (threshold: {self.alert_thresholds['max_response_time_us']}μs)"
            )
            self.alerts.append(alert)
            logger.warning(f"⚠️ {alert.message}")
    
    def get_performance_summary(self, last_minutes: int = 5) -> Dict[str, Any]:
        """Get performance summary for the last N minutes"""
        cutoff_time = time.time() - (last_minutes * 60)
        recent_snapshots = [s for s in self.snapshots if s.timestamp >= cutoff_time]
        recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
        
        if not recent_snapshots:
            return {"error": "No recent performance data"}
        
        # Calculate statistics
        memory_values = [s.memory_mb for s in recent_snapshots]
        cpu_values = [s.cpu_percent for s in recent_snapshots]
        operation_durations = [s.duration_us for s in recent_snapshots if s.duration_us > 0]
        
        summary = {
            "time_window_minutes": last_minutes,
            "snapshot_count": len(recent_snapshots),
            "alert_count": len(recent_alerts),
            "memory": {
                "current_mb": memory_values[-1] if memory_values else 0,
                "max_mb": max(memory_values) if memory_values else 0,
                "avg_mb": statistics.mean(memory_values) if memory_values else 0
            },
            "cpu": {
                "current_percent": cpu_values[-1] if cpu_values else 0,
                "max_percent": max(cpu_values) if cpu_values else 0,
                "avg_percent": statistics.mean(cpu_values) if cpu_values else 0
            },
            "operations": {
                "count": len(operation_durations),
                "avg_duration_us": statistics.mean(operation_durations) if operation_durations else 0,
                "max_duration_us": max(operation_durations) if operation_durations else 0
            },
            "recent_alerts": [alert.to_dict() for alert in recent_alerts[-5:]]  # Last 5 alerts
        }
        
        # Add Redis metrics if available
        redis_snapshots = [s for s in recent_snapshots if s.cache_hit_rate is not None]
        if redis_snapshots:
            summary["redis"] = {
                "cache_hit_rate": redis_snapshots[-1].cache_hit_rate,
                "ops_per_sec": redis_snapshots[-1].redis_ops_per_sec
            }
        
        return summary
    
    def export_performance_data(self, filepath: str):
        """Export all performance data to JSON file"""
        data = {
            "export_timestamp": time.time(),
            "monitoring_duration_seconds": time.time() - (self.snapshots[0].timestamp if self.snapshots else time.time()),
            "total_snapshots": len(self.snapshots),
            "total_alerts": len(self.alerts),
            "alert_thresholds": self.alert_thresholds,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "alerts": [a.to_dict() for a in self.alerts],
            "summary": self.get_performance_summary(60)  # Last hour
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"📊 Performance data exported to {filepath}")

def context_manager_monitor():
    """Context manager for performance monitoring"""
    class PerformanceMonitorContext:
        def __init__(self):
            self.monitor = PerformanceMonitor()
        
        def __enter__(self):
            self.monitor.start_monitoring()
            return self.monitor
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.monitor.stop_monitoring()
    
    return PerformanceMonitorContext()

def timed_operation(operation_name: str):
    """Decorator to time and monitor operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                duration_us = (end_time - start_time) * 1_000_000
                
                # Record in global monitor if available
                if hasattr(wrapper, '_monitor') and wrapper._monitor:
                    wrapper._monitor.record_operation(operation_name, duration_us)
                else:
                    # Create standalone snapshot
                    logger.info(f"⏱️ {operation_name}: {duration_us:.0f}μs")
                
                return result
            except Exception as e:
                end_time = time.perf_counter()
                duration_us = (end_time - start_time) * 1_000_000
                logger.error(f"❌ {operation_name} failed after {duration_us:.0f}μs: {e}")
                raise
        
        wrapper._monitor = None
        return wrapper
    return decorator

def main():
    """Standalone performance monitoring"""
    monitor = PerformanceMonitor(
        alert_thresholds={
            'max_response_time_us': 5000,   # 5ms
            'max_memory_increase_mb': 50,   # 50MB
            'min_cache_hit_rate': 0.8,      # 80%
            'max_cpu_percent': 70           # 70%
        }
    )
    
    def signal_handler(signum, frame):
        logger.info("📊 Exporting performance data...")
        monitor.export_performance_data("performance_monitoring_export.json")
        monitor.stop_monitoring()
        sys.exit(0)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🔍 Starting performance monitoring...")
    print("📊 Press Ctrl+C to stop and export data")
    
    monitor.start_monitoring()
    
    try:
        # Simulate some operations for demo
        while True:
            time.sleep(10)
            summary = monitor.get_performance_summary(1)  # Last minute
            print(f"📈 Performance: Memory: {summary['memory']['current_mb']:.1f}MB, "
                  f"CPU: {summary['cpu']['current_percent']:.1f}%, "
                  f"Alerts: {summary['alert_count']}")
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()