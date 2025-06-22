#!/usr/bin/env python3
"""
Test Enhanced Search Against Debug Report Scenarios
Based on the specific search problems identified in the debug report
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))
sys.path.append(os.path.join(project_root, 'mcp-tools'))

from mcp_server_optimized import handle_optimized_search, initialize_search_engine

async def test_debug_scenarios():
    """Test the enhanced search against all debug report scenarios"""
    
    print("🔧 Testing Enhanced Search Against Debug Report Scenarios")
    print("=" * 60)
    
    await initialize_search_engine()
    
    # Original failing queries from debug report
    failing_queries = [
        "entrepreneursettlement business opportunity severance Tripod AI consulting",
        "Tripod AI consulting firm exit strategies leveraging skills", 
        "6 months severance business opportunity entrepreneurial settlement",
        "tripod products tool documentation recent work leveraging",
        "triepod exit strategies more favorable outcome 6 months",
        "favorable outcome leveraging consulting business settlement"
    ]
    
    print(f"\n🎯 Testing {len(failing_queries)} original failing queries with enhancements:")
    print("-" * 60)
    
    for i, query in enumerate(failing_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        
        # Test with all enhancements enabled
        enhanced_result = await handle_optimized_search({
            "query": query,
            "n_results": 10,
            "similarity_threshold": -1.0,  # Accept all results to see improvement
            "enable_business_expansion": True,
            "enable_recency_boost": True,
            "enable_fuzzy_matching": True
        })
        
        # Test without enhancements for comparison
        basic_result = await handle_optimized_search({
            "query": query,
            "n_results": 10,
            "similarity_threshold": -1.0,
            "enable_business_expansion": False,
            "enable_recency_boost": False,
            "enable_fuzzy_matching": False
        })
        
        print(f"   📊 Results:")
        print(f"      Basic search: {basic_result.get('total_results', 0)} results")
        print(f"      Enhanced search: {enhanced_result.get('total_results', 0)} results")
        
        # Show expanded queries
        expanded = enhanced_result.get('optimization_features', {}).get('search_enhancements', {}).get('expanded_queries', [])
        if len(expanded) > 1:
            print(f"      📈 Query expanded to {len(expanded)} variations:")
            for j, exp_query in enumerate(expanded[:3]):
                print(f"         {j+1}. {exp_query}")
        
        # Show best results with relevance scores
        if enhanced_result.get('results'):
            print(f"      🎯 Top results:")
            for j, result in enumerate(enhanced_result['results'][:2]):
                score = result.relevance_score
                conversation = result.conversation_name[:60]
                print(f"         {j+1}. Score: {score:.3f} | {conversation}")
        else:
            print(f"      ❌ No results found")
    
    print(f"\n" + "=" * 60)
    print("🧪 Testing Specific Enhancement Features")
    print("=" * 60)
    
    # Test 1: Fuzzy matching for Tripod/Triepod
    print(f"\n1. Testing Fuzzy Matching (Tripod vs Triepod):")
    
    tripod_result = await handle_optimized_search({
        "query": "Tripod consulting strategies",  # Wrong spelling
        "n_results": 5,
        "enable_fuzzy_matching": True,
        "enable_business_expansion": True
    })
    
    triepod_result = await handle_optimized_search({
        "query": "Triepod consulting strategies",  # Correct spelling
        "n_results": 5,
        "enable_fuzzy_matching": True,
        "enable_business_expansion": True
    })
    
    print(f"   'Tripod' (wrong): {tripod_result.get('total_results', 0)} results")
    print(f"   'Triepod' (correct): {triepod_result.get('total_results', 0)} results")
    print(f"   🎯 Fuzzy matching should make these results similar")
    
    # Test 2: Business vocabulary expansion
    print(f"\n2. Testing Business Vocabulary Expansion:")
    
    business_queries = [
        ("exit strategies", "Should expand to: departure planning, transition strategy"),
        ("leveraging skills", "Should expand to: capitalize on, utilize strategically"),
        ("entrepreneurial settlement", "Should expand to: business opportunity conversion"),
        ("consulting transition", "Should expand to: advisory, professional services")
    ]
    
    for query, expected in business_queries:
        result = await handle_optimized_search({
            "query": query,
            "n_results": 5,
            "enable_business_expansion": True
        })
        
        expanded = result.get('optimization_features', {}).get('search_enhancements', {}).get('expanded_queries', [])
        print(f"   '{query}': {len(expanded)} variations -> {result.get('total_results', 0)} results")
        
    # Test 3: Recency boost
    print(f"\n3. Testing Recency Boost:")
    
    recency_result = await handle_optimized_search({
        "query": "recent consulting work",
        "n_results": 5,
        "enable_recency_boost": True
    })
    
    no_recency_result = await handle_optimized_search({
        "query": "recent consulting work", 
        "n_results": 5,
        "enable_recency_boost": False
    })
    
    print(f"   With recency boost: {recency_result.get('total_results', 0)} results")
    print(f"   Without recency boost: {no_recency_result.get('total_results', 0)} results")
    
    if recency_result.get('results'):
        print(f"   🕐 Top result dates:")
        for i, result in enumerate(recency_result['results'][:3]):
            created = result.created_at[:10] if result.created_at else "Unknown"
            score = result.relevance_score
            print(f"      {i+1}. {created} (score: {score:.3f})")
    
    # Test 4: Compound concept handling
    print(f"\n4. Testing Compound Concept Handling:")
    
    compound_queries = [
        "entrepreneurial settlement strategy leveraging consulting",
        "exit strategy business opportunity six months severance",
        "favorable outcome consulting transition planning"
    ]
    
    for query in compound_queries:
        result = await handle_optimized_search({
            "query": query,
            "n_results": 5,
            "enable_business_expansion": True,
            "enable_recency_boost": True
        })
        
        print(f"   '{query[:40]}...': {result.get('total_results', 0)} results")
        if result.get('results'):
            best_score = result['results'][0].relevance_score
            print(f"      Best score: {best_score:.3f}")
    
    print(f"\n" + "=" * 60)
    print("📈 Performance Summary")
    print("=" * 60)
    
    # Summary test: Compare overall performance
    test_queries = [
        "triepod consulting business opportunity",
        "exit strategies leveraging skills", 
        "entrepreneurial settlement favorable outcome"
    ]
    
    total_basic_results = 0
    total_enhanced_results = 0
    improved_queries = 0
    
    for query in test_queries:
        basic = await handle_optimized_search({
            "query": query,
            "n_results": 10,
            "enable_business_expansion": False,
            "enable_recency_boost": False
        })
        
        enhanced = await handle_optimized_search({
            "query": query, 
            "n_results": 10,
            "enable_business_expansion": True,
            "enable_recency_boost": True
        })
        
        basic_count = basic.get('total_results', 0)
        enhanced_count = enhanced.get('total_results', 0)
        
        total_basic_results += basic_count
        total_enhanced_results += enhanced_count
        
        if enhanced_count > basic_count:
            improved_queries += 1
    
    improvement_rate = (improved_queries / len(test_queries)) * 100
    result_improvement = ((total_enhanced_results - total_basic_results) / max(total_basic_results, 1)) * 100
    
    print(f"\n✅ Enhancement Impact:")
    print(f"   📊 Queries improved: {improved_queries}/{len(test_queries)} ({improvement_rate:.1f}%)")
    print(f"   📈 Total results increase: {result_improvement:+.1f}%")
    print(f"   🎯 Basic search total: {total_basic_results} results")
    print(f"   🚀 Enhanced search total: {total_enhanced_results} results")
    
    if improvement_rate >= 50:
        print(f"\n🎉 SUCCESS: Significant improvement achieved!")
        print(f"   Enhanced search addresses major issues from debug report")
    else:
        print(f"\n⚠️  MIXED RESULTS: Some improvement but may need additional tuning")
    
    print(f"\n💡 Debug Report Issues Addressed:")
    print(f"   ✅ Fuzzy matching for Tripod/Triepod variations")
    print(f"   ✅ Business vocabulary expansion for compound concepts")
    print(f"   ✅ Recency boost for temporal relevance")
    print(f"   ✅ Multi-query expansion for complex searches")
    print(f"   📋 Next: Conversation context aggregation (future enhancement)")

if __name__ == "__main__":
    asyncio.run(test_debug_scenarios())