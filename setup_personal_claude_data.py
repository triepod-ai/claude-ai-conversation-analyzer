#!/usr/bin/env python3
"""
Personal Claude Data Setup Script

This script helps you ingest your personal Claude AI conversation data
into the search system. It processes both projects.json and individual
conversation exports.

Usage:
    python3 setup_personal_claude_data.py --json_file /path/to/your/projects.json
    python3 setup_personal_claude_data.py --conversation_file /path/to/conversation.json
    python3 setup_personal_claude_data.py --data_dir /path/to/claude_exports/

Author: Bryan Thompson
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import time

# Third-party imports
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    import chromadb
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: uv pip install colorama chromadb")
    sys.exit(1)

# Add src to path for local imports
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    from ai.conversation_models import ConversationCategorizer, ConversationChunker, ConversationChunk
    from search.semantic_search import UnifiedSearchEngine
    from utils.simple_chunker import SimpleChunker
except ImportError as e:
    print(f"Error importing local modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class PersonalClaudeDataProcessor:
    """Processes personal Claude AI data for search indexing"""
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8001):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.client = None
        self.categorizer = ConversationCategorizer()
        self.chunker = ConversationChunker()
        self.collection = None
        
    def connect(self) -> bool:
        """Connect to ChromaDB"""
        try:
            # Try HTTP client first
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            self.client.heartbeat()
            print(f"{Fore.GREEN}✅ Connected to Chroma HTTP server at {self.chroma_host}:{self.chroma_port}")
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ HTTP connection failed: {e}")
            print(f"{Fore.CYAN}🔄 Falling back to persistent client...")
            
            try:
                self.client = chromadb.PersistentClient(path="./chroma_db")
                print(f"{Fore.GREEN}✅ Connected to local Chroma client")
            except Exception as e2:
                print(f"{Fore.RED}❌ Failed to connect to Chroma: {e2}")
                return False
        
        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name="personal_claude_conversations",
                metadata={"description": "Personal Claude conversation data"}
            )
            print(f"{Fore.GREEN}✅ Connected to collection: personal_claude_conversations")
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to create collection: {e}")
            return False
        
        return True
    
    def process_projects_file(self, json_file: str) -> Dict[str, Any]:
        """Process a Claude projects.json export file"""
        print(f"{Fore.CYAN}📂 Processing projects file: {json_file}")
        
        if not os.path.exists(json_file):
            return {"error": f"File not found: {json_file}"}
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                return {"error": "Expected a list of projects in the JSON file"}
            
            processed_count = 0
            error_count = 0
            total_chunks = 0
            
            for project in data:
                try:
                    result = self._process_single_project(project)
                    if result.get("success"):
                        processed_count += 1
                        total_chunks += result.get("chunks_created", 0)
                        print(f"{Fore.GREEN}✅ Processed project: {project.get('name', 'Unknown')}")
                    else:
                        error_count += 1
                        print(f"{Fore.RED}❌ Failed to process project: {project.get('name', 'Unknown')}")
                        print(f"   Error: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    error_count += 1
                    print(f"{Fore.RED}❌ Exception processing project: {e}")
            
            return {
                "success": True,
                "projects_processed": processed_count,
                "projects_failed": error_count,
                "total_chunks_created": total_chunks,
                "source_file": json_file
            }
            
        except Exception as e:
            return {"error": f"Failed to process projects file: {e}"}
    
    def _process_single_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single project from the export"""
        try:
            project_name = project.get('name', 'Unknown Project')
            project_uuid = project.get('uuid', '')
            conversations = project.get('chat_conversations', [])
            
            if not conversations:
                return {"success": True, "chunks_created": 0, "note": "No conversations found"}
            
            chunks_created = 0
            
            for conversation in conversations:
                try:
                    # Process conversation messages
                    messages = conversation.get('chat_messages', [])
                    conversation_uuid = conversation.get('uuid', '')
                    conversation_name = conversation.get('name', 'Untitled Conversation')
                    
                    for message in messages:
                        # Create conversation content
                        content = message.get('text', '')
                        sender = message.get('sender', 'unknown')
                        created_at = message.get('created_at', '')
                        
                        if not content.strip():
                            continue
                        
                        # Chunk the content
                        chunks = self.chunker.chunk_text(content)
                        
                        for i, chunk in enumerate(chunks):
                            # Categorize the chunk
                            category = self.analyzer.categorize_content(chunk)
                            
                            # Create metadata
                            metadata = {
                                'project_name': project_name,
                                'project_uuid': project_uuid,
                                'conversation_name': conversation_name,
                                'conversation_uuid': conversation_uuid,
                                'message_sender': sender,
                                'message_created_at': created_at,
                                'chunk_index': i,
                                'category': category,
                                'source_type': 'personal_claude_export',
                                'chunk_id': f"{conversation_uuid}_{message.get('uuid', '')}_{i}"
                            }
                            
                            # Add to vector database
                            collection_name = 'claude_project_chats'  # Use same collection as demo
                            self.vector_db.add_text_chunk(
                                text=chunk,
                                metadata=metadata,
                                collection_name=collection_name
                            )
                            
                            chunks_created += 1
                
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Error processing conversation in {project_name}: {e}")
                    continue
            
            return {
                "success": True,
                "chunks_created": chunks_created
            }
            
        except Exception as e:
            return {"error": f"Failed to process project: {e}"}
    
    def process_conversation_file(self, conversation_file: str) -> Dict[str, Any]:
        """Process a single conversation JSON file"""
        print(f"{Fore.CYAN}💬 Processing conversation file: {conversation_file}")
        
        if not os.path.exists(conversation_file):
            return {"error": f"File not found: {conversation_file}"}
        
        try:
            with open(conversation_file, 'r', encoding='utf-8') as f:
                conversation = json.load(f)
            
            # Extract conversation metadata
            conversation_name = conversation.get('name', 'Untitled Conversation')
            conversation_uuid = conversation.get('uuid', Path(conversation_file).stem)
            messages = conversation.get('chat_messages', [])
            
            if not messages:
                return {"error": "No messages found in conversation"}
            
            chunks_created = 0
            
            for message in messages:
                content = message.get('text', '')
                sender = message.get('sender', 'unknown')
                created_at = message.get('created_at', '')
                
                if not content.strip():
                    continue
                
                # Chunk the content
                chunks = self.chunker.chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    # Categorize the chunk
                    category = self.analyzer.categorize_content(chunk)
                    
                    # Create metadata
                    metadata = {
                        'conversation_name': conversation_name,
                        'conversation_uuid': conversation_uuid,
                        'message_sender': sender,
                        'message_created_at': created_at,
                        'chunk_index': i,
                        'category': category,
                        'source_type': 'personal_claude_conversation',
                        'chunk_id': f"{conversation_uuid}_{message.get('uuid', '')}_{i}"
                    }
                    
                    # Add to vector database
                    collection_name = 'claude_conversation_chats'
                    self.vector_db.add_text_chunk(
                        text=chunk,
                        metadata=metadata,
                        collection_name=collection_name
                    )
                    
                    chunks_created += 1
            
            return {
                "success": True,
                "conversation_name": conversation_name,
                "chunks_created": chunks_created,
                "source_file": conversation_file
            }
            
        except Exception as e:
            return {"error": f"Failed to process conversation file: {e}"}
    
    def process_data_directory(self, data_dir: str) -> Dict[str, Any]:
        """Process all JSON files in a directory"""
        print(f"{Fore.CYAN}📁 Processing data directory: {data_dir}")
        
        if not os.path.exists(data_dir):
            return {"error": f"Directory not found: {data_dir}"}
        
        data_path = Path(data_dir)
        json_files = list(data_path.glob("*.json"))
        
        if not json_files:
            return {"error": "No JSON files found in directory"}
        
        processed_files = 0
        failed_files = 0
        total_chunks = 0
        results = []
        
        for json_file in json_files:
            try:
                # Try to determine if it's a projects file or conversation file
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list) and len(data) > 0 and 'chat_conversations' in data[0]:
                    # Projects file
                    result = self.process_projects_file(str(json_file))
                elif isinstance(data, dict) and 'chat_messages' in data:
                    # Single conversation file
                    result = self.process_conversation_file(str(json_file))
                else:
                    print(f"{Fore.YELLOW}⚠️ Skipping unrecognized format: {json_file}")
                    continue
                
                if result.get("success"):
                    processed_files += 1
                    total_chunks += result.get("chunks_created", 0)
                    results.append(result)
                else:
                    failed_files += 1
                    print(f"{Fore.RED}❌ Failed to process: {json_file}")
                    print(f"   Error: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                failed_files += 1
                print(f"{Fore.RED}❌ Exception processing {json_file}: {e}")
        
        return {
            "success": True,
            "files_processed": processed_files,
            "files_failed": failed_files,
            "total_chunks_created": total_chunks,
            "source_directory": data_dir,
            "details": results
        }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collections"""
        try:
            collections = self.client.list_collections()
            stats = {}
            
            for collection in collections:
                count = collection.count()
                stats[collection.name] = count
            
            return stats
        except Exception as e:
            return {"error": f"Failed to get collection stats: {e}"}

def main():
    """Main function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Process personal Claude AI data for search indexing"
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--json_file',
        help='Path to Claude projects.json export file'
    )
    input_group.add_argument(
        '--conversation_file',
        help='Path to single conversation JSON file'
    )
    input_group.add_argument(
        '--data_dir',
        help='Directory containing Claude export JSON files'
    )
    
    # Connection options
    parser.add_argument(
        '--chroma_host',
        default='localhost',
        help='Chroma server host (default: localhost)'
    )
    parser.add_argument(
        '--chroma_port',
        type=int,
        default=8001,
        help='Chroma server port (default: 8001)'
    )
    
    # Options
    parser.add_argument(
        '--stats_only',
        action='store_true',
        help='Only show collection statistics, don\'t process data'
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = PersonalClaudeDataProcessor(args.chroma_host, args.chroma_port)
    
    # Connect to database
    if not processor.connect():
        print(f"{Fore.RED}❌ Failed to connect to ChromaDB")
        sys.exit(1)
    
    # Show current stats if requested
    if args.stats_only:
        print(f"{Fore.CYAN}📊 Current Collection Statistics:")
        stats = processor.get_collection_stats()
        for collection_name, count in stats.items():
            print(f"   {collection_name}: {count:,} documents")
        return
    
    # Process data
    start_time = time.time()
    
    if args.json_file:
        result = processor.process_projects_file(args.json_file)
    elif args.conversation_file:
        result = processor.process_conversation_file(args.conversation_file)
    elif args.data_dir:
        result = processor.process_data_directory(args.data_dir)
    
    processing_time = time.time() - start_time
    
    # Display results
    if result.get("error"):
        print(f"{Fore.RED}❌ Processing failed: {result['error']}")
        sys.exit(1)
    
    print(f"\n{Fore.GREEN}✅ Processing completed successfully!")
    print(f"{Fore.CYAN}📊 Summary:")
    
    if args.json_file:
        print(f"   Projects processed: {result.get('projects_processed', 0)}")
        print(f"   Projects failed: {result.get('projects_failed', 0)}")
    elif args.conversation_file:
        print(f"   Conversation: {result.get('conversation_name', 'Unknown')}")
    elif args.data_dir:
        print(f"   Files processed: {result.get('files_processed', 0)}")
        print(f"   Files failed: {result.get('files_failed', 0)}")
    
    print(f"   Total chunks created: {result.get('total_chunks_created', 0):,}")
    print(f"   Processing time: {processing_time:.2f} seconds")
    
    # Show updated stats
    print(f"\n{Fore.CYAN}📊 Updated Collection Statistics:")
    stats = processor.get_collection_stats()
    total_docs = 0
    for collection_name, count in stats.items():
        print(f"   {collection_name}: {count:,} documents")
        total_docs += count
    
    print(f"   Total searchable chunks: {total_docs:,}")
    
    print(f"\n{Fore.GREEN}🎯 Your personal Claude conversation history is now searchable!")
    print(f"{Fore.CYAN}💡 Next steps:")
    print(f"   1. Test search: python3 src/search/semantic_search.py --query 'your search term'")
    print(f"   2. Start MCP server: python3 mcp-tools/mcp_server.py")
    print(f"   3. Use with Claude Code for seamless conversation search")

if __name__ == "__main__":
    main()