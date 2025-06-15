#!/usr/bin/env python3
"""
chroma_import.py

Purpose:
  Imports chunked Claude project data into Chroma vector database
  for semantic search and retrieval.

Author: Bryan Thompson
Version: 1.0.0
Usage:
  python3 chroma_import.py --chunks_file chunks/project_chunks.json [--collection_name claude_projects]
"""

import argparse
import json
import os
from typing import List, Dict, Optional
import uuid

# Third-Party Libraries
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    print("Colorama not installed; install via 'pip install colorama' for colored output.")
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        BLUE = ""
        CYAN = ""
        MAGENTA = ""
    class Style:
        RESET_ALL = ""

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ChromaDB not installed. Install via: pip install chromadb")
    exit(1)

class ChromaProjectImporter:
    """Handles importing Claude project chunks into Chroma"""
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8001):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.client = None
        self.collection = None
        self.stats = {
            'chunks_imported': 0,
            'errors': [],
            'categories': {}
        }
    
    def connect(self) -> bool:
        """Connect to Chroma database"""
        try:
            print(Fore.BLUE + f"🔌 Connecting to Chroma at {self.chroma_host}:{self.chroma_port}" + Style.RESET_ALL)
            
            # Try HTTP connection first (for external Chroma server)
            try:
                self.client = chromadb.HttpClient(
                    host=self.chroma_host,
                    port=self.chroma_port,
                    settings=Settings(allow_reset=True)
                )
                # Test connection
                self.client.heartbeat()
                print(Fore.GREEN + "✔ Connected to Chroma HTTP server" + Style.RESET_ALL)
                return True
            except Exception as http_error:
                print(Fore.YELLOW + f"⚠ HTTP connection failed: {http_error}" + Style.RESET_ALL)
                
                # Fallback to persistent client (local file-based)
                print(Fore.BLUE + "🔄 Trying persistent client (local database)" + Style.RESET_ALL)
                
                # Create chroma_db directory if it doesn't exist
                db_path = os.path.join(os.getcwd(), "chroma_db")
                os.makedirs(db_path, exist_ok=True)
                
                self.client = chromadb.PersistentClient(
                    path=db_path,
                    settings=Settings(allow_reset=True)
                )
                print(Fore.GREEN + f"✔ Connected to local Chroma database at {db_path}" + Style.RESET_ALL)
                return True
                
        except Exception as e:
            print(Fore.RED + f"❌ Failed to connect to Chroma: {e}" + Style.RESET_ALL)
            return False
    
    def create_or_get_collection(self, collection_name: str) -> bool:
        """Create or get existing collection"""
        try:
            print(Fore.BLUE + f"📚 Setting up collection: {collection_name}" + Style.RESET_ALL)
            
            # Try to get existing collection first
            try:
                self.collection = self.client.get_collection(name=collection_name)
                existing_count = self.collection.count()
                print(Fore.YELLOW + f"⚠ Collection exists with {existing_count} documents" + Style.RESET_ALL)
                
                # Ask user if they want to delete and recreate
                response = input("Delete existing collection and recreate? (y/N): ").strip().lower()
                if response == 'y':
                    self.client.delete_collection(name=collection_name)
                    print(Fore.GREEN + "🗑️ Deleted existing collection" + Style.RESET_ALL)
                    raise Exception("Collection deleted, create new one")
                else:
                    print(Fore.GREEN + "✔ Using existing collection" + Style.RESET_ALL)
                    return True
                    
            except Exception:
                # Create new collection
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={
                        "description": "Claude AI project chunks for semantic search",
                        "created_by": "chroma_import.py",
                        "version": "1.0.0"
                    }
                )
                print(Fore.GREEN + f"✔ Created new collection: {collection_name}" + Style.RESET_ALL)
                return True
                
        except Exception as e:
            print(Fore.RED + f"❌ Error setting up collection: {e}" + Style.RESET_ALL)
            return False
    
    def prepare_documents(self, chunks: List[Dict]) -> tuple:
        """Prepare documents for Chroma import"""
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            # Extract content
            content = chunk.get('content', '').strip()
            if not content:
                continue
            
            # Generate ID
            chunk_id = chunk.get('chunk_id', str(uuid.uuid4()))
            
            # Prepare metadata
            metadata = {
                'project_uuid': chunk.get('project_uuid', ''),
                'project_name': chunk.get('project_name', ''),
                'chunk_type': chunk.get('chunk_type', ''),
                'category': chunk.get('category', ''),
                'created_at': chunk.get('created_at', ''),
                'updated_at': chunk.get('updated_at', ''),
                'creator_name': chunk.get('creator_name', ''),
                'chunk_index': chunk.get('chunk_index', 0),
                'total_chunks': chunk.get('total_chunks', 1),
                'content_length': len(content)
            }
            
            # Add additional metadata from the chunk
            chunk_metadata = chunk.get('metadata', {})
            if chunk_metadata:
                metadata.update({
                    'source': chunk_metadata.get('source', ''),
                    'filename': chunk_metadata.get('filename', ''),
                    'doc_index': chunk_metadata.get('doc_index', 0)
                })
            
            documents.append(content)
            metadatas.append(metadata)
            ids.append(chunk_id)
            
            # Update stats
            category = chunk.get('category', 'unknown')
            if category not in self.stats['categories']:
                self.stats['categories'][category] = 0
            self.stats['categories'][category] += 1
        
        return documents, metadatas, ids
    
    def import_chunks(self, chunks: List[Dict], batch_size: int = 100) -> bool:
        """Import chunks into Chroma in batches"""
        try:
            print(Fore.BLUE + f"📥 Preparing {len(chunks)} chunks for import" + Style.RESET_ALL)
            
            documents, metadatas, ids = self.prepare_documents(chunks)
            
            if not documents:
                print(Fore.RED + "❌ No valid documents to import" + Style.RESET_ALL)
                return False
            
            print(Fore.GREEN + f"✔ Prepared {len(documents)} documents" + Style.RESET_ALL)
            
            # Import in batches
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            for i in range(0, len(documents), batch_size):
                batch_num = (i // batch_size) + 1
                end_idx = min(i + batch_size, len(documents))
                
                batch_docs = documents[i:end_idx]
                batch_metas = metadatas[i:end_idx]
                batch_ids = ids[i:end_idx]
                
                print(Fore.CYAN + f"📤 Importing batch {batch_num}/{total_batches} ({len(batch_docs)} documents)" + Style.RESET_ALL)
                
                try:
                    self.collection.add(
                        documents=batch_docs,
                        metadatas=batch_metas,
                        ids=batch_ids
                    )
                    self.stats['chunks_imported'] += len(batch_docs)
                    
                except Exception as e:
                    error_msg = f"Error importing batch {batch_num}: {str(e)}"
                    print(Fore.RED + f"❌ {error_msg}" + Style.RESET_ALL)
                    self.stats['errors'].append(error_msg)
            
            print(Fore.GREEN + f"✔ Import completed! {self.stats['chunks_imported']} chunks imported" + Style.RESET_ALL)
            return True
            
        except Exception as e:
            print(Fore.RED + f"❌ Error during import: {e}" + Style.RESET_ALL)
            return False
    
    def verify_import(self) -> None:
        """Verify the import was successful"""
        try:
            print(Fore.BLUE + "🔍 Verifying import..." + Style.RESET_ALL)
            
            collection_count = self.collection.count()
            print(Fore.GREEN + f"✔ Collection contains {collection_count} documents" + Style.RESET_ALL)
            
            # Test a simple query
            try:
                results = self.collection.query(
                    query_texts=["project"],
                    n_results=3
                )
                print(Fore.GREEN + f"✔ Query test successful - found {len(results['documents'][0])} results" + Style.RESET_ALL)
                
                # Show sample results
                if results['documents'][0]:
                    print(Fore.YELLOW + "\nSample search results:" + Style.RESET_ALL)
                    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                        print(f"  {i+1}. Project: {metadata.get('project_name', 'N/A')}")
                        print(f"     Category: {metadata.get('category', 'N/A')}")
                        print(f"     Content: {doc[:100]}..." if len(doc) > 100 else f"     Content: {doc}")
                        print()
                        
            except Exception as e:
                print(Fore.YELLOW + f"⚠ Query test failed: {e}" + Style.RESET_ALL)
                
        except Exception as e:
            print(Fore.RED + f"❌ Error verifying import: {e}" + Style.RESET_ALL)
    
    def print_summary(self) -> None:
        """Print import summary"""
        print("\n" + "=" * 60)
        print(Fore.MAGENTA + "📊 IMPORT SUMMARY" + Style.RESET_ALL)
        print("=" * 60)
        print(f"Chunks imported: {self.stats['chunks_imported']}")
        print(f"Errors encountered: {len(self.stats['errors'])}")
        
        print("\n" + Fore.YELLOW + "Categories imported:" + Style.RESET_ALL)
        for category, count in sorted(self.stats['categories'].items()):
            print(f"  {category}: {count} chunks")
        
        if self.stats['errors']:
            print("\n" + Fore.RED + "Errors:" + Style.RESET_ALL)
            for error in self.stats['errors']:
                print(f"  - {error}")

def print_header():
    """Print script header"""
    print("=" * 60)
    print("🗄️ Chroma Database Importer 🗄️")
    print("Imports Claude project chunks into Chroma vector database")
    print("Version: 1.0.0")
    print("=" * 60 + "\n")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Import Claude project chunks into Chroma vector database"
    )
    parser.add_argument(
        "--chunks_file",
        required=True,
        help="Path to the project chunks JSON file"
    )
    parser.add_argument(
        "--collection_name",
        default="claude_project_chats",
        help="Name of the Chroma collection (default: claude_project_chats)"
    )
    parser.add_argument(
        "--chroma_host",
        default="localhost",
        help="Chroma server host (default: localhost)"
    )
    parser.add_argument(
        "--chroma_port",
        type=int,
        default=8001,
        help="Chroma server port (default: 8001)"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=100,
        help="Batch size for importing (default: 100)"
    )
    
    return parser.parse_args()

def main():
    """Main execution function"""
    print_header()
    args = parse_args()
    
    # Validate input file
    if not os.path.exists(args.chunks_file):
        print(Fore.RED + f"❌ Error: File not found: {args.chunks_file}" + Style.RESET_ALL)
        return 1
    
    try:
        # Load chunks
        print(Fore.BLUE + f"📂 Loading chunks from: {args.chunks_file}" + Style.RESET_ALL)
        with open(args.chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        if not isinstance(chunks, list):
            print(Fore.RED + "❌ Error: Expected JSON array of chunks" + Style.RESET_ALL)
            return 1
        
        print(Fore.GREEN + f"✔ Loaded {len(chunks)} chunks" + Style.RESET_ALL)
        
        # Import into Chroma
        importer = ChromaProjectImporter(args.chroma_host, args.chroma_port)
        
        if not importer.connect():
            return 1
        
        if not importer.create_or_get_collection(args.collection_name):
            return 1
        
        if not importer.import_chunks(chunks, args.batch_size):
            return 1
        
        importer.verify_import()
        importer.print_summary()
        
        print(Fore.GREEN + "\n🎉 Import completed successfully!" + Style.RESET_ALL)
        print(Fore.CYAN + f"Collection '{args.collection_name}' is ready for search!" + Style.RESET_ALL)
        return 0
        
    except Exception as e:
        print(Fore.RED + f"❌ Fatal error: {e}" + Style.RESET_ALL)
        return 1

if __name__ == "__main__":
    exit(main())