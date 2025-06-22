#!/usr/bin/env python3
"""
Enhanced MCP Server for Claude Conversation Search
Following MCP Tool Description Best Practices

A Model Context Protocol server that exposes Claude conversation search capabilities
with comprehensive tool descriptions, usage examples, and best practice implementations.

Enhanced Features:
- Comprehensive tool descriptions with use cases
- Parameter examples and recommendations  
- Category-based tool organization
- Performance optimization guidance
- Clear input/output schema definitions

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
logger = logging.getLogger("claude-search-mcp-enhanced")

# Server instance
server = Server("claude-search-enhanced")

# Global tool instance
search_tool: Optional[ClaudeSearchMCPTool] = None

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available MCP tools with enhanced descriptions following best practices"""
    return [
        types.Tool(
            name="claude_search",
            description="""🎯 Semantic search across Claude conversation history with vector similarity matching.

**Core Usage:**
• Find technical solutions: query="API authentication patterns", threshold=0.8
• Research patterns: query="error handling approaches", category="technical"  
• Discovery workflow: search → reconstruct → analyze solution

**Performance Optimized:**
• Focused: threshold 0.7+, limit 5-10, specific categories
• Broad: threshold 0.5-0.6, limit 20+, multiple categories
• Fast: category filters reduce scope, ~8K token limit

**Integration Chains:**
• Research: claude_search() → claude_reconstruct_conversation() → extract_solutions()
• Pattern Analysis: claude_search() → claude_search_stats() → insights
• Fallback: claude_search() || claude_find_conversations() || manual_browse()

**Error Handling:**
• No results: lower threshold, broaden categories, alternate queries
• Too many: increase threshold, add filters, specific terms""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query. Supports boolean operators (AND, OR), phrase matching, and question format.",
                        "examples": [
                            "machine learning optimization techniques",
                            "API security best practices AND authentication", 
                            "How do I implement OAuth2 with refresh tokens?",
                            "database performance optimization",
                            "legal compliance requirements"
                        ]
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return. Higher values provide more comprehensive results but may include less relevant matches. Recommended: 5-10 for focused results, 20+ for comprehensive analysis.",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter results by content category to narrow search scope to specific domains. Improves relevance and performance.",
                        "enum": [
                            "legal_compliance", "business_analysis", "technical_development",
                            "data_analytics", "communication", "research_strategy",
                            "project_management", "ai_assistance", "general"
                        ],
                        "category_descriptions": {
                            "technical_development": "Programming, architecture, APIs, databases, algorithms",
                            "legal_compliance": "GDPR, privacy, regulations, legal requirements, compliance",
                            "business_analysis": "Strategy, revenue, market analysis, ROI, business planning",
                            "data_analytics": "Data analysis, metrics, reporting, statistical analysis",
                            "ai_assistance": "AI tools, automation, machine learning applications",
                            "project_management": "Planning, task management, workflow, project coordination"
                        }
                    },
                    "source": {
                        "type": "string",
                        "description": "Filter by source type. 'conversation' for discussion threads, 'project' for project-related content.",
                        "enum": ["project", "conversation"]
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score (0.0-1.0) for results. Higher values return more precise matches. Recommendations: 0.85+ for precise search, 0.7+ for balanced search, 0.5+ for exploratory search.",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "recommendations": {
                            "precise_search": 0.85,
                            "balanced_search": 0.7,
                            "exploratory_search": 0.5
                        }
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="claude_find_conversations",
            description="""Discover complete conversations containing specific content or topics with full metadata.

Unlike claude_search which returns individual message chunks, this tool returns complete conversation metadata including titles, participant counts, message counts, creation dates, and relevance scores. 

Perfect for finding conversation threads to reconstruct or analyze in detail, understanding discussion context, or locating multi-turn conversations about complex topics.

**Use Cases:**
• Find conversation threads about specific projects
• Locate multi-turn discussions on complex topics  
• Discover conversations for detailed reconstruction
• Analyze conversation patterns and engagement metrics
• Research discussion threads by topic or timeframe

**Best Practices:**
• Use specific keywords for better thread discovery
• Lower limits (5-10) for quick browsing, higher (20+) for comprehensive discovery""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Content to search for in conversations. Use specific keywords or topics for better thread discovery.",
                        "examples": [
                            "API development best practices",
                            "machine learning project planning",
                            "legal compliance implementation",
                            "database optimization strategies"
                        ]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of conversations to return. Recommended: 5-10 for quick browsing, 20+ for comprehensive discovery.",
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
            description="""Reconstruct complete conversation threads by UUID with full message history and context.

Provides comprehensive conversation reconstruction including all messages with timestamps, participants, message ordering, and both raw data and human-readable formatted versions. Essential for detailed conversation analysis, decision context understanding, or comprehensive information extraction.

**Use Cases:**
• Review complete discussion threads with full context
• Understand decision-making processes and reasoning
• Analyze conversation flow and progression patterns  
• Extract comprehensive information from past discussions
• Study interaction patterns and communication effectiveness

**Output Includes:**
• Complete message history with timestamps
• Participant information and message attribution
• Formatted display for easy reading
• Conversation metadata and statistics""",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_uuid": {
                        "type": "string",
                        "description": "Unique identifier (UUID) of the conversation to reconstruct. Obtain from claude_find_conversations or claude_list_conversations.",
                        "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                        "examples": [
                            "a925c6cd-7cc1-4fd6-acc0-d29703fa9378",
                            "984505a6-ccec-4e59-8f14-3efe69c0efea"
                        ]
                    }
                },
                "required": ["conversation_uuid"]
            }
        ),
        types.Tool(
            name="claude_list_conversations",
            description="""Browse available conversations with comprehensive metadata for discovery and analysis.

Provides paginated listing of conversations with essential metadata including titles, creation dates, participant counts, message counts, categories, and activity status. Ideal for conversation discovery, database exploration, or understanding conversation patterns.

**Use Cases:**
• Browse conversation database for discovery
• Understand conversation volume and patterns
• Find conversations by recency or activity
• Analyze conversation engagement metrics
• Explore database contents systematically

**Metadata Provided:**
• Conversation titles and descriptions
• Creation and last activity timestamps  
• Participant and message counts
• Category classifications
• Relevance and engagement scores""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of conversations to list. Use smaller values (10-20) for quick browsing, larger values (50+) for comprehensive database exploration.",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 50,
                        "recommendations": {
                            "quick_browse": 10,
                            "standard_page": 25,
                            "comprehensive": 50
                        }
                    }
                }
            }
        ),
        types.Tool(
            name="claude_search_stats",
            description="""Retrieve comprehensive database statistics and available filters for search optimization.

Provides detailed insights into the conversation database including document counts, collection statistics, category distributions, date ranges, performance metrics, and available filter options. Essential for understanding search capabilities and optimizing query strategies.

**Use Cases:**
• Understand database scope and content distribution
• Optimize search strategies based on available data
• Analyze conversation patterns and growth trends
• Plan search approaches and filter strategies
• Monitor database health and performance metrics

**Statistics Provided:**
• Total documents, conversations, and projects
• Category and source type distributions
• Date ranges and temporal patterns
• Performance metrics and optimization data
• Available filters and search capabilities
• Growth trends and activity patterns""",
            inputSchema={
                "type": "object",
                "properties": {},
                "description": "No parameters required. Returns comprehensive database statistics and metadata."
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls with enhanced error handling and validation"""
    global search_tool
    
    # Initialize tool if needed
    if search_tool is None:
        search_tool = ClaudeSearchMCPTool()
        if not await search_tool.initialize():
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Failed to initialize Claude conversation search tool. Check ChromaDB connection.",
                    "troubleshooting": {
                        "check_chromadb": "Ensure ChromaDB server is running or embedded mode is available",
                        "verify_data": "Confirm conversation data has been imported",
                        "check_config": "Verify search tool configuration"
                    }
                }, indent=2)
            )]
    
    try:
        if name == "claude_search":
            query = arguments.get("query", "")
            n_results = arguments.get("n_results", 10)
            category = arguments.get("category")
            source = arguments.get("source")
            similarity_threshold = arguments.get("similarity_threshold")
            
            if not query.strip():
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Query parameter is required and cannot be empty",
                        "examples": [
                            "machine learning optimization techniques",
                            "API security best practices AND authentication",
                            "How do I implement OAuth2 with refresh tokens?"
                        ],
                        "tips": "Use specific keywords, boolean operators (AND, OR), or natural language questions"
                    }, indent=2)
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
            
            if not query.strip():
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Query parameter is required and cannot be empty",
                        "examples": [
                            "API development best practices",
                            "machine learning project planning",
                            "legal compliance implementation"
                        ]
                    }, indent=2)
                )]
            
            results = await search_tool.find_conversations_by_content(query, limit)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        
        elif name == "claude_reconstruct_conversation":
            conversation_uuid = arguments.get("conversation_uuid", "")
            
            if not conversation_uuid.strip():
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "conversation_uuid parameter is required",
                        "help": "Use claude_find_conversations or claude_list_conversations to find conversation UUIDs",
                        "uuid_format": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    }, indent=2)
                )]
            
            # Basic UUID format validation
            if len(conversation_uuid) != 36 or conversation_uuid.count('-') != 4:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Invalid UUID format",
                        "provided": conversation_uuid,
                        "expected_format": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                        "example": "a925c6cd-7cc1-4fd6-acc0-d29703fa9378"
                    }, indent=2)
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
                text=json.dumps({
                    "error": f"Unknown tool: {name}",
                    "available_tools": [
                        "claude_search",
                        "claude_find_conversations", 
                        "claude_reconstruct_conversation",
                        "claude_list_conversations",
                        "claude_search_stats"
                    ]
                }, indent=2)
            )]
    
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": f"Tool execution failed: {str(e)}",
                "tool": name,
                "arguments": arguments,
                "troubleshooting": {
                    "check_data": "Ensure conversation data is properly imported",
                    "verify_chromadb": "Confirm ChromaDB connection is working",
                    "validate_inputs": "Check that all required parameters are provided correctly"
                }
            }, indent=2)
        )]

async def main():
    """Main server function"""
    logger.info("Starting Enhanced Claude Search MCP Server...")
    logger.info("Following MCP Tool Description Best Practices")
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="claude-search-enhanced",
                server_version="2.0.0"
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())