#!/bin/bash
# High-Performance Claude Conversation API Startup Script

echo "🚀 Starting Claude Conversation API with Performance Optimizations..."

# Check Redis availability
echo "📊 Checking Redis cache availability..."
redis-cli ping 2>/dev/null && echo "✅ Redis cache available" || echo "⚠️  Redis cache unavailable - performance will be reduced"

# Set performance environment variables
export PYTHONPATH="$(pwd):$(pwd)/src"
export CHROMA_CACHE_POLICY="LRU"
export CHROMA_MAX_WORKERS="4" 
export CHROMA_MEMORY_LIMIT="1073741824"

# Memory optimization
export PYTHONHASHSEED=0
export PYTHONOPTIMIZE=1

# Start optimized MCP server
echo "⚡ Starting optimized MCP server..."
python3 mcp-tools/mcp_server_optimized.py

echo "🏁 Optimized server started successfully!"
