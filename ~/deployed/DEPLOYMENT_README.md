# Basic Deployment Package

This is a minimal deployment version of the My Claude Conversation API.

## Essential Files Included

### Core Application
- `src/` - Core Python modules (search, AI, utils)
- `api/` - API endpoints for Vercel deployment
- `mcp-tools/` - MCP server implementations

### Configuration
- `requirements.txt` - Python dependencies
- `vercel.json` - Vercel deployment configuration
- `claude_code_optimized_config.json` - Claude Code MCP configuration
- `setup.py` - Python package setup

### Startup Scripts
- `start_optimized_server.sh` - Start the optimized MCP server
- `simple_mcp_server.py` - Simple MCP server implementation

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start MCP Server:**
   ```bash
   ./start_optimized_server.sh
   ```

3. **Deploy to Vercel:**
   ```bash
   vercel deploy
   ```

## Files NOT Included (for minimal deployment)
- `venv/` - Virtual environment (recreate locally)
- `chroma_db/` - Database files (will be recreated)
- `import/` - Data import folders
- `tests/` - Test files
- `docs/` - Extended documentation
- `demo/` - Demo application

## Basic Usage

The core functionality includes:
- Semantic search with ChromaDB
- Redis caching for performance
- MCP tools for Claude Code integration
- Enhanced search with fuzzy matching and business vocabulary

For full functionality, you may need to set up:
- Redis server (for caching)
- ChromaDB (for vector search)
- Import your conversation data