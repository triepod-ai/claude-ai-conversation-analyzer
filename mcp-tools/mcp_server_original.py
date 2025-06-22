#!/usr/bin/env python3
"""
MCP Server for Claude Conversation Search

A Model Context Protocol server that exposes Claude conversation search capabilities
as MCP tools for integration with Claude Code and other MCP-compatible applications.

Usage:
    python mcp_server.py

This server provides the following MCP tools:
- claude_search: Search through conversation history
- claude_find_conversations: Find conversations by content
- claude_reconstruct_conversation: Get full conversation by UUID  
- claude_list_conversations: List available conversations
- claude_search_stats: Get database statistics

Author: Bryan Thompson
License: MIT
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass

# MCP imports
try:
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
except ImportError:
    print("MCP library not found. Install with: pip install mcp")
    print("See: https://github.com/modelcontextprotocol/python-sdk")
    exit(1)

# Local imports
from claude_search_tool import ClaudeSearchMCPTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("claude-search-mcp")

# Server instance
server = Server("claude-search")

# Global tool instance
search_tool: Optional[ClaudeSearchMCPTool] = None

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available MCP tools"""
    return [
        types.Tool(
            name="claude_search",
            description="Search through your personal Claude conversation history using semantic search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-50)",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by content category",
                        "enum": [
                            "legal_compliance", "business_analysis", "technical_development",
                            "data_analytics", "communication", "research_strategy",
                            "project_management", "ai_assistance", "general"
                        ]
                    },
                    "source": {
                        "type": "string",
                        "description": "Filter by source type",
                        "enum": ["project", "conversation"]
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="claude_find_conversations",
            description="Find full conversations containing specific content",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Content to search for in conversations"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of conversations to return (1-50)",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="claude_reconstruct_conversation",
            description="Reconstruct a full conversation by UUID for detailed analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_uuid": {
                        "type": "string",
                        "description": "UUID of the conversation to reconstruct"
                    }
                },
                "required": ["conversation_uuid"]
            }
        ),
        types.Tool(
            name="claude_list_conversations",
            description="List available conversations with metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of conversations to list (1-100)",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 50
                    }
                }
            }
        ),
        types.Tool(
            name="claude_search_stats",
            description="Get statistics about the Claude conversation database and available filters",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    global search_tool
    
    # Initialize tool if needed
    if search_tool is None:
        search_tool = ClaudeSearchMCPTool()
        if not await search_tool.initialize():
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Failed to initialize Claude conversation search tool. Check ChromaDB connection."
                })
            )]
    
    try:
        if name == "claude_search":
            query = arguments.get("query", "")
            n_results = arguments.get("n_results", 10)
            category = arguments.get("category")
            source = arguments.get("source")
            similarity_threshold = arguments.get("similarity_threshold")
            
            if not query:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Query parameter is required"})
                )]
            
            results = await search_tool.search_conversations(
                query=query,
                n_results=n_results,
                category_filter=category,
                source_filter=source,
                similarity_threshold=similarity_threshold
            )
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        
        elif name == "claude_find_conversations":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 20)
            
            if not query:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Query parameter is required"})
                )]
            
            results = await search_tool.find_conversations_by_content(query, limit)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        
        elif name == "claude_reconstruct_conversation":
            conversation_uuid = arguments.get("conversation_uuid", "")
            
            if not conversation_uuid:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "conversation_uuid parameter is required"})
                )]
            
            results = await search_tool.reconstruct_conversation(conversation_uuid)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        
        elif name == "claude_list_conversations":
            limit = arguments.get("limit", 50)
            
            results = await search_tool.list_conversations(limit)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        
        elif name == "claude_search_stats":
            results = await search_tool.get_search_statistics()
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]
    
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Tool execution failed: {str(e)}"})
        )]

async def main():
    """Main server function"""
    logger.info("Starting Claude Search MCP Server...")
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="claude-search",
                server_version="1.0.0"
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())