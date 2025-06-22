#!/usr/bin/env python3
"""
Incremental Claude Data Import Script
Handles dated folder structure and prevents duplicates

This script processes dated export folders and only imports new conversations
while preserving existing data. It tracks import history to avoid duplicates.

Usage:
    python3 incremental_data_import.py --import_dir import/
    python3 incremental_data_import.py --import_dir import/data-2025-06-20-19-52-38/
    python3 incremental_data_import.py --force_reimport --import_dir import/data-2025-06-19-10-24-12/

Features:
- Automatic duplicate detection by conversation UUID
- Import history tracking with metadata
- Incremental updates without data loss
- Dated folder structure support
- Dry-run mode for testing
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import time
from datetime import datetime
import hashlib

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
    from search.semantic_search import UnifiedSearchEngine
    from utils.simple_chunker import SimpleChunker
    
    # Simple categorizer for conversation content
    class ConversationCategorizer:
        def __init__(self):
            pass
        
        def categorize_content(self, text: str) -> str:
            """Simple categorization based on content keywords"""
            text_lower = text.lower()
            
            # Programming/technical indicators
            if any(keyword in text_lower for keyword in ['function', 'code', 'python', 'javascript', 'sql', 'api', 'database', 'script']):
                return 'programming'
            
            # Business/finance indicators
            elif any(keyword in text_lower for keyword in ['budget', 'integration', 'ticket', 'project', 'sow', 'requirement']):
                return 'business_analysis'
            
            # AI/assistant indicators
            elif any(keyword in text_lower for keyword in ['claude', 'ai assistant', 'prompt', 'optimization']):
                return 'ai_assistance'
            
            # Default category
            else:
                return 'general'
    
    # Use SimpleChunker as our chunking mechanism
    class ConversationChunker:
        def __init__(self):
            self.simple_chunker = SimpleChunker(chunk_size=1200, overlap=200)
        
        def chunk_text(self, text: str) -> List[str]:
            """Simple text chunking method"""
            if len(text) <= 1200:
                return [text]
            
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + 1200, len(text))
                
                # Find sentence boundary near the end
                if end < len(text):
                    for i in range(end, max(start + 1100, start), -1):
                        if text[i] in '.!?':
                            end = i + 1
                            break
                
                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                
                start = end - 200 if end < len(text) else end  # 200 char overlap
            
            return chunks
            
except ImportError as e:
    print(f"Error importing local modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

class ImportTracker:
    """Tracks import history to prevent duplicates"""
    
    def __init__(self, tracking_file: str = "import_history.json"):
        self.tracking_file = tracking_file
        self.history = self._load_history()
    
    def _load_history(self) -> Dict[str, Any]:
        """Load import history from file"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Could not load import history: {e}")
        
        return {
            "imports": {},  # folder_name -> import_metadata
            "conversation_uuids": set(),  # Track all imported conversation UUIDs
            "project_uuids": set(),  # Track all imported project UUIDs
            "last_updated": None
        }
    
    def _save_history(self):
        """Save import history to file"""
        # Convert sets to lists for JSON serialization
        history_copy = self.history.copy()
        history_copy["conversation_uuids"] = list(self.history["conversation_uuids"])
        history_copy["project_uuids"] = list(self.history["project_uuids"])
        history_copy["last_updated"] = datetime.now().isoformat()
        
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(history_copy, f, indent=2)
        except Exception as e:
            print(f"{Fore.RED}❌ Could not save import history: {e}")
    
    def is_folder_imported(self, folder_name: str) -> bool:
        """Check if a folder has already been imported"""
        return folder_name in self.history["imports"]
    
    def is_conversation_imported(self, conversation_uuid: str) -> bool:
        """Check if a conversation UUID has already been imported"""
        return conversation_uuid in self.history["conversation_uuids"]
    
    def is_project_imported(self, project_uuid: str) -> bool:
        """Check if a project UUID has already been imported"""
        return project_uuid in self.history["project_uuids"]
    
    def mark_folder_imported(self, folder_name: str, metadata: Dict[str, Any]):
        """Mark a folder as imported with metadata"""
        self.history["imports"][folder_name] = metadata
        self._save_history()
    
    def add_conversation_uuid(self, conversation_uuid: str):
        """Add a conversation UUID to the tracking set"""
        self.history["conversation_uuids"].add(conversation_uuid)
    
    def add_project_uuid(self, project_uuid: str):
        """Add a project UUID to the tracking set"""
        self.history["project_uuids"].add(project_uuid)
    
    def get_import_summary(self) -> Dict[str, Any]:
        """Get summary of import history"""
        return {
            "total_folders_imported": len(self.history["imports"]),
            "total_conversations_tracked": len(self.history["conversation_uuids"]),
            "total_projects_tracked": len(self.history["project_uuids"]),
            "imported_folders": list(self.history["imports"].keys()),
            "last_updated": self.history.get("last_updated")
        }

class IncrementalClaudeDataProcessor:
    """Processes Claude data incrementally without duplicates"""
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8001):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.client = None
        self.categorizer = ConversationCategorizer()
        self.chunker = ConversationChunker()
        self.collection = None
        self.tracker = ImportTracker()
        
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

    def discover_import_folders(self, import_dir: str) -> List[Tuple[str, str]]:
        """Discover dated folders in import directory"""
        import_path = Path(import_dir)
        folders = []
        
        if not import_path.exists():
            print(f"{Fore.RED}❌ Import directory not found: {import_dir}")
            return []
        
        # Check if this is a direct data folder
        if any(f.name.endswith('.json') for f in import_path.iterdir() if f.is_file()):
            folder_name = import_path.name
            folders.append((folder_name, str(import_path)))
            print(f"{Fore.CYAN}📁 Found direct data folder: {folder_name}")
        else:
            # Look for dated subfolders
            for subfolder in import_path.iterdir():
                if subfolder.is_dir():
                    # Check if folder contains JSON files
                    json_files = list(subfolder.glob("*.json"))
                    if json_files:
                        folders.append((subfolder.name, str(subfolder)))
                        print(f"{Fore.CYAN}📁 Found dated folder: {subfolder.name}")
        
        # Sort by folder name (which includes date) for chronological processing
        folders.sort(key=lambda x: x[0])
        return folders

    def analyze_folder_contents(self, folder_path: str) -> Dict[str, Any]:
        """Analyze contents of a folder before importing"""
        folder_path_obj = Path(folder_path)
        analysis = {
            "projects_file": None,
            "conversations_file": None,
            "other_files": [],
            "total_projects": 0,
            "total_conversations": 0,
            "new_projects": 0,
            "new_conversations": 0
        }
        
        # Find JSON files
        for json_file in folder_path_obj.glob("*.json"):
            if json_file.name.lower() == "projects.json":
                analysis["projects_file"] = str(json_file)
            elif json_file.name.lower() == "conversations.json":
                analysis["conversations_file"] = str(json_file)
            else:
                analysis["other_files"].append(str(json_file))
        
        # Analyze projects file
        if analysis["projects_file"]:
            try:
                with open(analysis["projects_file"], 'r', encoding='utf-8') as f:
                    projects_data = json.load(f)
                if isinstance(projects_data, list):
                    analysis["total_projects"] = len(projects_data)
                    # Count new projects
                    for project in projects_data:
                        project_uuid = project.get('uuid', '')
                        if project_uuid and not self.tracker.is_project_imported(project_uuid):
                            analysis["new_projects"] += 1
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Could not analyze projects file: {e}")
        
        # Analyze conversations file
        if analysis["conversations_file"]:
            try:
                with open(analysis["conversations_file"], 'r', encoding='utf-8') as f:
                    conversations_data = json.load(f)
                if isinstance(conversations_data, list):
                    analysis["total_conversations"] = len(conversations_data)
                    # Count new conversations
                    for conversation in conversations_data:
                        conversation_uuid = conversation.get('uuid', '')
                        if conversation_uuid and not self.tracker.is_conversation_imported(conversation_uuid):
                            analysis["new_conversations"] += 1
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Could not analyze conversations file: {e}")
        
        return analysis

    def process_projects_incremental(self, projects_file: str, folder_name: str) -> Dict[str, Any]:
        """Process projects file incrementally"""
        print(f"{Fore.CYAN}📂 Processing projects file: {projects_file}")
        
        try:
            with open(projects_file, 'r', encoding='utf-8') as f:
                projects_data = json.load(f)
            
            if not isinstance(projects_data, list):
                return {"error": "Expected a list of projects in the JSON file"}
            
            processed_count = 0
            skipped_count = 0
            error_count = 0
            total_chunks = 0
            
            for project in projects_data:
                try:
                    project_uuid = project.get('uuid', '')
                    project_name = project.get('name', 'Unknown Project')
                    
                    if not project_uuid:
                        print(f"{Fore.YELLOW}⚠️ Project missing UUID: {project_name}")
                        continue
                    
                    # Check if already imported
                    if self.tracker.is_project_imported(project_uuid):
                        skipped_count += 1
                        print(f"{Fore.BLUE}⏭️ Skipping existing project: {project_name}")
                        continue
                    
                    # Process new project
                    result = self._process_single_project(project)
                    if result.get("success"):
                        processed_count += 1
                        total_chunks += result.get("chunks_created", 0)
                        self.tracker.add_project_uuid(project_uuid)
                        print(f"{Fore.GREEN}✅ Processed new project: {project_name}")
                    else:
                        error_count += 1
                        print(f"{Fore.RED}❌ Failed to process project: {project_name}")
                        print(f"   Error: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    error_count += 1
                    print(f"{Fore.RED}❌ Exception processing project: {e}")
            
            return {
                "success": True,
                "projects_processed": processed_count,
                "projects_skipped": skipped_count,
                "projects_failed": error_count,
                "total_chunks_created": total_chunks,
                "source_file": projects_file
            }
            
        except Exception as e:
            return {"error": f"Failed to process projects file: {e}"}

    def process_conversations_incremental(self, conversations_file: str, folder_name: str) -> Dict[str, Any]:
        """Process conversations file incrementally"""
        print(f"{Fore.CYAN}💬 Processing conversations file: {conversations_file}")
        
        try:
            with open(conversations_file, 'r', encoding='utf-8') as f:
                conversations_data = json.load(f)
            
            if not isinstance(conversations_data, list):
                return {"error": "Expected a list of conversations in the JSON file"}
            
            processed_count = 0
            skipped_count = 0
            error_count = 0
            total_chunks = 0
            
            for conversation in conversations_data:
                try:
                    conversation_uuid = conversation.get('uuid', '')
                    conversation_name = conversation.get('name', 'Untitled Conversation')
                    
                    if not conversation_uuid:
                        print(f"{Fore.YELLOW}⚠️ Conversation missing UUID: {conversation_name}")
                        continue
                    
                    # Check if already imported
                    if self.tracker.is_conversation_imported(conversation_uuid):
                        skipped_count += 1
                        print(f"{Fore.BLUE}⏭️ Skipping existing conversation: {conversation_name}")
                        continue
                    
                    # Process new conversation
                    result = self._process_single_conversation(conversation)
                    if result.get("success"):
                        processed_count += 1
                        total_chunks += result.get("chunks_created", 0)
                        self.tracker.add_conversation_uuid(conversation_uuid)
                        print(f"{Fore.GREEN}✅ Processed new conversation: {conversation_name}")
                    else:
                        error_count += 1
                        print(f"{Fore.RED}❌ Failed to process conversation: {conversation_name}")
                        print(f"   Error: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    error_count += 1
                    print(f"{Fore.RED}❌ Exception processing conversation: {e}")
            
            return {
                "success": True,
                "conversations_processed": processed_count,
                "conversations_skipped": skipped_count,
                "conversations_failed": error_count,
                "total_chunks_created": total_chunks,
                "source_file": conversations_file
            }
            
        except Exception as e:
            return {"error": f"Failed to process conversations file: {e}"}

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
                            category = self.categorizer.categorize_content(chunk)
                            
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
                                'chunk_id': f"{conversation_uuid}_{message.get('uuid', '')}_{i}",
                                'import_timestamp': datetime.now().isoformat()
                            }
                            
                            # Add to vector database using ChromaDB directly
                            chunk_id = metadata['chunk_id']
                            
                            self.collection.add(
                                documents=[chunk],
                                metadatas=[metadata],
                                ids=[chunk_id]
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

    def _process_single_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single conversation from conversations.json"""
        try:
            conversation_name = conversation.get('name', 'Untitled Conversation')
            conversation_uuid = conversation.get('uuid', '')
            messages = conversation.get('chat_messages', [])
            
            if not messages:
                return {"success": True, "chunks_created": 0, "note": "No messages found"}
            
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
                    category = self.categorizer.categorize_content(chunk)
                    
                    # Create metadata
                    metadata = {
                        'conversation_name': conversation_name,
                        'conversation_uuid': conversation_uuid,
                        'message_sender': sender,
                        'message_created_at': created_at,
                        'chunk_index': i,
                        'category': category,
                        'source_type': 'personal_claude_conversation',
                        'chunk_id': f"{conversation_uuid}_{message.get('uuid', '')}_{i}",
                        'import_timestamp': datetime.now().isoformat()
                    }
                    
                    # Add to vector database using ChromaDB directly
                    chunk_id = metadata['chunk_id']
                    
                    self.collection.add(
                        documents=[chunk],
                        metadatas=[metadata],
                        ids=[chunk_id]
                    )
                    
                    chunks_created += 1
            
            return {
                "success": True,
                "chunks_created": chunks_created
            }
            
        except Exception as e:
            return {"error": f"Failed to process conversation: {e}"}

    def process_folder(self, folder_path: str, folder_name: str, force_reimport: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """Process a complete dated folder"""
        print(f"\n{Fore.CYAN}📁 Processing folder: {folder_name}")
        print(f"📍 Path: {folder_path}")
        
        # Check if already imported
        if not force_reimport and self.tracker.is_folder_imported(folder_name):
            print(f"{Fore.BLUE}⏭️ Folder already imported, skipping. Use --force_reimport to re-process.")
            return {"skipped": True, "reason": "already_imported"}
        
        # Analyze folder contents
        analysis = self.analyze_folder_contents(folder_path)
        
        print(f"\n{Fore.CYAN}📊 Folder Analysis:")
        print(f"   Projects file: {analysis['projects_file'] or 'Not found'}")
        print(f"   Conversations file: {analysis['conversations_file'] or 'Not found'}")
        print(f"   Total projects: {analysis['total_projects']}")
        print(f"   New projects: {analysis['new_projects']}")
        print(f"   Total conversations: {analysis['total_conversations']}")
        print(f"   New conversations: {analysis['new_conversations']}")
        
        if dry_run:
            print(f"{Fore.YELLOW}🔍 DRY RUN: Would process {analysis['new_projects']} projects and {analysis['new_conversations']} conversations")
            return {"dry_run": True, "analysis": analysis}
        
        # Process files
        results = {
            "folder_name": folder_name,
            "folder_path": folder_path,
            "projects_result": None,
            "conversations_result": None,
            "total_chunks_created": 0,
            "start_time": time.time()
        }
        
        # Process projects file
        if analysis["projects_file"] and analysis["new_projects"] > 0:
            projects_result = self.process_projects_incremental(analysis["projects_file"], folder_name)
            results["projects_result"] = projects_result
            if projects_result.get("success"):
                results["total_chunks_created"] += projects_result.get("total_chunks_created", 0)
        
        # Process conversations file
        if analysis["conversations_file"] and analysis["new_conversations"] > 0:
            conversations_result = self.process_conversations_incremental(analysis["conversations_file"], folder_name)
            results["conversations_result"] = conversations_result
            if conversations_result.get("success"):
                results["total_chunks_created"] += conversations_result.get("total_chunks_created", 0)
        
        # Mark folder as imported
        folder_metadata = {
            "import_timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "results": results,
            "processing_time": time.time() - results["start_time"]
        }
        
        self.tracker.mark_folder_imported(folder_name, folder_metadata)
        
        return results

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
        description="Incrementally process Claude AI data with duplicate prevention"
    )
    
    # Input options
    parser.add_argument(
        '--import_dir',
        default='import/',
        help='Directory containing dated export folders (default: import/)'
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
    
    # Processing options
    parser.add_argument(
        '--force_reimport',
        action='store_true',
        help='Force re-import of already processed folders'
    )
    parser.add_argument(
        '--dry_run',
        action='store_true',
        help='Analyze what would be imported without actually importing'
    )
    parser.add_argument(
        '--show_history',
        action='store_true',
        help='Show import history and exit'
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = IncrementalClaudeDataProcessor(args.chroma_host, args.chroma_port)
    
    # Show import history if requested
    if args.show_history:
        print(f"{Fore.CYAN}📊 Import History Summary:")
        summary = processor.tracker.get_import_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
        return
    
    # Connect to database
    if not processor.connect():
        print(f"{Fore.RED}❌ Failed to connect to ChromaDB")
        sys.exit(1)
    
    # Discover folders to process
    folders = processor.discover_import_folders(args.import_dir)
    
    if not folders:
        print(f"{Fore.RED}❌ No dated folders found in {args.import_dir}")
        sys.exit(1)
    
    print(f"\n{Fore.GREEN}🎯 Found {len(folders)} folders to process:")
    for folder_name, folder_path in folders:
        status = "✅ New" if not processor.tracker.is_folder_imported(folder_name) else "⏭️ Imported"
        print(f"   {status} {folder_name}")
    
    # Process folders
    start_time = time.time()
    total_results = {
        "folders_processed": 0,
        "folders_skipped": 0,
        "total_chunks_created": 0,
        "errors": []
    }
    
    for folder_name, folder_path in folders:
        try:
            result = processor.process_folder(folder_path, folder_name, args.force_reimport, args.dry_run)
            
            if result.get("skipped"):
                total_results["folders_skipped"] += 1
            elif result.get("dry_run"):
                print(f"{Fore.YELLOW}🔍 Dry run completed for {folder_name}")
            else:
                total_results["folders_processed"] += 1
                total_results["total_chunks_created"] += result.get("total_chunks_created", 0)
                print(f"{Fore.GREEN}✅ Completed folder: {folder_name}")
        
        except Exception as e:
            error_msg = f"Failed to process folder {folder_name}: {e}"
            total_results["errors"].append(error_msg)
            print(f"{Fore.RED}❌ {error_msg}")
    
    processing_time = time.time() - start_time
    
    # Display final results
    print(f"\n{Fore.GREEN}🏁 Incremental import completed!")
    print(f"{Fore.CYAN}📊 Summary:")
    print(f"   Folders processed: {total_results['folders_processed']}")
    print(f"   Folders skipped: {total_results['folders_skipped']}")
    print(f"   Total new chunks: {total_results['total_chunks_created']:,}")
    print(f"   Processing time: {processing_time:.2f} seconds")
    
    if total_results["errors"]:
        print(f"{Fore.RED}❌ Errors encountered:")
        for error in total_results["errors"]:
            print(f"   {error}")
    
    # Show updated stats
    if not args.dry_run and total_results["total_chunks_created"] > 0:
        print(f"\n{Fore.CYAN}📊 Updated Collection Statistics:")
        stats = processor.get_collection_stats()
        total_docs = 0
        for collection_name, count in stats.items():
            print(f"   {collection_name}: {count:,} documents")
            total_docs += count
        
        print(f"   Total searchable chunks: {total_docs:,}")
        
        print(f"\n{Fore.GREEN}🎯 Your Claude conversation history is up to date!")
        print(f"{Fore.CYAN}💡 Next steps:")
        print(f"   1. Test search: python3 src/search/semantic_search.py --query 'your search term'")
        print(f"   2. Check import history: python3 incremental_data_import.py --show_history")

if __name__ == "__main__":
    main()