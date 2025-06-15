#!/usr/bin/env python3
"""
conversation_models.py

Purpose:
  Data models for processing Claude AI conversation exports.
  Defines ConversationChunk and related data structures for conversation analysis.

Author: Bryan Thompson
Version: 2.0.0
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

@dataclass
class ConversationChunk:
    """Represents a chunk of text from a Claude conversation"""
    chunk_id: str
    conversation_uuid: str
    conversation_name: str
    message_uuid: str
    chunk_type: str  # 'message', 'attachment', 'thread_context'
    content: str
    category: str
    sender: str  # 'human' or 'assistant'
    created_at: str
    updated_at: str
    account_uuid: str
    metadata: Dict[str, Any]
    chunk_index: int
    total_chunks: int
    message_index: int  # Position of message within conversation
    total_messages: int  # Total messages in conversation

@dataclass
class AttachmentChunk:
    """Represents processed attachment content from a conversation message"""
    chunk_id: str
    conversation_uuid: str
    message_uuid: str
    file_name: str
    file_type: str
    file_size: int
    content: str
    category: str
    extracted_content: str
    chunk_index: int
    total_chunks: int

@dataclass
class ConversationMetadata:
    """Metadata about a conversation for processing tracking"""
    conversation_uuid: str
    conversation_name: str
    total_messages: int
    total_chunks: int
    categories_found: List[str]
    processing_time: float
    created_at: str
    updated_at: str
    account_uuid: str
    human_messages: int
    assistant_messages: int
    attachments_count: int
    avg_message_length: float
    
class ConversationCategorizer:
    """Enhanced categorizer for conversation content with Claude-specific patterns"""
    
    def __init__(self):
        # Extended categories for conversation content
        self.categories = {
            'legal_compliance': [
                'ada', 'compliance', 'violation', 'formal notice', 'legal', 'lawsuit', 'discrimination',
                'pip', 'performance improvement', 'employment', 'accommodation', 'disability', 'notice',
                'regulation', 'fsrao', 'ifrs', 'audit', 'regulatory'
            ],
            'business_analysis': [
                'requirements', 'business', 'analysis', 'specification', 'process', 'workflow',
                'stakeholder', 'client', 'documentation', 'fintech', 'ccm', 'integration',
                'sow', 'statement of work', 'estimate', 'proposal', 'architecture'
            ],
            'technical_development': [
                'code', 'api', 'database', 'sql', 'python', 'script', 'development', 'programming',
                'vba', 'automation', 'etl', 'oracle', 'integration', 'technical', 'devops',
                'deployment', 'migration', 'data model', 'ingestion', 'flat file'
            ],
            'data_analytics': [
                'data', 'analytics', 'reporting', 'cube', 'warehouse', 'bi', 'business intelligence',
                'metrics', 'analysis', 'query', 'table', 'column', 'entity', 'ifrs',
                'central 1', 'loan data', 'summarization'
            ],
            'communication': [
                'email', 'letter', 'correspondence', 'communication', 'reply', 'response',
                'meeting', 'discussion', 'chat', 'conversation', 'ticket', 'update',
                'client communication'
            ],
            'research_strategy': [
                'research', 'strategy', 'analysis', 'investigation', 'assessment', 'evaluation',
                'planning', 'approach', 'methodology', 'study', 'learning arc'
            ],
            'project_management': [
                'project', 'management', 'timeline', 'milestone', 'task', 'deliverable',
                'handoff', 'planning', 'coordination', 'tracking', 'estimate', 'hours',
                'ticket', 'status', 'workflow'
            ],
            'ai_assistance': [
                'claude', 'ai', 'assistant', 'prompt', 'structured', 'magic approach',
                'help me', 'organize', 'draft', 'generate', 'analysis'
            ]
        }
    
    def categorize(self, text: str, conversation_name: str = "") -> str:
        """Categorize conversation content with enhanced context awareness"""
        # Combine message text and conversation name for better categorization
        combined_text = f"{conversation_name} {text}".lower()
        category_scores = {}
        
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            # Weight longer phrases more heavily
            for keyword in keywords:
                if len(keyword.split()) > 1 and keyword in combined_text:
                    score += 2  # Bonus for multi-word phrases
            category_scores[category] = score
        
        if not any(category_scores.values()):
            return 'general'
        
        return max(category_scores, key=category_scores.get)

class ConversationChunker:
    """Handles intelligent chunking of conversation messages"""
    
    def __init__(self, chunk_size: int = 1200, overlap_size: int = 200):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.categorizer = ConversationCategorizer()
    
    def create_chunk_id(self, conversation_uuid: str, message_uuid: str, chunk_index: int) -> str:
        """Generate unique chunk ID"""
        base_string = f"{conversation_uuid}_{message_uuid}_{chunk_index}"
        return hashlib.md5(base_string.encode()).hexdigest()
    
    def chunk_message(self, message: Dict[str, Any], conversation: Dict[str, Any], 
                     message_index: int, total_messages: int) -> List[ConversationChunk]:
        """Chunk a single conversation message into searchable segments"""
        chunks = []
        text = message.get('text', '')
        
        # Skip empty messages
        if not text.strip():
            return chunks
        
        # Split text into chunks with overlap
        text_chunks = self._split_text_with_overlap(text)
        
        conversation_name = conversation.get('name', '')
        category = self.categorizer.categorize(text, conversation_name)
        
        for chunk_index, chunk_text in enumerate(text_chunks):
            chunk_id = self.create_chunk_id(
                conversation['uuid'], 
                message['uuid'], 
                chunk_index
            )
            
            # Build metadata
            metadata = {
                'conversation_name': conversation_name,
                'message_sender': message.get('sender', ''),
                'message_created_at': message.get('created_at', ''),
                'chunk_length': len(chunk_text),
                'has_attachments': len(message.get('attachments', [])) > 0,
                'attachment_count': len(message.get('attachments', [])),
                'message_position': f"{message_index + 1}/{total_messages}"
            }
            
            chunk = ConversationChunk(
                chunk_id=chunk_id,
                conversation_uuid=conversation['uuid'],
                conversation_name=conversation_name,
                message_uuid=message['uuid'],
                chunk_type='message',
                content=chunk_text,
                category=category,
                sender=message.get('sender', ''),
                created_at=message.get('created_at', ''),
                updated_at=message.get('updated_at', ''),
                account_uuid=conversation.get('account', {}).get('uuid', ''),
                metadata=metadata,
                chunk_index=chunk_index,
                total_chunks=len(text_chunks),
                message_index=message_index,
                total_messages=total_messages
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def chunk_attachments(self, message: Dict[str, Any], conversation: Dict[str, Any]) -> List[AttachmentChunk]:
        """Process and chunk attachment content from messages"""
        attachment_chunks = []
        
        attachments = message.get('attachments', [])
        for attachment in attachments:
            extracted_content = attachment.get('extracted_content', '')
            if not extracted_content.strip():
                continue
            
            # Split large attachments into chunks
            content_chunks = self._split_text_with_overlap(extracted_content)
            
            category = self.categorizer.categorize(
                extracted_content, 
                conversation.get('name', '')
            )
            
            for chunk_index, chunk_content in enumerate(content_chunks):
                chunk_id = self.create_chunk_id(
                    conversation['uuid'],
                    f"{message['uuid']}_att_{attachment.get('file_name', 'unknown')}",
                    chunk_index
                )
                
                attachment_chunk = AttachmentChunk(
                    chunk_id=chunk_id,
                    conversation_uuid=conversation['uuid'],
                    message_uuid=message['uuid'],
                    file_name=attachment.get('file_name', ''),
                    file_type=attachment.get('file_type', ''),
                    file_size=attachment.get('file_size', 0),
                    content=chunk_content,
                    category=category,
                    extracted_content=extracted_content,
                    chunk_index=chunk_index,
                    total_chunks=len(content_chunks)
                )
                
                attachment_chunks.append(attachment_chunk)
        
        return attachment_chunks
    
    def _split_text_with_overlap(self, text: str) -> List[str]:
        """Split text into chunks with intelligent sentence boundary detection"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to break at sentence boundary
            chunk_text = text[start:end]
            
            # Look for sentence endings near the end of the chunk
            sentence_endings = ['.', '!', '?', '\n\n']
            best_break = end
            
            for i in range(len(chunk_text) - 1, max(0, len(chunk_text) - 100), -1):
                if chunk_text[i] in sentence_endings:
                    best_break = start + i + 1
                    break
            
            chunks.append(text[start:best_break])
            start = max(start + self.overlap_size, best_break - self.overlap_size)
        
        return [chunk.strip() for chunk in chunks if chunk.strip()]

def create_conversation_metadata(conversation: Dict[str, Any], chunks: List[ConversationChunk], 
                                processing_time: float) -> ConversationMetadata:
    """Create metadata summary for a processed conversation"""
    messages = conversation.get('chat_messages', [])
    human_messages = sum(1 for msg in messages if msg.get('sender') == 'human')
    assistant_messages = sum(1 for msg in messages if msg.get('sender') == 'assistant')
    
    # Count attachments
    attachments_count = sum(len(msg.get('attachments', [])) for msg in messages)
    
    # Calculate average message length
    total_text_length = sum(len(msg.get('text', '')) for msg in messages)
    avg_message_length = total_text_length / len(messages) if messages else 0
    
    # Extract unique categories
    categories_found = list(set(chunk.category for chunk in chunks))
    
    return ConversationMetadata(
        conversation_uuid=conversation['uuid'],
        conversation_name=conversation.get('name', ''),
        total_messages=len(messages),
        total_chunks=len(chunks),
        categories_found=categories_found,
        processing_time=processing_time,
        created_at=conversation.get('created_at', ''),
        updated_at=conversation.get('updated_at', ''),
        account_uuid=conversation.get('account', {}).get('uuid', ''),
        human_messages=human_messages,
        assistant_messages=assistant_messages,
        attachments_count=attachments_count,
        avg_message_length=avg_message_length
    )