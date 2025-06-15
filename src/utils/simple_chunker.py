"""Simple conversation chunker for demo purposes."""

import json
import uuid
from typing import List, Dict, Any
from datetime import datetime

class SimpleChunker:
    """Simple conversation chunker for portfolio demo."""
    
    def __init__(self, chunk_size: int = 1200, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_conversations(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert conversations into searchable chunks."""
        chunks = []
        
        for conv in conversations:
            conv_chunks = self._chunk_conversation(conv)
            chunks.extend(conv_chunks)
        
        return chunks
    
    def _chunk_conversation(self, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk a single conversation into searchable pieces."""
        content = conversation['content']
        chunks = []
        
        # Split content into chunks with overlap
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            
            # Find sentence boundary near the end
            if end < len(content):
                # Look for sentence endings
                for i in range(end, max(start + self.chunk_size - 100, start), -1):
                    if content[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_text = content[start:end].strip()
            
            if chunk_text:  # Only add non-empty chunks
                chunk = {
                    "id": str(uuid.uuid4()),
                    "conversation_id": conversation['id'],
                    "conversation_title": conversation['title'],
                    "chunk_index": chunk_index,
                    "content": chunk_text,
                    "category": conversation['category'],
                    "project_name": conversation['metadata']['project_name'],
                    "participants": conversation['metadata']['participants'],
                    "complexity_score": conversation['metadata']['complexity_score'],
                    "created_date": conversation['created_date'],
                    "chunk_length": len(chunk_text),
                    "metadata": {
                        "source": "demo_conversation",
                        "processing_date": datetime.now().isoformat(),
                        "chunk_method": "simple_overlap",
                        "original_message_count": conversation['message_count']
                    }
                }
                
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + self.chunk_size - self.overlap, end)
            
            if start >= len(content):
                break
        
        return chunks

def main():
    """Generate chunks from mock conversations."""
    chunker = SimpleChunker(chunk_size=800, overlap=150)  # Smaller chunks for demo
    
    # Load mock conversations
    with open('data/mock_conversations.json', 'r') as f:
        conversations = json.load(f)
    
    # Generate chunks
    chunks = chunker.chunk_conversations(conversations)
    
    # Save chunks
    with open('data/conversation_chunks.json', 'w') as f:
        json.dump(chunks, f, indent=2)
    
    # Print statistics
    print(f"✅ Generated {len(chunks)} chunks from {len(conversations)} conversations")
    
    # Category breakdown
    categories = {}
    for chunk in chunks:
        cat = chunk['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📊 Chunks by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} chunks")
    
    # Length statistics
    lengths = [chunk['chunk_length'] for chunk in chunks]
    avg_length = sum(lengths) / len(lengths)
    print(f"\n📏 Chunk statistics:")
    print(f"  Average length: {avg_length:.0f} characters")
    print(f"  Min length: {min(lengths)} characters") 
    print(f"  Max length: {max(lengths)} characters")
    
    return chunks

if __name__ == "__main__":
    main()