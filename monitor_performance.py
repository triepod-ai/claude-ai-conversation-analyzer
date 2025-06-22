#!/usr/bin/env python3
# Performance Monitoring Script for Claude Conversation API

import time
import psutil
import json
from datetime import datetime

def monitor_performance():
    while True:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Performance data
        perf_data = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3)
            }
        }
        
        # Try to get Redis stats
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            info = r.info()
            perf_data["redis"] = {
                "used_memory_mb": info.get('used_memory', 0) / (1024**2),
                "connected_clients": info.get('connected_clients', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0)
            }
        except:
            perf_data["redis"] = {"status": "unavailable"}
        
        # Log performance data
        print(f"📊 {datetime.now().strftime('%H:%M:%S')} | "
              f"CPU: {cpu_percent:.1f}% | "
              f"RAM: {memory.percent:.1f}% | "
              f"Redis: {'✅' if 'redis' in perf_data and perf_data['redis'].get('connected_clients', 0) >= 0 else '❌'}")
        
        time.sleep(10)  # Monitor every 10 seconds

if __name__ == "__main__":
    print("🔍 Starting performance monitoring...")
    monitor_performance()
