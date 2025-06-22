#!/usr/bin/env python3
"""
Simple Claude Data Import Script

Simple script to import Claude conversation data into ChromaDB
"""

import json
import sys
import os
from pathlib import Path

# Third-party imports
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    import chromadb
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: uv pip install colorama chromadb")
    sys.exit(1)

def import_conversations_data(json_file: str):
    """Import conversations.json data into ChromaDB"""
    print(f"{Fore.CYAN}📂 Importing Claude conversation data from: {json_file}")
    
    # Load the data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            conversations_data = json.load(f)
        print(f"{Fore.GREEN}✅ Loaded {len(conversations_data)} conversations")
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to load file: {e}")
        return False
    
    # Connect to ChromaDB
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        print(f"{Fore.GREEN}✅ Connected to ChromaDB")
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to connect to ChromaDB: {e}")
        return False
    
    # Create collection
    try:
        collection = client.get_or_create_collection(
            name="personal_claude_conversations",
            metadata={"description": "Personal Claude conversation data"}
        )
        print(f"{Fore.GREEN}✅ Created/connected to collection")
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to create collection: {e}")
        return False
    
    # Process and import data
    total_messages = 0
    total_conversations = 0
    
    documents = []
    metadatas = []
    ids = []
    
    for conversation in conversations_data:
        conversation_uuid = conversation.get('uuid', '')
        conversation_name = conversation.get('name', 'Untitled')
        messages = conversation.get('chat_messages', [])
        
        print(f"{Fore.CYAN}🔄 Processing conversation: {conversation_name} ({len(messages)} messages)")
        
        total_conversations += 1
        
        for msg_idx, message in enumerate(messages):
                content = message.get('text', '')
                sender = message.get('sender', 'unknown')
                created_at = message.get('created_at', '')
                message_uuid = message.get('uuid', '')
                
                if not content.strip():
                    continue
                
                # Create document ID
                doc_id = f"{conversation_uuid}_{message_uuid}_{msg_idx}"
                
                # Prepare metadata
                metadata = {
                    'conversation_uuid': conversation_uuid,
                    'conversation_name': conversation_name,
                    'message_uuid': message_uuid,
                    'sender': sender,
                    'created_at': created_at,
                    'message_index': msg_idx,
                    'total_messages': len(messages)
                }
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(doc_id)
                
                total_messages += 1
                
                # Batch insert every 1000 messages
                if len(documents) >= 1000:
                    try:
                        collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        print(f"{Fore.GREEN}✅ Inserted batch of {len(documents)} messages")
                        documents = []
                        metadatas = []
                        ids = []
                    except Exception as e:
                        print(f"{Fore.RED}❌ Failed to insert batch: {e}")
    
    # Insert remaining documents
    if documents:
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"{Fore.GREEN}✅ Inserted final batch of {len(documents)} messages")
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to insert final batch: {e}")
    
    print(f"\n{Fore.GREEN}🎉 Import completed!")
    print(f"📊 Total conversations: {total_conversations}")
    print(f"📊 Total messages imported: {total_messages}")
    
    return True

def main():
    print("=" * 60)
    print("🚀 Simple Claude Data Import")
    print("=" * 60)
    
    # Get the import file
    import_file = "import/conversations.json"
    
    if not os.path.exists(import_file):
        print(f"{Fore.RED}❌ Import file not found: {import_file}")
        print("Make sure your projects.json is in the import/ folder")
        return False
    
    success = import_conversations_data(import_file)
    
    if success:
        print(f"\n{Fore.GREEN}✅ Import successful!")
        print(f"{Fore.CYAN}💡 You can now test the MCP server:")
        print(f"   python3 mcp-tools/mcp_server.py")
        return True
    else:
        print(f"\n{Fore.RED}❌ Import failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)