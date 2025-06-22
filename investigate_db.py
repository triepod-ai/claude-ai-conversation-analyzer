#!/usr/bin/env python3
import asyncio
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))
sys.path.append(os.path.join(project_root, 'mcp-tools'))

from mcp_server_optimized import handle_optimized_search, initialize_search_engine

async def investigate_database():
    await initialize_search_engine()
    
    print('🔍 Investigating Database Content for Debug Scenarios...')
    
    # Test broad searches first
    broad_searches = ['triepod', 'consulting', 'business', 'exit', 'severance']
    
    for term in broad_searches:
        result = await handle_optimized_search({
            'query': term,
            'n_results': 5,
            'similarity_threshold': -1.0  # Accept all results
        })
        
        print(f'\n"{term}": {result.get("total_results", 0)} results')
        if result.get('results'):
            for i, res in enumerate(result['results'][:2]):
                print(f'  {i+1}. Score: {res.relevance_score:.3f} | {res.conversation_name[:50]}...')
                
    # Also test if "triepod" specifically returns content
    print(f'\n🎯 Specific Triepod investigation:')
    triepod_result = await handle_optimized_search({
        'query': 'triepod',
        'n_results': 10,
        'similarity_threshold': -1.0,
        'enable_business_expansion': True
    })
    
    print(f'Triepod results: {triepod_result.get("total_results", 0)}')
    expanded_queries = triepod_result.get('optimization_features', {}).get('search_enhancements', {}).get('expanded_queries', [])
    print(f'Query expansions: {expanded_queries}')
    
    if triepod_result.get('results'):
        print('Top Triepod results:')
        for i, res in enumerate(triepod_result['results'][:3]):
            print(f'  {i+1}. Score: {res.relevance_score:.3f} | {res.conversation_name}')

if __name__ == "__main__":
    asyncio.run(investigate_database())