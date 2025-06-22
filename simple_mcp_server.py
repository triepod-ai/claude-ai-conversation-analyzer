#!/usr/bin/env python3
"""
Simple MCP Server for Claude Conversation Search

A minimal MCP server implementation.
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional

# MCP imports
try:
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import chromadb
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: uv pip install mcp chromadb")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("claude-search")

# Create server
server = Server("claude-search")

# Global ChromaDB client
client = None
collection = None

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="claude_search",
            description="Search through Claude conversation history",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "Number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="claude_search_stats",
            description="Get database statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> List[types.TextContent]:
    """Handle tool calls"""
    global client, collection
    
    try:
        # Initialize ChromaDB if needed
        if client is None:
            client = chromadb.PersistentClient(path="./chroma_db")
            collection = client.get_collection("personal_claude_conversations")
        
        if name == "claude_search":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 5)
            
            if not query:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Query is required"})
                )]
            
            # Perform search
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            search_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    search_results.append({
                        "content": doc,
                        "conversation_name": metadata.get("conversation_name", "Unknown"),
                        "sender": metadata.get("sender", "unknown"),
                        "created_at": metadata.get("created_at", ""),
                        "relevance_score": 1 - distance,
                        "metadata": metadata
                    })
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "results": search_results,
                    "query": query,
                    "total_results": len(search_results)
                }, indent=2)
            )]
        
        elif name == "claude_search_stats":
            # Get collection stats
            count = collection.count()
            
            return [types.TextContent(
                type="text", 
                text=json.dumps({
                    "total_messages": count,
                    "collection_name": "personal_claude_conversations",
                    "status": "active"
                }, indent=2)
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]
            
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Tool execution failed: {str(e)}"})
        )]

async def main():
    """Main server function"""
    logger.info("Starting Simple Claude Search MCP Server...")
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="claude-search",
                server_version="1.0.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability(listChanged=False)
                )
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())