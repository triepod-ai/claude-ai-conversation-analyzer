#!/usr/bin/env python3
"""
conversation_reconstructor.py

Purpose:
  Reconstruct complete conversations from chunked data in chronological order.
  Provides capabilities to view full conversation flows with proper message boundaries.

Author: Bryan Thompson
Version: 1.0.0
Usage:
  from conversation_reconstructor import ConversationReconstructor
  reconstructor = ConversationReconstructor()
  conversation = reconstructor.reconstruct_conversation("uuid-here")
"""

import json
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Third-Party Libraries
try:
    import chromadb
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: uv pip install colorama chromadb")
    sys.exit(1)

@dataclass
class ReconstructedMessage:
    """Represents a complete message reconstructed from chunks"""
    message_uuid: str
    message_index: int
    sender: str  # 'human' or 'assistant'
    content: str
    created_at: str
    updated_at: str
    attachments_count: int
    chunk_count: int
    category: str

@dataclass
class ReconstructedConversation:
    """Represents a complete conversation with all messages in order"""
    conversation_uuid: str
    conversation_name: str
    total_messages: int
    total_chunks: int
    messages: List[ReconstructedMessage]
    created_at: str
    updated_at: str
    account_uuid: str
    categories: List[str]
    human_messages: int
    assistant_messages: int
    attachments_count: int
    avg_message_length: float

class ConversationReconstructor:
    """Reconstructs complete conversations from chunked search results"""
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8001):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.client = None
        self.conversation_collection = None
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize Chroma client and collection"""
        try:
            # Try HTTP client first
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            
            # Test connection
            self.client.heartbeat()
            self.conversation_collection = self.client.get_collection("claude_conversation_chats")
            print(f"{Fore.GREEN}✓ Connected to Chroma HTTP server at {self.chroma_host}:{self.chroma_port}")
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ HTTP connection failed: {e}")
            print(f"{Fore.CYAN}→ Attempting local persistent client...")
            
            try:
                self.client = chromadb.PersistentClient()
                self.conversation_collection = self.client.get_collection("claude_conversation_chats")
                print(f"{Fore.GREEN}✓ Connected to local Chroma client")
            except Exception as e2:
                print(f"{Fore.RED}✗ Failed to connect to Chroma: {e2}")
                raise
    
    def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List available conversations with metadata"""
        try:
            # Check if data was imported with conversation_uuid or needs alternative approach
            sample = self.conversation_collection.get(limit=1, include=["metadatas"])
            if not sample['metadatas']:
                return []
            
            has_conversation_uuid = 'conversation_uuid' in sample['metadatas'][0]
            
            if has_conversation_uuid:
                # Use proper conversation metadata
                results = self.conversation_collection.get(
                    limit=1000,  # Get more to find unique conversations
                    include=["metadatas"]
                )
                
                # Extract unique conversations
                conversations = {}
                for metadata in results['metadatas']:
                    conv_uuid = metadata.get('conversation_uuid')
                    if conv_uuid and conv_uuid not in conversations:
                        conversations[conv_uuid] = {
                            'conversation_uuid': conv_uuid,
                            'conversation_name': metadata.get('conversation_name', 'Unknown'),
                            'message_count': 0,
                            'chunk_count': 0,
                            'categories': set()
                        }
                    
                    if conv_uuid:
                        conversations[conv_uuid]['chunk_count'] += 1
                        if metadata.get('category'):
                            conversations[conv_uuid]['categories'].add(metadata.get('category'))
                
                # Convert to list and add more details
                conversation_list = []
                for conv_data in conversations.values():
                    conv_data['categories'] = list(conv_data['categories'])
                    conversation_list.append(conv_data)
                
                # Sort by name and limit results
                conversation_list.sort(key=lambda x: x['conversation_name'])
                return conversation_list[:limit]
            else:
                # Fallback: Load from original conversation chunks file
                print(f"{Fore.YELLOW}⚠️ Database has simplified metadata. Loading from conversation chunks file...")
                return self._load_conversations_from_file(limit)
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error listing conversations: {e}")
            return []
    
    def _load_conversations_from_file(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Load conversation list from chunks file as fallback"""
        try:
            import json
            import os
            
            chunks_file = 'chunks_conversations/conversation_chunks.json'
            if not os.path.exists(chunks_file):
                chunks_file = '/home/bryan/lodestar-ada/chunks_conversations/conversation_chunks.json'
            
            if not os.path.exists(chunks_file):
                print(f"{Fore.YELLOW}⚠️ Conversation chunks file not found")
                return []
            
            with open(chunks_file, 'r') as f:
                chunks = json.load(f)
            
            # Extract unique conversations
            conversations = {}
            for chunk in chunks:
                conv_uuid = chunk.get('conversation_uuid')
                if conv_uuid and conv_uuid not in conversations:
                    # Get first few chars of content as preview if name is empty
                    conv_name = chunk.get('conversation_name', '').strip()
                    if not conv_name:
                        content_preview = chunk.get('content', '')[:50].strip()
                        conv_name = f"Conversation: {content_preview}..." if content_preview else "Unknown Conversation"
                    
                    conversations[conv_uuid] = {
                        'conversation_uuid': conv_uuid,
                        'conversation_name': conv_name,
                        'message_count': 0,
                        'chunk_count': 0,
                        'categories': set()
                    }
                
                if conv_uuid:
                    conversations[conv_uuid]['chunk_count'] += 1
                    if chunk.get('category'):
                        conversations[conv_uuid]['categories'].add(chunk.get('category'))
            
            # Convert to list
            conversation_list = []
            for conv_data in conversations.values():
                conv_data['categories'] = list(conv_data['categories'])
                conversation_list.append(conv_data)
            
            # Sort by name and limit results
            conversation_list.sort(key=lambda x: x['conversation_name'])
            return conversation_list[:limit]
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error loading conversations from file: {e}")
            return []
    
    def _reconstruct_from_file(self, conversation_uuid: str) -> Optional[ReconstructedConversation]:
        """Reconstruct conversation from chunks file as fallback"""
        try:
            import json
            import os
            
            chunks_file = 'chunks_conversations/conversation_chunks.json'
            if not os.path.exists(chunks_file):
                chunks_file = '/home/bryan/lodestar-ada/chunks_conversations/conversation_chunks.json'
            
            if not os.path.exists(chunks_file):
                print(f"{Fore.RED}✗ Conversation chunks file not found")
                return None
            
            with open(chunks_file, 'r') as f:
                all_chunks = json.load(f)
            
            # Filter chunks for this conversation
            conversation_chunks = [
                chunk for chunk in all_chunks 
                if chunk.get('conversation_uuid') == conversation_uuid
            ]
            
            if not conversation_chunks:
                print(f"{Fore.YELLOW}⚠ No chunks found for conversation: {conversation_uuid}")
                return None
            
            print(f"{Fore.CYAN}→ Found {len(conversation_chunks)} chunks for conversation")
            
            # Group chunks by message UUID and sort
            messages_data = {}
            conversation_metadata = None
            
            for chunk in conversation_chunks:
                message_uuid = chunk.get('message_uuid')
                if not message_uuid:
                    continue
                
                # Store conversation metadata from first chunk
                if conversation_metadata is None:
                    conversation_metadata = chunk
                
                # Initialize message if not seen
                if message_uuid not in messages_data:
                    messages_data[message_uuid] = {
                        'message_uuid': message_uuid,
                        'message_index': chunk.get('message_index', 0),
                        'sender': chunk.get('sender', ''),
                        'created_at': chunk.get('created_at', ''),
                        'updated_at': chunk.get('updated_at', ''),
                        'category': chunk.get('category', 'general'),
                        'attachments_count': 0,  # Can't get this from current structure
                        'chunks': []
                    }
                
                # Add chunk to message
                chunk_info = {
                    'chunk_index': chunk.get('chunk_index', 0),
                    'content': chunk.get('content', ''),
                    'chunk_type': chunk.get('chunk_type', 'message')
                }
                messages_data[message_uuid]['chunks'].append(chunk_info)
            
            # Reconstruct messages by assembling chunks in order
            reconstructed_messages = []
            
            for message_data in messages_data.values():
                # Sort chunks by index and assemble content
                message_data['chunks'].sort(key=lambda x: x['chunk_index'])
                
                # Assemble content from chunks
                content_parts = []
                for chunk in message_data['chunks']:
                    content_parts.append(chunk['content'])
                
                # Join with proper spacing
                full_content = ' '.join(content_parts)
                
                # Create reconstructed message
                message = ReconstructedMessage(
                    message_uuid=message_data['message_uuid'],
                    message_index=message_data['message_index'],
                    sender=message_data['sender'],
                    content=full_content,
                    created_at=message_data['created_at'],
                    updated_at=message_data['updated_at'],
                    attachments_count=message_data['attachments_count'],
                    chunk_count=len(message_data['chunks']),
                    category=message_data['category']
                )
                
                reconstructed_messages.append(message)
            
            # Sort messages by message_index to maintain chronological order
            reconstructed_messages.sort(key=lambda x: x.message_index)
            
            # Calculate conversation statistics
            human_messages = sum(1 for msg in reconstructed_messages if msg.sender == 'human')
            assistant_messages = sum(1 for msg in reconstructed_messages if msg.sender == 'assistant')
            total_attachments = sum(msg.attachments_count for msg in reconstructed_messages)
            
            # Calculate average message length
            total_length = sum(len(msg.content) for msg in reconstructed_messages)
            avg_length = total_length / len(reconstructed_messages) if reconstructed_messages else 0
            
            # Extract unique categories
            categories = list(set(msg.category for msg in reconstructed_messages))
            
            # Create reconstructed conversation
            conversation = ReconstructedConversation(
                conversation_uuid=conversation_uuid,
                conversation_name=conversation_metadata.get('conversation_name', 'Unknown Conversation'),
                total_messages=len(reconstructed_messages),
                total_chunks=len(conversation_chunks),
                messages=reconstructed_messages,
                created_at=conversation_metadata.get('created_at', ''),
                updated_at=conversation_metadata.get('updated_at', ''),
                account_uuid=conversation_metadata.get('account_uuid', ''),
                categories=categories,
                human_messages=human_messages,
                assistant_messages=assistant_messages,
                attachments_count=total_attachments,
                avg_message_length=avg_length
            )
            
            print(f"{Fore.GREEN}✓ Successfully reconstructed conversation: {conversation.conversation_name}")
            print(f"  {len(reconstructed_messages)} messages, {len(conversation_chunks)} chunks")
            
            return conversation
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error reconstructing conversation from file: {e}")
            return None
    
    def reconstruct_conversation(self, conversation_uuid: str) -> Optional[ReconstructedConversation]:
        """Reconstruct a complete conversation from its UUID"""
        try:
            # Check if database has conversation_uuid metadata
            sample = self.conversation_collection.get(limit=1, include=["metadatas"])
            has_conversation_uuid = sample['metadatas'] and 'conversation_uuid' in sample['metadatas'][0]
            
            if has_conversation_uuid:
                # Query all chunks for this conversation from database
                results = self.conversation_collection.get(
                    where={"conversation_uuid": conversation_uuid},
                    include=["documents", "metadatas"]
                )
                
                if not results['documents']:
                    print(f"{Fore.YELLOW}⚠ No chunks found for conversation: {conversation_uuid}")
                    return None
            else:
                # Fallback: Load from file and find matching chunks
                print(f"{Fore.YELLOW}⚠️ Using file-based reconstruction for conversation: {conversation_uuid}")
                return self._reconstruct_from_file(conversation_uuid)
            
            print(f"{Fore.CYAN}→ Found {len(results['documents'])} chunks for conversation")
            
            # Group chunks by message UUID and sort
            messages_data = {}
            conversation_metadata = None
            
            for i, (document, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                message_uuid = metadata.get('message_uuid')
                if not message_uuid:
                    continue
                
                # Store conversation metadata from first chunk
                if conversation_metadata is None:
                    conversation_metadata = metadata
                
                # Initialize message if not seen
                if message_uuid not in messages_data:
                    messages_data[message_uuid] = {
                        'message_uuid': message_uuid,
                        'message_index': metadata.get('message_index', 0),
                        'sender': metadata.get('message_sender', ''),
                        'created_at': metadata.get('message_created_at', ''),
                        'updated_at': metadata.get('updated_at', ''),
                        'category': metadata.get('category', 'general'),
                        'attachments_count': metadata.get('attachment_count', 0),
                        'chunks': []
                    }
                
                # Add chunk to message
                chunk_info = {
                    'chunk_index': metadata.get('chunk_index', 0),
                    'content': document,
                    'chunk_type': metadata.get('chunk_type', 'message')
                }
                messages_data[message_uuid]['chunks'].append(chunk_info)
            
            # Reconstruct messages by assembling chunks in order
            reconstructed_messages = []
            
            for message_data in messages_data.values():
                # Sort chunks by index and assemble content
                message_data['chunks'].sort(key=lambda x: x['chunk_index'])
                
                # Assemble content from chunks
                content_parts = []
                for chunk in message_data['chunks']:
                    content_parts.append(chunk['content'])
                
                # Join with proper spacing
                full_content = ' '.join(content_parts)
                
                # Create reconstructed message
                message = ReconstructedMessage(
                    message_uuid=message_data['message_uuid'],
                    message_index=message_data['message_index'],
                    sender=message_data['sender'],
                    content=full_content,
                    created_at=message_data['created_at'],
                    updated_at=message_data['updated_at'],
                    attachments_count=message_data['attachments_count'],
                    chunk_count=len(message_data['chunks']),
                    category=message_data['category']
                )
                
                reconstructed_messages.append(message)
            
            # Sort messages by message_index to maintain chronological order
            reconstructed_messages.sort(key=lambda x: x.message_index)
            
            # Calculate conversation statistics
            human_messages = sum(1 for msg in reconstructed_messages if msg.sender == 'human')
            assistant_messages = sum(1 for msg in reconstructed_messages if msg.sender == 'assistant')
            total_attachments = sum(msg.attachments_count for msg in reconstructed_messages)
            
            # Calculate average message length
            total_length = sum(len(msg.content) for msg in reconstructed_messages)
            avg_length = total_length / len(reconstructed_messages) if reconstructed_messages else 0
            
            # Extract unique categories
            categories = list(set(msg.category for msg in reconstructed_messages))
            
            # Create reconstructed conversation
            conversation = ReconstructedConversation(
                conversation_uuid=conversation_uuid,
                conversation_name=conversation_metadata.get('conversation_name', 'Unknown Conversation'),
                total_messages=len(reconstructed_messages),
                total_chunks=len(results['documents']),
                messages=reconstructed_messages,
                created_at=conversation_metadata.get('created_at', ''),
                updated_at=conversation_metadata.get('updated_at', ''),
                account_uuid=conversation_metadata.get('account_uuid', ''),
                categories=categories,
                human_messages=human_messages,
                assistant_messages=assistant_messages,
                attachments_count=total_attachments,
                avg_message_length=avg_length
            )
            
            print(f"{Fore.GREEN}✓ Successfully reconstructed conversation: {conversation.conversation_name}")
            print(f"  {len(reconstructed_messages)} messages, {len(results['documents'])} chunks")
            
            return conversation
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error reconstructing conversation: {e}")
            return None
    
    def find_conversations_by_content(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Find conversations containing specific content"""
        try:
            # Search for relevant chunks
            results = self.conversation_collection.query(
                query_texts=[query],
                n_results=n_results * 3,  # Get more to find unique conversations
                include=["metadatas", "distances"]
            )
            
            # Extract unique conversations with relevance scores
            conversations = {}
            
            for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
                conv_uuid = metadata.get('conversation_uuid')
                if conv_uuid and conv_uuid not in conversations:
                    conversations[conv_uuid] = {
                        'conversation_uuid': conv_uuid,
                        'conversation_name': metadata.get('conversation_name', 'Unknown'),
                        'relevance_score': round((1 - distance) * 100, 2),
                        'category': metadata.get('category', 'general'),
                        'message_count': 0,
                        'chunk_count': 1
                    }
                elif conv_uuid:
                    # Update with better relevance score if this chunk is more relevant
                    current_score = conversations[conv_uuid]['relevance_score']
                    new_score = round((1 - distance) * 100, 2)
                    if new_score > current_score:
                        conversations[conv_uuid]['relevance_score'] = new_score
                    conversations[conv_uuid]['chunk_count'] += 1
            
            # Convert to list and sort by relevance
            conversation_list = list(conversations.values())
            conversation_list.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return conversation_list[:n_results]
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error finding conversations: {e}")
            return []
    
    def format_conversation_for_display(self, conversation: ReconstructedConversation, 
                                      show_metadata: bool = True) -> str:
        """Format a reconstructed conversation for human-readable display"""
        output = []
        
        # Header
        output.append(f"{Fore.CYAN}{'='*80}")
        output.append(f"{Fore.CYAN}CONVERSATION: {conversation.conversation_name}")
        output.append(f"{Fore.CYAN}{'='*80}")
        
        if show_metadata:
            # Metadata
            output.append(f"\n{Fore.YELLOW}📊 CONVERSATION DETAILS:")
            output.append(f"  UUID: {conversation.conversation_uuid}")
            output.append(f"  Total Messages: {conversation.total_messages}")
            output.append(f"  Total Chunks: {conversation.total_chunks}")
            output.append(f"  Human Messages: {conversation.human_messages}")
            output.append(f"  Assistant Messages: {conversation.assistant_messages}")
            output.append(f"  Categories: {', '.join(conversation.categories)}")
            output.append(f"  Created: {conversation.created_at}")
            output.append(f"  Avg Message Length: {conversation.avg_message_length:.0f} chars")
            
        # Messages
        output.append(f"\n{Fore.YELLOW}💬 MESSAGES:")
        output.append(f"{Fore.CYAN}{'-'*80}")
        
        for i, message in enumerate(conversation.messages, 1):
            # Message header
            sender_icon = "👤" if message.sender == "human" else "🤖"
            sender_color = Fore.GREEN if message.sender == "human" else Fore.BLUE
            
            output.append(f"\n{sender_color}{sender_icon} MESSAGE {i}/{conversation.total_messages} - {message.sender.upper()}")
            output.append(f"{Fore.CYAN}📅 {message.created_at} | 📂 {message.category} | 📎 {message.attachments_count} attachments")
            output.append(f"{Fore.CYAN}{'-'*60}")
            
            # Message content (with word wrapping)
            content_lines = self._wrap_text(message.content, width=76)
            for line in content_lines:
                output.append(f"{Style.RESET_ALL}{line}")
            
            output.append(f"{Fore.CYAN}{'-'*60}")
        
        output.append(f"\n{Fore.CYAN}{'='*80}")
        output.append(f"{Fore.GREEN}✓ End of conversation")
        
        return '\n'.join(output)
    
    def _wrap_text(self, text: str, width: int = 76) -> List[str]:
        """Simple text wrapping for better display"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

def main():
    """Command-line interface for conversation reconstruction"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reconstruct Claude conversations from chunks")
    parser.add_argument('--list', action='store_true', help='List available conversations')
    parser.add_argument('--reconstruct', type=str, help='Reconstruct conversation by UUID')
    parser.add_argument('--find', type=str, help='Find conversations containing specific content')
    parser.add_argument('--limit', type=int, default=20, help='Limit number of results')
    parser.add_argument('--no-metadata', action='store_true', help='Hide conversation metadata')
    
    args = parser.parse_args()
    
    reconstructor = ConversationReconstructor()
    
    if args.list:
        print(f"{Fore.CYAN}📋 Available Conversations:")
        conversations = reconstructor.list_conversations(limit=args.limit)
        
        for i, conv in enumerate(conversations, 1):
            print(f"\n{Fore.YELLOW}{i}. {conv['conversation_name']}")
            print(f"   UUID: {conv['conversation_uuid']}")
            print(f"   Chunks: {conv['chunk_count']}")
            print(f"   Categories: {', '.join(conv['categories'])}")
    
    elif args.reconstruct:
        conversation = reconstructor.reconstruct_conversation(args.reconstruct)
        if conversation:
            formatted = reconstructor.format_conversation_for_display(
                conversation, 
                show_metadata=not args.no_metadata
            )
            print(formatted)
    
    elif args.find:
        print(f"{Fore.CYAN}🔍 Finding conversations containing: '{args.find}'")
        conversations = reconstructor.find_conversations_by_content(args.find, args.limit)
        
        for i, conv in enumerate(conversations, 1):
            print(f"\n{Fore.YELLOW}{i}. {conv['conversation_name']}")
            print(f"   UUID: {conv['conversation_uuid']}")
            print(f"   Relevance: {conv['relevance_score']}%")
            print(f"   Category: {conv['category']}")
            print(f"   Chunks Found: {conv['chunk_count']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()