#!/usr/bin/env python3
"""
Test script for MCP search tool with project filtering
"""

import sys
import os
import asyncio
import json

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

# Import the MCP server components
sys.path.append(os.path.join(project_root, 'mcp-tools'))
from mcp_server_optimized import handle_optimized_search, initialize_search_engine

async def test_search_with_filters():
    """Test the enhanced search functionality"""
    
    print("🚀 Testing Enhanced MCP Search Tool...")
    
    # Initialize search engine
    success = await initialize_search_engine()
    if not success:
        print("❌ Failed to initialize search engine")
        return
    
    print("✅ Search engine initialized")
    
    # Test 1: Basic search with known good query
    print("\n1. Basic search for 'python':")
    basic_args = {
        "query": "python",
        "n_results": 3
    }
    result1 = await handle_optimized_search(basic_args)
    print(f"   Results: {result1.get('total_results', 0)}")
    print(f"   Full result keys: {list(result1.keys())}")
    if 'error' in result1:
        print(f"   Error: {result1['error']}")
    if result1.get('results'):
        print(f"   Sample conversations:")
        for i, result in enumerate(result1['results'][:2]):
            print(f"     {i+1}. {result.conversation_name}")
    
    # Test 2: Search with conversation filter that should match
    print("\n2. Search 'python' with conversation filter 'Windows' (should match):")
    conv_args = {
        "query": "python",
        "n_results": 5,
        "conversation_filter": "Windows"
    }
    result2 = await handle_optimized_search(conv_args)
    print(f"   Results: {result2.get('total_results', 0)}")
    print(f"   Filters applied: {result2.get('optimization_features', {}).get('filters_applied', {})}")
    if result2.get('results'):
        print(f"   Sample result: {result2['results'][0].conversation_name}")
    
    # Test 3: Search with conversation filter for 'Monitor'
    print("\n3. Search 'app' with conversation filter 'Monitor':")
    monitor_args = {
        "query": "app",
        "n_results": 5,
        "conversation_filter": "Monitor"
    }
    result3 = await handle_optimized_search(monitor_args)
    print(f"   Results: {result3.get('total_results', 0)}")
    print(f"   Filters applied: {result3.get('optimization_features', {}).get('filters_applied', {})}")
    if result3.get('results'):
        print(f"   Sample result: {result3['results'][0].conversation_name}")
    
    # Test 4: Search without filters vs with filters to show difference
    print("\n4. Comparison - search 'optimization' without vs with 'Code' filter:")
    
    # Without filter
    no_filter_args = {"query": "optimization", "n_results": 10}
    result4a = await handle_optimized_search(no_filter_args)
    print(f"   Without filter: {result4a.get('total_results', 0)} results")
    
    # With filter  
    with_filter_args = {"query": "optimization", "n_results": 10, "conversation_filter": "Code"}
    result4b = await handle_optimized_search(with_filter_args)
    print(f"   With 'Code' filter: {result4b.get('total_results', 0)} results")
    print(f"   Filters applied: {result4b.get('optimization_features', {}).get('filters_applied', {})}")
    
    print("\n✅ MCP search tool testing complete!")

if __name__ == "__main__":
    asyncio.run(test_search_with_filters())