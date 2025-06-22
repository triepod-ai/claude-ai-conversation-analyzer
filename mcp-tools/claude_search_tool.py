#!/usr/bin/env python3
"""
MCP Tool: Claude Conversation Search

A Model Context Protocol tool for searching through personal Claude AI conversation history.
Provides semantic search, conversation reconstruction, and export capabilities.

Author: Bryan Thompson
License: MIT
"""

import json
import sys
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src' / 'search'))

try:
    from semantic_search import UnifiedSearchEngine
    from conversation_reconstructor import ConversationReconstructor
except ImportError as e:
    print(f"Error importing search modules: {e}")
    sys.exit(1)

class ClaudeSearchMCPTool:
    """MCP tool for searching Claude conversation history"""
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8001):
        self.search_engine = UnifiedSearchEngine(chroma_host, chroma_port)
        self.reconstructor = ConversationReconstructor(chroma_host, chroma_port)
        self.connected = False
    
    async def initialize(self) -> bool:
        """Initialize connections to ChromaDB"""
        try:
            self.connected = self.search_engine.connect()
            return self.connected
        except Exception as e:
            print(f"Failed to initialize Claude search tool: {e}")
            return False
    
    async def search_conversations(self, 
                                 query: str,
                                 n_results: int = 10,
                                 category_filter: Optional[str] = None,
                                 source_filter: Optional[str] = None,
                                 similarity_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Search through Claude conversation history
        
        Args:
            query: Search query text
            n_results: Number of results to return (default: 10)
            category_filter: Filter by content category (e.g., 'technical_development')
            source_filter: Filter by source type ('project' or 'conversation')
            similarity_threshold: Minimum similarity score (0.0-1.0)
        
        Returns:
            Dictionary with search results and metadata
        """
        if not self.connected:
            return {"error": "Tool not initialized. Call initialize() first."}
        
        try:
            results = self.search_engine.search_unified(
                query=query,
                n_results=n_results,
                category_filter=category_filter,
                source_filter=source_filter,
                similarity_threshold=similarity_threshold
            )
            
            # Convert results to serializable format
            search_results = []
            for result in results:
                search_results.append({
                    "rank": result.rank,
                    "content": result.content,
                    "category": result.category,
                    "similarity_score": round((1 - result.distance) * 100, 2),
                    "source_type": result.source_type,
                    "source_name": result.source_name,
                    "chunk_id": result.chunk_id,
                    "metadata": result.metadata
                })
            
            return {
                "query": query,
                "total_results": len(search_results),
                "results": search_results,
                "collection_stats": self.search_engine.get_collection_stats()
            }
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    async def find_conversations_by_content(self, 
                                          query: str, 
                                          limit: int = 20) -> Dict[str, Any]:
        """
        Find full conversations containing specific content
        
        Args:
            query: Content to search for in conversations
            limit: Maximum number of conversations to return
        
        Returns:
            Dictionary with matching conversations
        """
        if not self.connected:
            return {"error": "Tool not initialized. Call initialize() first."}
        
        try:
            conversations = self.reconstructor.find_conversations_by_content(query, limit)
            
            return {
                "query": query,
                "total_found": len(conversations),
                "conversations": conversations
            }
            
        except Exception as e:
            return {"error": f"Conversation search failed: {str(e)}"}
    
    async def reconstruct_conversation(self, conversation_uuid: str) -> Dict[str, Any]:
        """
        Reconstruct a full conversation by UUID
        
        Args:
            conversation_uuid: UUID of the conversation to reconstruct
        
        Returns:
            Dictionary with full conversation data
        """
        if not self.connected:
            return {"error": "Tool not initialized. Call initialize() first."}
        
        try:
            conversation = self.reconstructor.reconstruct_conversation(conversation_uuid)
            
            if not conversation:
                return {"error": f"Conversation not found: {conversation_uuid}"}
            
            return {
                "conversation_uuid": conversation_uuid,
                "conversation": conversation,
                "formatted_display": self.reconstructor.format_conversation_for_display(conversation)
            }
            
        except Exception as e:
            return {"error": f"Conversation reconstruction failed: {str(e)}"}
    
    async def list_conversations(self, limit: int = 50) -> Dict[str, Any]:
        """
        List available conversations
        
        Args:
            limit: Maximum number of conversations to list
        
        Returns:
            Dictionary with conversation list
        """
        if not self.connected:
            return {"error": "Tool not initialized. Call initialize() first."}
        
        try:
            conversations = self.reconstructor.list_conversations(limit)
            
            return {
                "total_conversations": len(conversations),
                "conversations": conversations
            }
            
        except Exception as e:
            return {"error": f"Failed to list conversations: {str(e)}"}
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the conversation database
        
        Returns:
            Dictionary with database statistics
        """
        if not self.connected:
            return {"error": "Tool not initialized. Call initialize() first."}
        
        try:
            stats = self.search_engine.get_collection_stats()
            filter_options = self.search_engine.get_filter_options()
            
            return {
                "database_stats": stats,
                "available_filters": filter_options,
                "connected": self.connected
            }
            
        except Exception as e:
            return {"error": f"Failed to get statistics: {str(e)}"}
    
    async def export_search_results(self, 
                                  query: str,
                                  results: List[Dict],
                                  export_format: str = "json",
                                  output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Export search results to file
        
        Args:
            query: Original search query
            results: Search results to export
            export_format: Export format ('json', 'csv', 'markdown', 'txt')
            output_file: Optional output filename
        
        Returns:
            Dictionary with export status
        """
        if not self.connected:
            return {"error": "Tool not initialized. Call initialize() first."}
        
        try:
            # Convert results back to UnifiedSearchResult objects for export
            from semantic_search import UnifiedSearchResult
            
            unified_results = []
            for result in results:
                unified_result = UnifiedSearchResult(
                    chunk_id=result.get("chunk_id", ""),
                    content=result.get("content", ""),
                    category=result.get("category", ""),
                    distance=1 - (result.get("similarity_score", 0) / 100),
                    source_type=result.get("source_type", ""),
                    source_name=result.get("source_name", ""),
                    metadata=result.get("metadata", {}),
                    rank=result.get("rank", 0)
                )
                unified_results.append(unified_result)
            
            output_file_path = self.search_engine.export_results(
                results=unified_results,
                query=query,
                export_format=export_format,
                output_file=output_file
            )
            
            return {
                "success": bool(output_file_path),
                "output_file": output_file_path,
                "format": export_format,
                "results_count": len(results)
            }
            
        except Exception as e:
            return {"error": f"Export failed: {str(e)}"}

# MCP Tool Interface Functions
# These functions provide the MCP-compatible interface

async def claude_search(query: str, 
                       n_results: int = 10,
                       category: Optional[str] = None,
                       source: Optional[str] = None,
                       similarity_threshold: Optional[float] = None) -> str:
    """
    MCP Tool: Search Claude conversation history
    
    Args:
        query: Search query text
        n_results: Number of results to return (1-50, default: 10)
        category: Filter by category (legal_compliance, business_analysis, technical_development, etc.)
        source: Filter by source type ('project' or 'conversation')
        similarity_threshold: Minimum similarity score (0.0-1.0)
    
    Returns:
        JSON string with search results
    """
    tool = ClaudeSearchMCPTool()
    
    if not await tool.initialize():
        return json.dumps({"error": "Failed to connect to Claude conversation database"})
    
    results = await tool.search_conversations(
        query=query,
        n_results=min(max(n_results, 1), 50),  # Clamp between 1-50
        category_filter=category,
        source_filter=source,
        similarity_threshold=similarity_threshold
    )
    
    return json.dumps(results, indent=2)

async def claude_find_conversations(query: str, limit: int = 20) -> str:
    """
    MCP Tool: Find full conversations containing specific content
    
    Args:
        query: Content to search for in conversations
        limit: Maximum number of conversations to return (1-50, default: 20)
    
    Returns:
        JSON string with matching conversations
    """
    tool = ClaudeSearchMCPTool()
    
    if not await tool.initialize():
        return json.dumps({"error": "Failed to connect to Claude conversation database"})
    
    results = await tool.find_conversations_by_content(
        query=query,
        limit=min(max(limit, 1), 50)  # Clamp between 1-50
    )
    
    return json.dumps(results, indent=2)

async def claude_reconstruct_conversation(conversation_uuid: str) -> str:
    """
    MCP Tool: Reconstruct a full conversation by UUID
    
    Args:
        conversation_uuid: UUID of the conversation to reconstruct
    
    Returns:
        JSON string with full conversation data
    """
    tool = ClaudeSearchMCPTool()
    
    if not await tool.initialize():
        return json.dumps({"error": "Failed to connect to Claude conversation database"})
    
    results = await tool.reconstruct_conversation(conversation_uuid)
    
    return json.dumps(results, indent=2)

async def claude_list_conversations(limit: int = 50) -> str:
    """
    MCP Tool: List available conversations
    
    Args:
        limit: Maximum number of conversations to list (1-100, default: 50)
    
    Returns:
        JSON string with conversation list
    """
    tool = ClaudeSearchMCPTool()
    
    if not await tool.initialize():
        return json.dumps({"error": "Failed to connect to Claude conversation database"})
    
    results = await tool.list_conversations(
        limit=min(max(limit, 1), 100)  # Clamp between 1-100
    )
    
    return json.dumps(results, indent=2)

async def claude_search_stats() -> str:
    """
    MCP Tool: Get statistics about the Claude conversation database
    
    Returns:
        JSON string with database statistics and available filters
    """
    tool = ClaudeSearchMCPTool()
    
    if not await tool.initialize():
        return json.dumps({"error": "Failed to connect to Claude conversation database"})
    
    results = await tool.get_search_statistics()
    
    return json.dumps(results, indent=2)

# Example usage and testing
if __name__ == "__main__":
    async def test_tool():
        print("Testing Claude Search MCP Tool...")
        
        # Test search
        search_result = await claude_search("machine learning optimization", n_results=5)
        print("Search Result:")
        print(search_result)
        
        # Test statistics
        stats_result = await claude_search_stats()
        print("\nDatabase Statistics:")
        print(stats_result)
    
    asyncio.run(test_tool())