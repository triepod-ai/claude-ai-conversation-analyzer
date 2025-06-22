#!/usr/bin/env python3
"""
Creative MCP Search Scenarios - Advanced Test Cases
Tests edge cases, creative queries, date combinations, and real-world search patterns
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import re

class CreativeMCPSearchTests:
    """Creative and advanced search test scenarios"""
    
    def __init__(self):
        self.search_history = []
        self.performance_metrics = []
    
    async def mock_search_call(self, tool_name: str, params: Dict) -> Dict:
        """Enhanced mock search with realistic responses"""
        self.search_history.append((tool_name, params))
        
        if tool_name == "mcp__search-conv-history__claude_search":
            return await self.generate_creative_search_response(params)
        elif tool_name == "mcp__search-conv-history__claude_search_stats":
            return self.generate_enhanced_stats()
        
        return {"error": "Unknown tool"}
    
    async def generate_creative_search_response(self, params: Dict) -> Dict:
        """Generate creative and contextual search responses"""
        query = params.get("query", "")
        category = params.get("category")
        n_results = params.get("n_results", 10)
        similarity_threshold = params.get("similarity_threshold", 0.0)
        
        # Creative response patterns based on query content
        results = []
        
        # Date-aware queries
        if any(term in query.lower() for term in ["recent", "latest", "new", "updated", "this week", "last month"]):
            results.extend(self.generate_temporal_results(query))
        
        # Technical domain queries
        if any(term in query.lower() for term in ["api", "database", "algorithm", "performance", "optimization"]):
            results.extend(self.generate_technical_results(query))
        
        # Business domain queries  
        if any(term in query.lower() for term in ["strategy", "revenue", "market", "customer", "business"]):
            results.extend(self.generate_business_results(query))
        
        # Legal/compliance queries
        if any(term in query.lower() for term in ["legal", "compliance", "regulation", "privacy", "gdpr"]):
            results.extend(self.generate_legal_results(query))
        
        # Multi-entity queries (AND/OR logic)
        if " and " in query.lower() or " or " in query.lower():
            results.extend(self.generate_multi_entity_results(query))
        
        # Question-based queries
        if query.startswith(("How", "What", "Why", "When", "Where", "Can", "Should")):
            results.extend(self.generate_qa_results(query))
        
        # Fallback for generic queries
        if not results:
            results = self.generate_generic_results(query)
        
        # Apply category filtering
        if category:
            results = [r for r in results if r["category"] == category]
        
        # Apply similarity threshold
        results = [r for r in results if r["similarity_score"] >= (similarity_threshold * 100)]
        
        # Sort by similarity score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results[:n_results],
            "collection_stats": {
                "total_documents": 46424,
                "query_processing_time": "0.125s",
                "semantic_analysis": "✅ Enhanced",
                "context_matching": "✅ Multi-dimensional"
            }
        }
    
    def generate_temporal_results(self, query: str) -> List[Dict]:
        """Generate time-aware search results"""
        now = datetime.now()
        recent_dates = [
            now - timedelta(days=1),
            now - timedelta(days=3), 
            now - timedelta(weeks=1),
            now - timedelta(weeks=2)
        ]
        
        results = []
        for i, date in enumerate(recent_dates):
            results.append({
                "rank": i + 1,
                "content": f"Recent discussion about {query.replace('recent', '').replace('latest', '').strip()}",
                "category": "general",
                "similarity_score": 90 - (i * 5),
                "source_type": "conversation",
                "metadata": {
                    "created_at": date.isoformat() + "Z",
                    "conversation_uuid": f"recent-conv-{i+1}",
                    "recency_boost": True,
                    "temporal_relevance": "high"
                }
            })
        
        return results
    
    def generate_technical_results(self, query: str) -> List[Dict]:
        """Generate technical domain results"""
        technical_contexts = [
            {
                "content": f"API design patterns and best practices for {query}",
                "category": "technical_development", 
                "score": 95,
                "metadata": {"tech_stack": ["REST", "GraphQL", "Python"], "complexity": "high"}
            },
            {
                "content": f"Database optimization strategies related to {query}",
                "category": "technical_development",
                "score": 92,
                "metadata": {"databases": ["PostgreSQL", "Redis", "ChromaDB"], "optimization_type": "performance"}
            },
            {
                "content": f"Algorithm efficiency analysis for {query}",
                "category": "technical_development", 
                "score": 89,
                "metadata": {"algorithms": ["search", "sort", "graph"], "time_complexity": "O(log n)"}
            }
        ]
        
        results = []
        for i, ctx in enumerate(technical_contexts):
            results.append({
                "rank": i + 1,
                "content": ctx["content"],
                "category": ctx["category"],
                "similarity_score": ctx["score"],
                "source_type": "conversation",
                "metadata": {
                    "created_at": (datetime.now() - timedelta(days=i*2)).isoformat() + "Z",
                    "conversation_uuid": f"tech-conv-{i+1}",
                    **ctx["metadata"]
                }
            })
        
        return results
    
    def generate_business_results(self, query: str) -> List[Dict]:
        """Generate business domain results"""
        business_contexts = [
            {
                "content": f"Market analysis and strategic planning for {query}",
                "category": "business_analysis",
                "score": 94,
                "metadata": {"market_segments": ["B2B", "Enterprise", "SMB"], "roi_impact": "high"}
            },
            {
                "content": f"Customer feedback and satisfaction metrics regarding {query}",
                "category": "business_analysis",
                "score": 91,
                "metadata": {"metrics": ["NPS", "CSAT", "Retention"], "customer_segment": "enterprise"}
            },
            {
                "content": f"Revenue optimization strategies involving {query}",
                "category": "business_analysis", 
                "score": 88,
                "metadata": {"revenue_streams": ["subscription", "usage", "enterprise"], "growth_rate": "15%"}
            }
        ]
        
        results = []
        for i, ctx in enumerate(business_contexts):
            results.append({
                "rank": i + 1,
                "content": ctx["content"],
                "category": ctx["category"],
                "similarity_score": ctx["score"],
                "source_type": "project" if i % 2 == 0 else "conversation",
                "metadata": {
                    "created_at": (datetime.now() - timedelta(days=i*3)).isoformat() + "Z",
                    "conversation_uuid": f"biz-conv-{i+1}",
                    **ctx["metadata"]
                }
            })
        
        return results
    
    def generate_legal_results(self, query: str) -> List[Dict]:
        """Generate legal/compliance domain results"""
        legal_contexts = [
            {
                "content": f"GDPR compliance requirements for {query}",
                "category": "legal_compliance",
                "score": 96,
                "metadata": {"regulations": ["GDPR", "CCPA", "PIPEDA"], "compliance_status": "compliant"}
            },
            {
                "content": f"Data privacy policies and procedures related to {query}",
                "category": "legal_compliance",
                "score": 93,
                "metadata": {"privacy_frameworks": ["Privacy by Design", "ISO 27001"], "audit_status": "passed"}
            },
            {
                "content": f"Legal risk assessment for implementation of {query}",
                "category": "legal_compliance",
                "score": 90,
                "metadata": {"risk_level": "medium", "mitigation_strategies": ["documentation", "training"]}
            }
        ]
        
        results = []
        for i, ctx in enumerate(legal_contexts):
            results.append({
                "rank": i + 1,
                "content": ctx["content"],
                "category": ctx["category"],
                "similarity_score": ctx["score"],
                "source_type": "conversation",
                "metadata": {
                    "created_at": (datetime.now() - timedelta(days=i*1)).isoformat() + "Z",
                    "conversation_uuid": f"legal-conv-{i+1}",
                    **ctx["metadata"]
                }
            })
        
        return results
    
    def generate_multi_entity_results(self, query: str) -> List[Dict]:
        """Generate results for multi-entity queries (AND/OR logic)"""
        # Parse entities from query
        entities = []
        if " and " in query.lower():
            entities = [e.strip() for e in query.lower().split(" and ")]
            logic_type = "AND"
        elif " or " in query.lower():
            entities = [e.strip() for e in query.lower().split(" or ")]
            logic_type = "OR"
        else:
            entities = [query]
            logic_type = "SINGLE"
        
        results = []
        for i, entity in enumerate(entities[:3]):  # Limit to first 3 entities
            results.append({
                "rank": i + 1,
                "content": f"Comprehensive analysis covering {entity} with cross-references to related topics",
                "category": self.infer_category_from_entity(entity),
                "similarity_score": 85 + (3 - i) * 3,
                "source_type": "conversation",
                "metadata": {
                    "created_at": (datetime.now() - timedelta(hours=i*6)).isoformat() + "Z",
                    "conversation_uuid": f"multi-entity-{i+1}",
                    "entity_matches": entities,
                    "logic_type": logic_type,
                    "cross_references": len(entities) - 1
                }
            })
        
        return results
    
    def generate_qa_results(self, query: str) -> List[Dict]:
        """Generate results for question-based queries"""
        question_types = {
            "how": "procedural_guide",
            "what": "definition_explanation", 
            "why": "reasoning_analysis",
            "when": "temporal_guidance",
            "where": "location_context",
            "can": "capability_assessment",
            "should": "recommendation_advice"
        }
        
        question_word = query.split()[0].lower()
        result_type = question_types.get(question_word, "general_qa")
        
        results = [
            {
                "rank": 1,
                "content": f"Comprehensive answer to: {query}",
                "category": "ai_assistance",
                "similarity_score": 93,
                "source_type": "conversation",
                "metadata": {
                    "created_at": datetime.now().isoformat() + "Z",
                    "conversation_uuid": "qa-primary",
                    "question_type": result_type,
                    "answer_completeness": "comprehensive",
                    "follow_up_questions": 3
                }
            },
            {
                "rank": 2,
                "content": f"Related discussion thread about {query.split()[-3:]}",
                "category": "general",
                "similarity_score": 87,
                "source_type": "conversation", 
                "metadata": {
                    "created_at": (datetime.now() - timedelta(days=2)).isoformat() + "Z",
                    "conversation_uuid": "qa-related",
                    "question_type": result_type,
                    "context_similarity": "high"
                }
            }
        ]
        
        return results
    
    def generate_generic_results(self, query: str) -> List[Dict]:
        """Generate generic fallback results"""
        return [
            {
                "rank": 1,
                "content": f"General discussion about {query}",
                "category": "general",
                "similarity_score": 75,
                "source_type": "conversation",
                "metadata": {
                    "created_at": datetime.now().isoformat() + "Z",
                    "conversation_uuid": "generic-1",
                    "query_type": "fallback"
                }
            }
        ]
    
    def infer_category_from_entity(self, entity: str) -> str:
        """Infer category from entity content"""
        entity_lower = entity.lower()
        
        if any(term in entity_lower for term in ["api", "code", "algorithm", "database", "programming"]):
            return "technical_development"
        elif any(term in entity_lower for term in ["business", "revenue", "market", "customer", "strategy"]):
            return "business_analysis"
        elif any(term in entity_lower for term in ["legal", "compliance", "privacy", "regulation"]):
            return "legal_compliance"
        elif any(term in entity_lower for term in ["data", "analytics", "metrics", "analysis"]):
            return "data_analytics"
        elif any(term in entity_lower for term in ["project", "management", "planning", "workflow"]):
            return "project_management"
        elif any(term in entity_lower for term in ["research", "study", "investigation", "exploration"]):
            return "research_strategy"
        else:
            return "general"
    
    def generate_enhanced_stats(self) -> Dict:
        """Generate enhanced database statistics with creative insights"""
        return {
            "database_stats": {
                "total_documents": 46424,
                "total_conversations": 1250,
                "total_projects": 87,
                "avg_messages_per_conversation": 12.5,
                "date_range": {
                    "earliest": "2023-06-01T00:00:00Z",
                    "latest": datetime.now().isoformat() + "Z"
                },
                "growth_metrics": {
                    "daily_conversations": 15.3,
                    "weekly_growth_rate": "12%",
                    "most_active_category": "technical_development"
                },
                "content_insights": {
                    "avg_response_length": 245,
                    "most_common_topics": ["API design", "data analysis", "legal compliance"],
                    "sentiment_distribution": {"positive": 0.65, "neutral": 0.30, "negative": 0.05}
                }
            },
            "available_filters": {
                "categories": [
                    "legal_compliance", "business_analysis", "technical_development",
                    "data_analytics", "communication", "research_strategy", 
                    "project_management", "ai_assistance", "general"
                ],
                "source_types": ["conversation", "project"],
                "date_formats": ["ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)", "natural language (last week, recent)"],
                "similarity_thresholds": {"minimum": 0.0, "recommended": 0.7, "high_precision": 0.85},
                "advanced_operators": ["AND", "OR", "NOT", "phrase matching", "wildcard support"]
            },
            "performance_metrics": {
                "avg_search_time": "0.125s",
                "index_size": "2.3GB",
                "cache_hit_rate": "87%",
                "concurrent_searches_supported": 50
            },
            "connected": True
        }


# Test Cases for Creative Scenarios
class TestCreativeSearchScenarios:
    """Test creative and advanced search scenarios"""
    
    @pytest.fixture
    def creative_client(self):
        """Provide creative search client"""
        return CreativeMCPSearchTests()
    
    @pytest.mark.asyncio
    async def test_temporal_search_patterns(self, creative_client):
        """Test various temporal search patterns"""
        temporal_queries = [
            "recent machine learning developments",
            "latest API updates this week", 
            "new compliance requirements",
            "updated documentation last month",
            "fresh insights from yesterday"
        ]
        
        for query in temporal_queries:
            response = await creative_client.mock_search_call(
                "mcp__search-conv-history__claude_search",
                {"query": query, "n_results": 5}
            )
            
            assert response["total_results"] > 0
            # Verify temporal relevance
            for result in response["results"]:
                assert "created_at" in result["metadata"]
                # Should have recent dates
                created_date = datetime.fromisoformat(result["metadata"]["created_at"].replace("Z", "+00:00"))
                assert created_date > datetime.now() - timedelta(days=30)
    
    @pytest.mark.asyncio 
    async def test_domain_specific_searches(self, creative_client):
        """Test domain-specific search intelligence"""
        domain_tests = [
            {
                "query": "REST API authentication patterns",
                "expected_category": "technical_development",
                "expected_metadata": ["tech_stack", "complexity"]
            },
            {
                "query": "customer acquisition strategy",
                "expected_category": "business_analysis", 
                "expected_metadata": ["revenue_streams", "customer_segment"]
            },
            {
                "query": "GDPR data retention policies",
                "expected_category": "legal_compliance",
                "expected_metadata": ["regulations", "compliance_status"]
            }
        ]
        
        for test_case in domain_tests:
            response = await creative_client.mock_search_call(
                "mcp__search-conv-history__claude_search",
                {"query": test_case["query"], "n_results": 3}
            )
            
            # Verify domain-appropriate results
            for result in response["results"]:
                assert result["category"] == test_case["expected_category"]
                # Check for domain-specific metadata
                metadata_keys = result["metadata"].keys()
                assert any(key in metadata_keys for key in test_case["expected_metadata"])
    
    @pytest.mark.asyncio
    async def test_multi_entity_logic(self, creative_client):
        """Test multi-entity search with AND/OR logic"""
        logic_tests = [
            {
                "query": "machine learning and data privacy",
                "logic": "AND",
                "expected_entities": 2
            },
            {
                "query": "API design or database optimization or performance tuning",
                "logic": "OR", 
                "expected_entities": 3
            }
        ]
        
        for test_case in logic_tests:
            response = await creative_client.mock_search_call(
                "mcp__search-conv-history__claude_search", 
                {"query": test_case["query"], "n_results": 5}
            )
            
            # Verify multi-entity handling
            for result in response["results"]:
                metadata = result["metadata"]
                if "entity_matches" in metadata:
                    assert len(metadata["entity_matches"]) >= test_case["expected_entities"]
                    assert metadata["logic_type"] == test_case["logic"]
    
    @pytest.mark.asyncio
    async def test_question_answering_patterns(self, creative_client):
        """Test question-based search patterns"""
        qa_patterns = [
            {
                "query": "How do I implement OAuth2 authentication?",
                "question_type": "procedural_guide"
            },
            {
                "query": "What are the benefits of microservices architecture?",
                "question_type": "definition_explanation"
            },
            {
                "query": "Why should we migrate to containerized deployment?",
                "question_type": "reasoning_analysis"
            },
            {
                "query": "When is the best time to refactor legacy code?",
                "question_type": "temporal_guidance"
            },
            {
                "query": "Can we integrate multiple payment processors?",
                "question_type": "capability_assessment"
            }
        ]
        
        for test_case in qa_patterns:
            response = await creative_client.mock_search_call(
                "mcp__search-conv-history__claude_search",
                {"query": test_case["query"], "n_results": 3}
            )
            
            # Verify question-appropriate responses
            primary_result = response["results"][0]
            assert primary_result["category"] == "ai_assistance"
            assert primary_result["metadata"]["question_type"] == test_case["question_type"]
    
    @pytest.mark.asyncio
    async def test_complex_search_combinations(self, creative_client):
        """Test complex search scenarios combining multiple criteria"""
        complex_scenarios = [
            {
                "query": "recent API security vulnerabilities and compliance requirements",
                "filters": {
                    "category": "technical_development",
                    "similarity_threshold": 0.85,
                    "n_results": 3
                },
                "expected_aspects": ["temporal", "security", "compliance", "technical"]
            },
            {
                "query": "customer feedback about performance issues last week",
                "filters": {
                    "category": "business_analysis", 
                    "similarity_threshold": 0.8,
                    "n_results": 5
                },
                "expected_aspects": ["temporal", "customer", "performance", "feedback"]
            }
        ]
        
        for scenario in complex_scenarios:
            response = await creative_client.mock_search_call(
                "mcp__search-conv-history__claude_search",
                {**{"query": scenario["query"]}, **scenario["filters"]}
            )
            
            # Verify complex criteria handling
            assert len(response["results"]) <= scenario["filters"]["n_results"]
            for result in response["results"]:
                assert result["similarity_score"] >= scenario["filters"]["similarity_threshold"] * 100
                assert result["category"] == scenario["filters"]["category"]
    
    @pytest.mark.asyncio
    async def test_edge_case_queries(self, creative_client):
        """Test edge cases and unusual query patterns"""
        edge_cases = [
            "",  # Empty query
            "a",  # Single character
            "🔍 search for API documentation 📚",  # With emojis
            "API && authentication || OAuth2",  # Programming operators
            "machine_learning.optimization(performance='high')",  # Code-like syntax
            "What's the ROI of AI/ML initiatives?",  # Mixed punctuation
            "Can you explain the API design pattern for REST vs GraphQL?",  # Long question
            "recent" * 20,  # Repeated words
            "SELECT * FROM conversations WHERE topic = 'API'",  # SQL-like
            "@mentions #hashtags and other social syntax"  # Social media syntax
        ]
        
        for query in edge_cases:
            try:
                response = await creative_client.mock_search_call(
                    "mcp__search-conv-history__claude_search",
                    {"query": query, "n_results": 3}
                )
                # Should handle gracefully
                assert "query" in response
                assert "total_results" in response
                assert isinstance(response["results"], list)
            except Exception as e:
                # Some edge cases might fail, but should be handled gracefully
                assert "error" in str(e).lower() or len(query.strip()) == 0
    
    @pytest.mark.asyncio
    async def test_performance_and_stats_integration(self, creative_client):
        """Test performance monitoring and statistics integration"""
        # Get enhanced stats
        stats_response = await creative_client.mock_search_call(
            "mcp__search-conv-history__claude_search_stats",
            {}
        )
        
        # Verify enhanced statistics
        assert "performance_metrics" in stats_response
        assert "content_insights" in stats_response["database_stats"]
        assert "growth_metrics" in stats_response["database_stats"]
        
        performance = stats_response["performance_metrics"]
        assert "avg_search_time" in performance
        assert "cache_hit_rate" in performance
        assert "concurrent_searches_supported" in performance
        
        # Use stats to inform search strategy
        categories = stats_response["available_filters"]["categories"]
        most_active = stats_response["database_stats"]["growth_metrics"]["most_active_category"]
        
        # Search in most active category
        active_response = await creative_client.mock_search_call(
            "mcp__search-conv-history__claude_search",
            {
                "query": "optimization techniques",
                "category": most_active,
                "n_results": 5
            }
        )
        
        assert active_response["total_results"] > 0
        for result in active_response["results"]:
            assert result["category"] == most_active


if __name__ == "__main__":
    # Demonstration of creative search scenarios
    async def demonstrate_creative_searches():
        """Demonstrate various creative search scenarios"""
        client = CreativeMCPSearchTests()
        
        print("🎯 Creative MCP Search Scenarios Demo")
        print("=" * 60)
        
        test_scenarios = [
            {
                "name": "Temporal Intelligence",
                "query": "recent API security vulnerabilities",
                "description": "Time-aware search with recency boost"
            },
            {
                "name": "Domain Expertise", 
                "query": "REST API authentication patterns",
                "description": "Technical domain with specialized metadata"
            },
            {
                "name": "Multi-Entity Logic",
                "query": "machine learning and data privacy and performance optimization",
                "description": "Complex AND logic with multiple entities"
            },
            {
                "name": "Question Intelligence",
                "query": "How do I implement OAuth2 with refresh tokens?",
                "description": "Procedural question with technical context"
            },
            {
                "name": "Business Context",
                "query": "customer acquisition strategy ROI analysis",
                "description": "Business domain with metrics focus"
            },
            {
                "name": "Legal Compliance",
                "query": "GDPR data retention policies for EU customers",
                "description": "Legal domain with regulatory context"
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}. {scenario['name']}")
            print(f"   Query: {scenario['query']}")
            print(f"   Description: {scenario['description']}")
            
            response = await client.mock_search_call(
                "mcp__search-conv-history__claude_search",
                {"query": scenario["query"], "n_results": 2}
            )
            
            print(f"   Results: {response['total_results']}")
            for j, result in enumerate(response["results"][:1]):
                print(f"   {j+1}. {result['content'][:80]}...")
                print(f"      Category: {result['category']} | Score: {result['similarity_score']}")
                if "tech_stack" in result["metadata"]:
                    print(f"      Tech Stack: {result['metadata']['tech_stack']}")
                if "regulations" in result["metadata"]:
                    print(f"      Regulations: {result['metadata']['regulations']}")
        
        # Enhanced statistics demo
        print(f"\n7. Enhanced Statistics")
        stats = await client.mock_search_call(
            "mcp__search-conv-history__claude_search_stats",
            {}
        )
        
        db_stats = stats["database_stats"]
        perf_stats = stats["performance_metrics"]
        
        print(f"   Database: {db_stats['total_documents']:,} docs, {db_stats['total_conversations']:,} conversations")
        print(f"   Growth: {db_stats['growth_metrics']['daily_conversations']} conversations/day")
        print(f"   Performance: {perf_stats['avg_search_time']} avg search, {perf_stats['cache_hit_rate']} cache hit rate")
        print(f"   Most Active: {db_stats['growth_metrics']['most_active_category']}")
        
        print("\n✨ Creative search scenarios completed!")
    
    # Run the demonstration
    asyncio.run(demonstrate_creative_searches())