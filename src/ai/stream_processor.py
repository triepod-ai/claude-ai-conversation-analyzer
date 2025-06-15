#!/usr/bin/env python3
"""
chunk_conversations.py

Purpose:
  Memory-efficient stream processing of Claude AI conversation exports.
  Processes large JSON files (153MB+) without loading entire file into memory.

Author: Bryan Thompson
Version: 2.0.0
Usage:
  python3 chunk_conversations.py --json_file conversations.json [--output_dir chunks/]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Iterator, Optional, Tuple
from dataclasses import asdict
import ijson  # For streaming JSON processing

# Import our conversation models
from conversation_models import (
    ConversationChunk, AttachmentChunk, ConversationMetadata, 
    ConversationChunker, create_conversation_metadata
)

# Third-Party Libraries
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    print("Colorama not installed; install via 'uv pip install colorama' for colored output.")
    class Fore:
        GREEN = ""
        RED = ""
        YELLOW = ""
        BLUE = ""
        CYAN = ""
        MAGENTA = ""
    class Style:
        RESET_ALL = ""

class ConversationStreamProcessor:
    """Stream-based processor for large conversation JSON files"""
    
    def __init__(self, chunk_size: int = 1200, overlap_size: int = 200):
        self.chunker = ConversationChunker(chunk_size, overlap_size)
        self.total_conversations = 0
        self.total_chunks = 0
        self.total_messages = 0
        self.total_attachments = 0
        self.processing_errors = 0
        self.categories_found = set()
        
    def estimate_total_conversations(self, json_file: str) -> int:
        """Quick estimate of total conversations for progress tracking"""
        try:
            print(f"{Fore.CYAN}🔍 Estimating total conversations...")
            with open(json_file, 'rb') as file:
                # Count opening braces at array level to estimate conversation count
                count = 0
                parser = ijson.parse(file)
                for prefix, event, value in parser:
                    if prefix == 'item' and event == 'start_map':
                        count += 1
                        if count % 100 == 0:
                            print(f"{Fore.YELLOW}   Found {count} conversations so far...")
                return count
        except Exception as e:
            print(f"{Fore.RED}❌ Error estimating conversations: {e}")
            return 1435  # Fallback to known count
    
    def stream_conversations(self, json_file: str) -> Iterator[Dict]:
        """Stream conversations one at a time without loading entire file"""
        try:
            with open(json_file, 'rb') as file:
                # Use ijson to parse conversations one by one
                parser = ijson.items(file, 'item')
                for conversation in parser:
                    yield conversation
        except Exception as e:
            print(f"{Fore.RED}❌ Error streaming conversations: {e}")
            raise
    
    def process_conversation_stream(self, json_file: str, output_dir: str = "chunks/") -> Tuple[List[str], Dict]:
        """Process conversations using streaming approach for memory efficiency"""
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize tracking
        start_time = time.time()
        processed_conversations = 0
        all_chunks = []
        all_metadata = []
        batch_size = 50  # Process in batches to manage memory
        current_batch = []
        
        # Estimate total for progress tracking
        estimated_total = self.estimate_total_conversations(json_file)
        print(f"{Fore.GREEN}📊 Estimated {estimated_total} conversations to process")
        
        try:
            print(f"{Fore.CYAN}🔄 Starting stream processing of {json_file}...")
            
            # Stream and process conversations
            for conversation in self.stream_conversations(json_file):
                try:
                    # Process single conversation
                    conv_start_time = time.time()
                    chunks = self.process_single_conversation(conversation)
                    conv_processing_time = time.time() - conv_start_time
                    
                    # Create metadata
                    metadata = create_conversation_metadata(
                        conversation, chunks, conv_processing_time
                    )
                    
                    # Add to current batch
                    current_batch.extend(chunks)
                    all_metadata.append(metadata)
                    
                    # Track progress
                    processed_conversations += 1
                    self.total_conversations += 1
                    self.total_chunks += len(chunks)
                    self.total_messages += len(conversation.get('chat_messages', []))
                    
                    # Update categories found
                    for chunk in chunks:
                        self.categories_found.add(chunk.category)
                    
                    # Progress reporting
                    if processed_conversations % 10 == 0:
                        progress_pct = (processed_conversations / estimated_total) * 100
                        print(f"{Fore.YELLOW}⏳ Processed {processed_conversations}/{estimated_total} conversations ({progress_pct:.1f}%) - {len(chunks)} chunks")
                    
                    # Write batch when it gets large enough
                    if len(current_batch) >= batch_size * 20:  # ~1000 chunks per batch
                        self._write_batch_to_file(current_batch, output_dir, processed_conversations)
                        all_chunks.extend(current_batch)
                        current_batch = []
                        
                        # Optional: Force garbage collection for large datasets
                        import gc
                        gc.collect()
                
                except Exception as e:
                    self.processing_errors += 1
                    print(f"{Fore.RED}❌ Error processing conversation {conversation.get('uuid', 'unknown')}: {e}")
                    continue
            
            # Write final batch
            if current_batch:
                self._write_batch_to_file(current_batch, output_dir, processed_conversations)
                all_chunks.extend(current_batch)
            
            # Write metadata
            self._write_metadata(all_metadata, output_dir)
            
            # Generate summary
            total_time = time.time() - start_time
            summary = self._generate_processing_summary(total_time)
            
            print(f"{Fore.GREEN}✅ Stream processing completed successfully!")
            print(f"{Fore.CYAN}📊 Final Summary:")
            for key, value in summary.items():
                print(f"   {key}: {value}")
                
            return self._write_final_chunks_file(all_chunks, output_dir), summary
            
        except Exception as e:
            print(f"{Fore.RED}❌ Critical error during stream processing: {e}")
            raise
    
    def process_single_conversation(self, conversation: Dict) -> List[ConversationChunk]:
        """Process a single conversation into chunks"""
        chunks = []
        messages = conversation.get('chat_messages', [])
        total_messages = len(messages)
        
        for message_index, message in enumerate(messages):
            try:
                # Process message content
                message_chunks = self.chunker.chunk_message(
                    message, conversation, message_index, total_messages
                )
                chunks.extend(message_chunks)
                
                # Process attachments
                attachment_chunks = self.chunker.chunk_attachments(message, conversation)
                # Convert attachment chunks to conversation chunks for consistency
                for att_chunk in attachment_chunks:
                    conv_chunk = ConversationChunk(
                        chunk_id=att_chunk.chunk_id,
                        conversation_uuid=att_chunk.conversation_uuid,
                        conversation_name=conversation.get('name', ''),
                        message_uuid=att_chunk.message_uuid,
                        chunk_type='attachment',
                        content=att_chunk.content,
                        category=att_chunk.category,
                        sender='attachment',
                        created_at=message.get('created_at', ''),
                        updated_at=message.get('updated_at', ''),
                        account_uuid=conversation.get('account', {}).get('uuid', ''),
                        metadata={
                            'file_name': att_chunk.file_name,
                            'file_type': att_chunk.file_type,
                            'file_size': att_chunk.file_size,
                            'chunk_length': len(att_chunk.content)
                        },
                        chunk_index=att_chunk.chunk_index,
                        total_chunks=att_chunk.total_chunks,
                        message_index=message_index,
                        total_messages=total_messages
                    )
                    chunks.append(conv_chunk)
                    self.total_attachments += 1
                    
            except Exception as e:
                print(f"{Fore.RED}❌ Error processing message {message.get('uuid', 'unknown')}: {e}")
                continue
        
        return chunks
    
    def _write_batch_to_file(self, batch: List[ConversationChunk], output_dir: str, batch_num: int):
        """Write a batch of chunks to temporary file"""
        batch_file = os.path.join(output_dir, f"conversation_batch_{batch_num:04d}.json")
        batch_data = [asdict(chunk) for chunk in batch]
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
    
    def _write_final_chunks_file(self, all_chunks: List[ConversationChunk], output_dir: str) -> List[str]:
        """Combine all batches into final chunks file"""
        
        # Convert chunks to dictionaries
        chunks_data = [asdict(chunk) for chunk in all_chunks]
        
        # Write main chunks file
        chunks_file = os.path.join(output_dir, "conversation_chunks.json")
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        # Group by category for categorized file
        categorized_chunks = {}
        for chunk in all_chunks:
            category = chunk.category
            if category not in categorized_chunks:
                categorized_chunks[category] = []
            categorized_chunks[category].append(asdict(chunk))
        
        # Write categorized chunks file
        categorized_file = os.path.join(output_dir, "conversation_chunks_categorized.json")
        with open(categorized_file, 'w', encoding='utf-8') as f:
            json.dump(categorized_chunks, f, indent=2, ensure_ascii=False)
        
        # Clean up batch files
        self._cleanup_batch_files(output_dir)
        
        return [chunks_file, categorized_file]
    
    def _write_metadata(self, metadata_list: List[ConversationMetadata], output_dir: str):
        """Write processing metadata to file"""
        metadata_data = [asdict(metadata) for metadata in metadata_list]
        metadata_file = os.path.join(output_dir, "conversation_metadata.json")
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_data, f, indent=2, ensure_ascii=False)
    
    def _cleanup_batch_files(self, output_dir: str):
        """Remove temporary batch files"""
        try:
            for file in os.listdir(output_dir):
                if file.startswith("conversation_batch_") and file.endswith(".json"):
                    os.remove(os.path.join(output_dir, file))
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not clean up batch files: {e}")
    
    def _generate_processing_summary(self, processing_time: float) -> Dict:
        """Generate comprehensive processing summary"""
        return {
            "Total Conversations Processed": self.total_conversations,
            "Total Message Chunks": self.total_chunks,
            "Total Messages": self.total_messages,
            "Total Attachments": self.total_attachments,
            "Categories Found": len(self.categories_found),
            "Category List": sorted(list(self.categories_found)),
            "Processing Errors": self.processing_errors,
            "Processing Time": f"{processing_time:.2f} seconds",
            "Average Chunks per Conversation": f"{self.total_chunks / max(1, self.total_conversations):.1f}",
            "Processing Rate": f"{self.total_conversations / max(1, processing_time):.1f} conversations/second"
        }

def main():
    """Main function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Stream-process Claude AI conversation exports into searchable chunks"
    )
    parser.add_argument(
        '--json_file', 
        required=True, 
        help='Path to conversations.json file'
    )
    parser.add_argument(
        '--output_dir', 
        default='chunks/', 
        help='Output directory for chunk files (default: chunks/)'
    )
    parser.add_argument(
        '--chunk_size', 
        type=int, 
        default=1200, 
        help='Maximum chunk size in characters (default: 1200)'
    )
    parser.add_argument(
        '--overlap_size', 
        type=int, 
        default=200, 
        help='Overlap size between chunks (default: 200)'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.json_file):
        print(f"{Fore.RED}❌ Error: File '{args.json_file}' not found.")
        sys.exit(1)
    
    # Check file size
    file_size_mb = os.path.getsize(args.json_file) / (1024 * 1024)
    print(f"{Fore.CYAN}📂 Processing file: {args.json_file} ({file_size_mb:.1f} MB)")
    
    # Initialize processor
    processor = ConversationStreamProcessor(args.chunk_size, args.overlap_size)
    
    try:
        # Process conversations
        output_files, summary = processor.process_conversation_stream(
            args.json_file, 
            args.output_dir
        )
        
        print(f"{Fore.GREEN}🎉 Successfully created:")
        for file_path in output_files:
            print(f"   📄 {file_path}")
        
        # Write summary to file
        summary_file = os.path.join(args.output_dir, "processing_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"   📊 {summary_file}")
        
    except Exception as e:
        print(f"{Fore.RED}❌ Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()