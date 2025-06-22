#!/usr/bin/env python3
"""
Test project-based filtering functionality
"""

import asyncio
import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))
sys.path.append(os.path.join(project_root, 'mcp-tools'))

from mcp_server_optimized import handle_optimized_search, initialize_search_engine

async def test_project_filtering():
    print('🎯 Testing Project-Based Filtering for MCP Search Tool...')
    
    await initialize_search_engine()
    
    # Test 1: Show all conversations about Claude
    print('\n1. Search all conversations for "claude":')
    all_claude = await handle_optimized_search({'query': 'claude', 'n_results': 10})
    print(f'   Total results: {all_claude.get("total_results", 0)}')
    
    if all_claude.get('results'):
        print('   Sample conversations:')
        for i, result in enumerate(all_claude['results'][:3]):
            print(f'     {i+1}. {result.conversation_name}')
    
    # Test 2: Filter by project name pattern
    print('\n2. Search "claude" with project filter "conversation-api":')
    project_filtered = await handle_optimized_search({
        'query': 'claude', 
        'n_results': 10,
        'project_filter': 'conversation-api'
    })
    print(f'   Filtered results: {project_filtered.get("total_results", 0)}')
    print(f'   Filter applied: {project_filtered.get("optimization_features", {}).get("filters_applied", {})}')
    
    # Test 3: Test with API-related conversations
    print('\n3. Search "optimization" with conversation filter "API":')
    api_filtered = await handle_optimized_search({
        'query': 'optimization', 
        'n_results': 10,
        'conversation_filter': 'API'
    })
    print(f'   API filtered results: {api_filtered.get("total_results", 0)}')
    if api_filtered.get('results'):
        for result in api_filtered['results']:
            print(f'     - {result.conversation_name}')
    
    # Test 4: Demonstrate scope limiting
    print('\n4. Demonstrate scope limiting - search "code" without vs with filter:')
    
    # Without filter
    code_all = await handle_optimized_search({'query': 'code', 'n_results': 10})
    print(f'   "code" without filter: {code_all.get("total_results", 0)} results')
    
    # With filter
    code_filtered = await handle_optimized_search({
        'query': 'code', 
        'n_results': 10,
        'conversation_filter': 'Update'
    })
    print(f'   "code" with "Update" filter: {code_filtered.get("total_results", 0)} results')
    
    if code_filtered.get('results'):
        print('   Filtered conversations:')
        for result in code_filtered['results']:
            print(f'     - {result.conversation_name}')
    
    print('\n✅ Project filtering testing complete!')
    print('\n📝 Usage Summary:')
    print('   • project_filter: Filter by terms in conversation names (for project identification)')
    print('   • conversation_filter: Filter by conversation topics/types')
    print('   • Both filters use case-insensitive substring matching')
    print('   • Filters are applied post-search for maximum compatibility')

if __name__ == "__main__":
    asyncio.run(test_project_filtering())