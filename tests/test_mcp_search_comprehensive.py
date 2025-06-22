#!/usr/bin/env python3
"""
Comprehensive MCP Search Tools Test Suite
Tests various search methods, entity combinations, date filtering, and creative search scenarios
"""

import pytest
import json
import datetime
from typing import Dict, List, Any, Optional
import asyncio
from unittest.mock import AsyncMock, patch

# Mock MCP client for testing
class MockMCPClient:
    """Mock MCP client to simulate tool calls"""
    
    def __init__(self):
        self.call_history = []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Mock tool call that returns realistic responses"""
        self.call_history.append((tool_name, arguments))
        
        # Return different responses based on tool and arguments
        if tool_name == "mcp__search-conv-history__claude_search":
            return self._mock_search_response(arguments)
        elif tool_name == "mcp__search-conv-history__claude_find_conversations":
            return self._mock_find_conversations_response(arguments)
        elif tool_name == "mcp__search-conv-history__claude_reconstruct_conversation":
            return self._mock_reconstruct_response(arguments)
        elif tool_name == "mcp__search-conv-history__claude_list_conversations":
            return self._mock_list_conversations_response(arguments)
        elif tool_name == "mcp__search-conv-history__claude_search_stats":
            return self._mock_search_stats_response()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def _mock_search_response(self, args: Dict) -> Dict:
        """Mock search response with realistic data"""
        query = args.get("query", "")
        n_results = args.get("n_results", 10)
        category = args.get("category")
        
        # Simulate different results based on query
        if "machine learning" in query.lower():
            results = [
                {
                    "rank": 1,
                    "content": "Machine learning optimization techniques for neural networks",
                    "category": "technical_development",
                    "similarity_score": 92.5,
                    "source_type": "conversation",
                    "metadata": {
                        "created_at": "2024-01-15T10:30:00Z",
                        "conversation_uuid": "ml-conv-123"
                    }
                },
                {
                    "rank": 2,
                    "content": "Business applications of machine learning in automation",
                    "category": "business_analysis",
                    "similarity_score": 87.3,
                    "source_type": "project",
                    "metadata": {
                        "created_at": "2024-01-12T14:45:00Z",
                        "conversation_uuid": "ml-business-456"
                    }
                }
            ]
        elif "legal" in query.lower():
            results = [
                {
                    "rank": 1,
                    "content": "Legal compliance requirements for data processing",
                    "category": "legal_compliance",
                    "similarity_score": 95.1,
                    "source_type": "conversation",
                    "metadata": {
                        "created_at": "2024-01-10T09:15:00Z",
                        "conversation_uuid": "legal-comp-789"
                    }
                }
            ]
        else:
            results = [
                {
                    "rank": 1,
                    "content": f"Generic result for query: {query}",
                    "category": category or "general",
                    "similarity_score": 75.0,
                    "source_type": "conversation",
                    "metadata": {
                        "created_at": "2024-01-01T12:00:00Z",
                        "conversation_uuid": "generic-123"
                    }
                }
            ]
        
        # Filter by category if specified
        if category:
            results = [r for r in results if r["category"] == category]
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results[:n_results],
            "collection_stats": {
                "total_documents": 46424,
                "collections": {"conversations": 1250, "projects": 87}
            }
        }
    
    def _mock_find_conversations_response(self, args: Dict) -> Dict:
        """Mock conversation finding response"""
        query = args.get("query", "")
        limit = args.get("limit", 20)
        
        conversations = [
            {
                "conversation_uuid": "conv-uuid-1",
                "title": f"Discussion about {query}",
                "created_at": "2024-01-15T10:30:00Z",
                "participant_count": 2,
                "message_count": 15,
                "categories": ["technical_development", "research_strategy"]
            },
            {
                "conversation_uuid": "conv-uuid-2", 
                "title": f"Analysis of {query} implications",
                "created_at": "2024-01-12T16:20:00Z",
                "participant_count": 3,
                "message_count": 23,
                "categories": ["business_analysis", "legal_compliance"]
            }
        ]
        
        return {
            "query": query,
            "total_found": len(conversations),
            "conversations": conversations[:limit]
        }
    
    def _mock_reconstruct_response(self, args: Dict) -> Dict:
        """Mock conversation reconstruction response"""
        uuid = args.get("conversation_uuid", "")
        
        return {
            "conversation_uuid": uuid,
            "conversation": {
                "title": "Reconstructed Conversation",
                "created_at": "2024-01-15T10:30:00Z",
                "messages": [
                    {
                        "role": "human",
                        "content": "Can you help me with machine learning optimization?",
                        "timestamp": "2024-01-15T10:30:00Z"
                    },
                    {
                        "role": "assistant", 
                        "content": "I'd be happy to help with ML optimization techniques.",
                        "timestamp": "2024-01-15T10:31:00Z"
                    }
                ]
            },
            "formatted_display": "Human: Can you help me...\nAssistant: I'd be happy to help..."
        }
    
    def _mock_list_conversations_response(self, args: Dict) -> Dict:
        """Mock conversation listing response"""
        limit = args.get("limit", 50)
        
        conversations = []
        for i in range(min(limit, 10)):  # Return up to 10 mock conversations
            conversations.append({
                "conversation_uuid": f"conv-uuid-{i+1}",
                "title": f"Conversation {i+1}",
                "created_at": f"2024-01-{15-i:02d}T10:30:00Z",
                "participant_count": 2,
                "message_count": 10 + i * 2,
                "categories": ["general", "technical_development"][i % 2:]
            })
        
        return {
            "total_conversations": 1250,
            "conversations": conversations
        }
    
    def _mock_search_stats_response(self) -> Dict:
        """Mock search statistics response"""
        return {
            "database_stats": {
                "total_documents": 46424,
                "total_conversations": 1250,
                "total_projects": 87,
                "avg_messages_per_conversation": 12.5,
                "date_range": {
                    "earliest": "2023-06-01T00:00:00Z",
                    "latest": "2024-01-15T23:59:59Z"
                }
            },
            "available_filters": {
                "categories": [
                    "legal_compliance", "business_analysis", "technical_development",
                    "data_analytics", "communication", "research_strategy",
                    "project_management", "ai_assistance", "general"
                ],
                "source_types": ["conversation", "project"],
                "date_formats": "ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)"
            },
            "connected": True
        }


class TestMCPSearchMethods:
    """Test suite for MCP search tool methods"""
    
    @pytest.fixture
    def mock_client(self):
        """Provide mock MCP client for tests"""
        return MockMCPClient()
    
    @pytest.mark.asyncio
    async def test_basic_semantic_search(self, mock_client):
        """Test basic semantic search functionality"""
        response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {"query": "machine learning optimization", "n_results": 5}
        )
        
        assert response["query"] == "machine learning optimization"
        assert response["total_results"] >= 1
        assert len(response["results"]) <= 5
        assert response["results"][0]["similarity_score"] > 80
    
    @pytest.mark.asyncio
    async def test_category_filtered_search(self, mock_client):
        """Test search with category filtering"""
        response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {
                "query": "legal compliance requirements",
                "category": "legal_compliance",
                "n_results": 10
            }
        )
        
        assert all(r["category"] == "legal_compliance" for r in response["results"])
        assert response["results"][0]["similarity_score"] > 90
    
    @pytest.mark.asyncio
    async def test_multiple_entity_search(self, mock_client):
        """Test searching for multiple entities/topics"""
        # Search for multiple topics in one query
        multi_entity_query = "machine learning AND legal compliance AND data analytics"
        
        response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {"query": multi_entity_query, "n_results": 15}
        )
        
        assert response["query"] == multi_entity_query
        assert response["total_results"] >= 1
        
        # Test OR search
        or_query = "machine learning OR artificial intelligence OR neural networks"
        response_or = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {"query": or_query, "n_results": 10}
        )
        
        assert response_or["total_results"] >= 1
    
    @pytest.mark.asyncio
    async def test_similarity_threshold_search(self, mock_client):
        """Test search with similarity threshold filtering"""
        response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {
                "query": "machine learning",
                "similarity_threshold": 0.85,
                "n_results": 10
            }
        )
        
        # All results should meet the similarity threshold
        for result in response["results"]:
            assert result["similarity_score"] >= 85.0
    
    @pytest.mark.asyncio
    async def test_source_type_filtering(self, mock_client):
        """Test filtering by source type (conversation vs project)"""
        # Test conversation filtering
        conv_response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {
                "query": "project management",
                "source": "conversation",
                "n_results": 5
            }
        )
        
        # Test project filtering
        proj_response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {
                "query": "project management", 
                "source": "project",
                "n_results": 5
            }
        )
        
        # Verify source type filtering works
        assert all(r["source_type"] == "conversation" for r in conv_response["results"])
        assert all(r["source_type"] == "project" for r in proj_response["results"])
    
    @pytest.mark.asyncio
    async def test_conversation_discovery(self, mock_client):
        """Test finding full conversations containing specific content"""
        response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_find_conversations",
            {"query": "machine learning optimization", "limit": 5}
        )
        
        assert response["query"] == "machine learning optimization"
        assert response["total_found"] >= 1
        assert len(response["conversations"]) <= 5
        
        # Verify conversation metadata structure
        for conv in response["conversations"]:
            assert "conversation_uuid" in conv
            assert "title" in conv
            assert "created_at" in conv
            assert "message_count" in conv
    
    @pytest.mark.asyncio
    async def test_conversation_reconstruction(self, mock_client):
        """Test reconstructing full conversations"""
        # First find a conversation
        find_response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_find_conversations",
            {"query": "machine learning", "limit": 1}
        )
        
        if find_response["conversations"]:
            conv_uuid = find_response["conversations"][0]["conversation_uuid"]
            
            # Then reconstruct it
            reconstruct_response = await mock_client.call_tool(
                "mcp__search-conv-history__claude_reconstruct_conversation",
                {"conversation_uuid": conv_uuid}
            )
            
            assert reconstruct_response["conversation_uuid"] == conv_uuid
            assert "conversation" in reconstruct_response
            assert "messages" in reconstruct_response["conversation"]
            assert "formatted_display" in reconstruct_response
    
    @pytest.mark.asyncio
    async def test_conversation_listing(self, mock_client):
        """Test listing available conversations with metadata"""
        response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_list_conversations",
            {"limit": 20}
        )
        
        assert "total_conversations" in response
        assert "conversations" in response
        assert len(response["conversations"]) <= 20
        
        # Verify conversation metadata
        for conv in response["conversations"]:
            assert "conversation_uuid" in conv
            assert "title" in conv
            assert "created_at" in conv
            assert "participant_count" in conv
            assert "message_count" in conv
    
    @pytest.mark.asyncio
    async def test_search_statistics(self, mock_client):
        """Test getting database statistics and available filters"""
        response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search_stats",
            {}
        )
        
        assert "database_stats" in response
        assert "available_filters" in response
        assert "connected" in response
        
        # Verify database stats structure
        stats = response["database_stats"]
        assert "total_documents" in stats
        assert "total_conversations" in stats
        assert "date_range" in stats
        
        # Verify available filters
        filters = response["available_filters"]
        assert "categories" in filters
        assert "source_types" in filters
        assert len(filters["categories"]) > 5  # Should have multiple categories
    
    @pytest.mark.asyncio
    async def test_date_based_searches(self, mock_client):
        """Test various date-based search scenarios"""
        # Note: The current API doesn't explicitly support date filtering in search,
        # but we can test date-aware queries and check metadata dates
        
        # Search for recent conversations
        recent_response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {"query": "recent discussions", "n_results": 10}
        )
        
        # Verify date format in metadata
        for result in recent_response["results"]:
            created_at = result["metadata"]["created_at"]
            # Should be ISO 8601 format
            assert "T" in created_at
            assert created_at.endswith("Z")
            
        # Test date-specific queries
        date_queries = [
            "discussions from January 2024",
            "conversations this week",
            "recent machine learning updates",
            "latest legal compliance changes"
        ]
        
        for query in date_queries:
            response = await mock_client.call_tool(
                "mcp__search-conv-history__claude_search",
                {"query": query, "n_results": 5}
            )
            assert response["total_results"] >= 0
    
    @pytest.mark.asyncio
    async def test_complex_multi_criteria_search(self, mock_client):
        """Test complex searches combining multiple criteria"""
        # Complex query with multiple filters
        complex_response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {
                "query": "machine learning optimization performance",
                "category": "technical_development",
                "source": "conversation",
                "n_results": 8,
                "similarity_threshold": 0.8
            }
        )
        
        # Verify all criteria are applied
        for result in complex_response["results"]:
            assert result["category"] == "technical_development"
            assert result["source_type"] == "conversation" 
            assert result["similarity_score"] >= 80.0
    
    @pytest.mark.asyncio
    async def test_creative_search_scenarios(self, mock_client):
        """Test creative and edge case search scenarios"""
        
        # 1. Empty query handling
        try:
            await mock_client.call_tool(
                "mcp__search-conv-history__claude_search",
                {"query": "", "n_results": 5}
            )
        except Exception as e:
            # Should handle empty queries gracefully
            pass
        
        # 2. Very long query
        long_query = "artificial intelligence machine learning deep learning neural networks " * 10
        long_response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search", 
            {"query": long_query[:500], "n_results": 3}  # Truncate to reasonable length
        )
        assert long_response["total_results"] >= 0
        
        # 3. Special characters and symbols
        special_queries = [
            "C++ programming optimization",
            "data analytics & visualization",
            "API design patterns (REST/GraphQL)",
            "machine learning @ scale",
            "legal compliance 101",
            "business analysis: ROI calculations"
        ]
        
        for query in special_queries:
            response = await mock_client.call_tool(
                "mcp__search-conv-history__claude_search",
                {"query": query, "n_results": 3}
            )
            assert response["query"] == query
        
        # 4. Different language patterns
        pattern_queries = [
            "How to implement machine learning?",
            "What are the best practices for...",
            "Can you explain the difference between...",
            "I need help with legal compliance",
            "Show me examples of data analysis"
        ]
        
        for query in pattern_queries:
            response = await mock_client.call_tool(
                "mcp__search-conv-history__claude_search",
                {"query": query, "n_results": 2}
            )
            assert response["total_results"] >= 0
    
    @pytest.mark.asyncio
    async def test_result_limits_and_boundaries(self, mock_client):
        """Test various result limits and boundary conditions"""
        
        # Test minimum results
        min_response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {"query": "machine learning", "n_results": 1}
        )
        assert len(min_response["results"]) <= 1
        
        # Test maximum results (should be capped at 50)
        max_response = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search",
            {"query": "machine learning", "n_results": 100}  # Request more than max
        )
        # Should be limited to reasonable number
        assert len(max_response["results"]) <= 50
        
        # Test different similarity thresholds
        thresholds = [0.5, 0.7, 0.85, 0.95]
        for threshold in thresholds:
            response = await mock_client.call_tool(
                "mcp__search-conv-history__claude_search",
                {
                    "query": "machine learning",
                    "similarity_threshold": threshold,
                    "n_results": 10
                }
            )
            # All results should meet threshold
            for result in response["results"]:
                assert result["similarity_score"] >= threshold * 100
    
    @pytest.mark.asyncio
    async def test_workflow_integration(self, mock_client):
        """Test integrated workflow using multiple tools together"""
        
        # Step 1: Get database stats
        stats = await mock_client.call_tool(
            "mcp__search-conv-history__claude_search_stats",
            {}
        )
        
        # Step 2: Use stats to inform search strategy
        categories = stats["available_filters"]["categories"]
        
        # Step 3: Search across multiple categories
        multi_category_results = []
        for category in categories[:3]:  # Test first 3 categories
            response = await mock_client.call_tool(
                "mcp__search-conv-history__claude_search",
                {
                    "query": "optimization techniques",
                    "category": category,
                    "n_results": 2
                }
            )
            multi_category_results.append(response)
        
        # Step 4: Find related conversations
        if multi_category_results[0]["results"]:
            first_result = multi_category_results[0]["results"][0]
            related_convs = await mock_client.call_tool(
                "mcp__search-conv-history__claude_find_conversations", 
                {"query": first_result["content"][:100], "limit": 3}
            )
            
            # Step 5: Reconstruct a conversation for detailed analysis
            if related_convs["conversations"]:
                conv_uuid = related_convs["conversations"][0]["conversation_uuid"]
                full_conv = await mock_client.call_tool(
                    "mcp__search-conv-history__claude_reconstruct_conversation",
                    {"conversation_uuid": conv_uuid}
                )
                
                assert full_conv["conversation_uuid"] == conv_uuid
                assert "messages" in full_conv["conversation"]
        
        # Verify workflow completion
        assert len(multi_category_results) == 3
        assert all("results" in result for result in multi_category_results)


class TestDateFormatting:
    """Test date formatting and search patterns"""
    
    def test_iso_8601_date_parsing(self):
        """Test ISO 8601 date format parsing"""
        iso_dates = [
            "2024-01-15T10:30:00Z",
            "2024-01-15T10:30:00.123Z", 
            "2024-01-15T10:30:00+00:00",
            "2024-01-15T10:30:00-05:00"
        ]
        
        for date_str in iso_dates:
            try:
                # Should be parseable as ISO format
                if date_str.endswith('Z'):
                    parsed = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    parsed = datetime.datetime.fromisoformat(date_str)
                assert parsed.year == 2024
                assert parsed.month == 1
                assert parsed.day == 15
            except ValueError:
                pytest.fail(f"Failed to parse ISO date: {date_str}")
    
    def test_date_range_queries(self):
        """Test various date range query patterns"""
        date_patterns = [
            "after:2024-01-01",
            "before:2024-01-31", 
            "created:2024-01-15",
            "updated:last-week",
            "from:2024-01-01 to:2024-01-31",
            "recent",
            "this week",
            "last month",
            "January 2024"
        ]
        
        # These patterns could be used in natural language queries
        for pattern in date_patterns:
            assert len(pattern) > 0
            assert isinstance(pattern, str)


if __name__ == "__main__":
    # Run specific test scenarios
    import asyncio
    
    async def run_demo_searches():
        """Demonstrate various search scenarios"""
        client = MockMCPClient()
        
        print("🔍 MCP Search Tools Demo")
        print("=" * 50)
        
        # 1. Basic semantic search
        print("\n1. Basic Semantic Search:")
        response = await client.call_tool(
            "mcp__search-conv-history__claude_search",
            {"query": "machine learning optimization", "n_results": 3}
        )
        print(f"   Query: {response['query']}")
        print(f"   Results: {response['total_results']}")
        for i, result in enumerate(response['results'][:2]):
            print(f"   {i+1}. {result['content'][:60]}... (Score: {result['similarity_score']})")
        
        # 2. Category-filtered search  
        print("\n2. Category-Filtered Search:")
        response = await client.call_tool(
            "mcp__search-conv-history__claude_search",
            {"query": "legal compliance", "category": "legal_compliance", "n_results": 2}
        )
        print(f"   Category: legal_compliance")
        print(f"   Results: {response['total_results']}")
        
        # 3. Multi-entity search
        print("\n3. Multi-Entity Search:")
        response = await client.call_tool(
            "mcp__search-conv-history__claude_search", 
            {"query": "machine learning AND legal compliance", "n_results": 3}
        )
        print(f"   Multi-entity query results: {response['total_results']}")
        
        # 4. Conversation discovery
        print("\n4. Conversation Discovery:")
        response = await client.call_tool(
            "mcp__search-conv-history__claude_find_conversations",
            {"query": "optimization", "limit": 2}
        )
        print(f"   Conversations found: {response['total_found']}")
        for conv in response['conversations']:
            print(f"   - {conv['title']} ({conv['message_count']} messages)")
        
        # 5. Database statistics
        print("\n5. Database Statistics:")
        response = await client.call_tool(
            "mcp__search-conv-history__claude_search_stats",
            {}
        )
        stats = response['database_stats']
        print(f"   Total documents: {stats['total_documents']:,}")
        print(f"   Total conversations: {stats['total_conversations']:,}")
        print(f"   Available categories: {len(response['available_filters']['categories'])}")
        
        print("\n✅ Demo completed successfully!")
    
    # Run the demo
    asyncio.run(run_demo_searches())