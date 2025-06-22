#!/usr/bin/env python3
"""
unified_search.py

Purpose:
  Unified search interface across both Claude project chunks and conversation chunks.
  Provides semantic search across multiple Chroma collections with result aggregation.

Author: Bryan Thompson
Version: 2.0.0
Usage:
  python3 unified_search.py --query "ADA accommodation" [--interactive]
"""

import argparse
import json
import sys
import csv
import io
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import time

# Third-Party Libraries
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    import chromadb
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: uv pip install colorama chromadb")
    sys.exit(1)

# Local imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'ai'))
from conversation_reconstructor import ConversationReconstructor

@dataclass
class UnifiedSearchResult:
    """Represents a search result from unified search across collections"""
    chunk_id: str
    content: str
    category: str
    distance: float
    source_type: str  # 'project' or 'conversation'
    source_name: str
    metadata: Dict[str, Any]
    rank: int
    
class UnifiedSearchEngine:
    """Search engine that queries multiple Chroma collections and aggregates results"""
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8001):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.client = None
        self.collections = {}
        self.collection_configs = {
            'claude_project_chats': {
                'name': 'Projects',
                'source_type': 'project',
                'source_name_field': 'project_name'
            },
            'claude_conversation_chats': {
                'name': 'Conversations', 
                'source_type': 'conversation',
                'source_name_field': 'conversation_name'
            }
        }
        self.last_search_results = None
        
    def connect(self) -> bool:
        """Connect to Chroma database and load available collections"""
        try:
            # Try HTTP client first
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            
            # Test connection
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
        
        # Load available collections
        return self._load_collections()
    
    def _load_collections(self) -> bool:
        """Load and validate available collections"""
        try:
            available_collections = [col.name for col in self.client.list_collections()]
            print(f"{Fore.CYAN}📚 Available collections: {available_collections}")
            
            for collection_name, config in self.collection_configs.items():
                if collection_name in available_collections:
                    collection = self.client.get_collection(collection_name)
                    count = collection.count()
                    self.collections[collection_name] = {
                        'collection': collection,
                        'config': config,
                        'count': count
                    }
                    print(f"{Fore.GREEN}✅ Loaded {config['name']}: {count:,} documents")
                else:
                    print(f"{Fore.YELLOW}⚠️ Collection '{collection_name}' not found")
            
            if not self.collections:
                print(f"{Fore.RED}❌ No valid collections found")
                return False
                
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading collections: {e}")
            return False
    
    def search_unified(self, query: str, n_results: int = 10, 
                      category_filter: Optional[str] = None,
                      source_filter: Optional[str] = None,
                      date_from: Optional[str] = None,
                      date_to: Optional[str] = None,
                      min_content_length: Optional[int] = None,
                      max_content_length: Optional[int] = None,
                      similarity_threshold: Optional[float] = None,
                      creator_filter: Optional[str] = None) -> List[UnifiedSearchResult]:
        """Perform unified search across all available collections"""
        
        if not self.collections:
            print(f"{Fore.RED}❌ No collections available for search")
            return []
        
        all_results = []
        
        # Search each collection
        for collection_name, collection_info in self.collections.items():
            try:
                collection = collection_info['collection']
                config = collection_info['config']
                
                # Skip if source filter doesn't match
                if source_filter and config['source_type'] != source_filter:
                    continue
                
                print(f"{Fore.CYAN}🔍 Searching {config['name']}...")
                
                # Build where clause for filtering
                where_clause = {}
                if category_filter:
                    where_clause['category'] = category_filter
                
                # Add date range filtering
                if date_from or date_to:
                    date_conditions = []
                    if date_from:
                        date_conditions.append({"created_at": {"$gte": date_from}})
                    if date_to:
                        date_conditions.append({"created_at": {"$lte": date_to}})
                    
                    if date_conditions:
                        if where_clause:
                            where_clause = {"$and": [where_clause] + date_conditions}
                        else:
                            where_clause = {"$and": date_conditions} if len(date_conditions) > 1 else date_conditions[0]
                
                # Add creator filtering
                if creator_filter:
                    creator_condition = {"$or": [
                        {"creator_name": {"$contains": creator_filter}},
                        {"message_sender": {"$contains": creator_filter}}
                    ]}
                    if where_clause:
                        where_clause = {"$and": [where_clause, creator_condition]}
                    else:
                        where_clause = creator_condition
                
                # Perform search
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_clause if where_clause else None,
                    include=['documents', 'metadatas', 'distances']
                )
                
                # Process results
                for i in range(len(results['documents'][0])):
                    content = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    # Apply content length filtering
                    if min_content_length and len(content) < min_content_length:
                        continue
                    if max_content_length and len(content) > max_content_length:
                        continue
                    
                    # Apply similarity threshold filtering
                    if similarity_threshold and (1 - distance) < similarity_threshold:
                        continue
                    
                    # Extract source name
                    source_name = metadata.get(config['source_name_field'], 'Unknown')
                    
                    result = UnifiedSearchResult(
                        chunk_id=metadata.get('chunk_id', f"unknown_{i}"),
                        content=content,
                        category=metadata.get('category', 'general'),
                        distance=distance,
                        source_type=config['source_type'],
                        source_name=source_name,
                        metadata=metadata,
                        rank=0  # Will be set during aggregation
                    )
                    
                    all_results.append(result)
                    
                print(f"{Fore.GREEN}✅ Found {len(results['documents'][0])} results from {config['name']}")
                
            except Exception as e:
                print(f"{Fore.RED}❌ Error searching {collection_name}: {e}")
                continue
        
        # Aggregate and rank results
        return self._aggregate_results(all_results, n_results)
    
    def _aggregate_results(self, results: List[UnifiedSearchResult], n_results: int) -> List[UnifiedSearchResult]:
        """Aggregate results from multiple collections and rank them"""
        
        if not results:
            return []
        
        # Sort by distance (lower is better for similarity)
        results.sort(key=lambda x: x.distance)
        
        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        # Return top N results
        return results[:n_results]
    
    def display_results(self, results: List[UnifiedSearchResult], query: str):
        """Display search results in a formatted way"""
        
        if not results:
            print(f"{Fore.YELLOW}🔍 No results found for query: '{query}'")
            return
        
        print(f"\n{Fore.GREEN}🎯 Found {len(results)} results for: '{query}'")
        print(f"{Fore.CYAN}{'='*80}")
        
        for result in results:
            # Source indicator
            source_icon = "📄" if result.source_type == "project" else "💬"
            similarity = (1 - result.distance) * 100
            
            print(f"\n{Fore.YELLOW}#{result.rank} {source_icon} {result.source_type.title()}: {result.source_name}")
            print(f"{Fore.MAGENTA}Category: {result.category} | Similarity: {similarity:.1f}%")
            print(f"{Fore.WHITE}{result.content[:300]}{'...' if len(result.content) > 300 else ''}")
            
            # Additional metadata
            if result.source_type == "conversation":
                sender = result.metadata.get('message_sender', 'unknown')
                created_at = result.metadata.get('message_created_at', 'unknown')
                print(f"{Fore.BLUE}💭 From: {sender} | Date: {created_at[:10]}")
            elif result.source_type == "project":
                creator = result.metadata.get('creator_name', 'unknown')
                created_at = result.metadata.get('created_at', 'unknown')
                print(f"{Fore.BLUE}👤 Creator: {creator} | Date: {created_at[:10]}")
            
            print(f"{Fore.CYAN}{'-'*80}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about all loaded collections"""
        stats = {
            'total_collections': len(self.collections),
            'total_documents': sum(info['count'] for info in self.collections.values()),
            'collections': {}
        }
        
        for collection_name, collection_info in self.collections.items():
            stats['collections'][collection_name] = {
                'name': collection_info['config']['name'],
                'type': collection_info['config']['source_type'],
                'count': collection_info['count']
            }
        
        return stats
    
    def export_results(self, results: List[UnifiedSearchResult], query: str, 
                      export_format: str = 'json', output_file: Optional[str] = None,
                      filters_applied: Optional[Dict] = None) -> str:
        """Export search results to various formats"""
        
        if not results:
            print(f"{Fore.YELLOW}⚠️ No results to export")
            return ""
        
        # Generate export data
        export_data = self._generate_export_data(query, results, filters_applied or {})
        
        # Generate output based on format
        if export_format.lower() == 'json':
            content = self._export_as_json(export_data)
            extension = 'json'
        elif export_format.lower() == 'csv':
            content = self._export_as_csv(export_data)
            extension = 'csv'
        elif export_format.lower() == 'markdown' or export_format.lower() == 'md':
            content = self._export_as_markdown(export_data)
            extension = 'md'
        elif export_format.lower() == 'txt' or export_format.lower() == 'text':
            content = self._export_as_text(export_data)
            extension = 'txt'
        else:
            print(f"{Fore.RED}❌ Unsupported export format: {export_format}")
            return ""
        
        # Determine output file name
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c for c in query[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_query = safe_query.replace(' ', '_')
            output_file = f"search_results_{safe_query}_{timestamp}.{extension}"
        
        # Write to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"{Fore.GREEN}✅ Results exported to: {output_file}")
            print(f"{Fore.CYAN}📊 Export details:")
            print(f"   Format: {export_format.upper()}")
            print(f"   Results: {len(results)}")
            print(f"   Query: '{query}'")
            print(f"   File size: {len(content):,} characters")
            
            return output_file
            
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to write export file: {e}")
            return ""
    
    def _generate_export_data(self, query: str, results: List[UnifiedSearchResult], 
                             filters_applied: Dict) -> Dict:
        """Generate structured export data"""
        timestamp = datetime.now().isoformat()
        
        export_data = {
            'export_metadata': {
                'query': query,
                'timestamp': timestamp,
                'total_results': len(results),
                'filters_applied': filters_applied,
                'export_type': 'claude_project_search_results',
                'tool': 'unified_search_cli'
            },
            'results': []
        }
        
        for result in results:
            similarity = (1 - result.distance) * 100 if result.distance is not None else 0
            
            result_data = {
                'rank': result.rank,
                'source_type': result.source_type,
                'source_name': result.source_name,
                'category': result.category,
                'similarity_score': round(similarity, 2),
                'content_length': len(result.content),
                'content': result.content,
                'chunk_id': result.chunk_id,
                'distance': result.distance,
                'metadata': result.metadata
            }
            
            export_data['results'].append(result_data)
        
        return export_data
    
    def _export_as_json(self, export_data: Dict) -> str:
        """Export as JSON format"""
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_as_csv(self, export_data: Dict) -> str:
        """Export as CSV format"""
        output = io.StringIO()
        
        # CSV headers
        fieldnames = [
            'rank', 'source_type', 'source_name', 'category', 'similarity_score',
            'content_length', 'creator', 'created_at', 'chunk_id', 'content'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write data rows
        for result in export_data['results']:
            creator = result['metadata'].get('creator_name') or result['metadata'].get('message_sender', 'Unknown')
            created_at = result['metadata'].get('created_at') or result['metadata'].get('message_created_at', 'Unknown')
            
            row = {
                'rank': result['rank'],
                'source_type': result['source_type'],
                'source_name': result['source_name'],
                'category': result['category'],
                'similarity_score': result['similarity_score'],
                'content_length': result['content_length'],
                'creator': creator,
                'created_at': created_at,
                'chunk_id': result['chunk_id'],
                'content': result['content'].replace('\n', ' ').replace('\r', ' ')  # Clean content for CSV
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    def _export_as_markdown(self, export_data: Dict) -> str:
        """Export as Markdown format"""
        metadata = export_data['export_metadata']
        results = export_data['results']
        
        md_content = f"""# Claude Search Results

**Query:** {metadata['query']}  
**Exported:** {metadata['timestamp']}  
**Total Results:** {metadata['total_results']}  
**Tool:** {metadata['tool']}  

## Applied Filters

"""
        
        if metadata['filters_applied']:
            for filter_name, filter_value in metadata['filters_applied'].items():
                md_content += f"- **{filter_name.replace('_', ' ').title()}:** {filter_value}\n"
        else:
            md_content += "- No filters applied\n"
        
        md_content += "\n## Search Results\n\n"
        
        for result in results:
            source_icon = "📄" if result['source_type'] == 'project' else "💬"
            creator = result['metadata'].get('creator_name') or result['metadata'].get('message_sender', 'Unknown')
            created_at = result['metadata'].get('created_at') or result['metadata'].get('message_created_at', 'Unknown')
            
            md_content += f"""### {result['rank']}. {source_icon} {result['source_name']}

**Category:** {result['category']}  
**Similarity:** {result['similarity_score']}%  
**Source Type:** {result['source_type']}  
**Creator:** {creator}  
**Created:** {created_at}  
**Content Length:** {result['content_length']} characters  
**Chunk ID:** {result['chunk_id']}  

**Content:**
```
{result['content']}
```

---

"""
        
        return md_content
    
    def _export_as_text(self, export_data: Dict) -> str:
        """Export as plain text format"""
        metadata = export_data['export_metadata']
        results = export_data['results']
        
        text_content = f"""CLAUDE PROJECT SEARCH RESULTS
================================

Query: {metadata['query']}
Exported: {metadata['timestamp']}
Total Results: {metadata['total_results']}
Tool: {metadata['tool']}

Filters Applied:
"""
        
        if metadata['filters_applied']:
            for filter_name, filter_value in metadata['filters_applied'].items():
                text_content += f"  - {filter_name.replace('_', ' ').title()}: {filter_value}\n"
        else:
            text_content += "  - No filters applied\n"
        
        text_content += "\n" + "="*50 + "\n\n"
        
        for result in results:
            source_icon = "[PROJECT]" if result['source_type'] == 'project' else "[CONVERSATION]"
            creator = result['metadata'].get('creator_name') or result['metadata'].get('message_sender', 'Unknown')
            created_at = result['metadata'].get('created_at') or result['metadata'].get('message_created_at', 'Unknown')
            
            text_content += f"""{result['rank']}. {source_icon} {result['source_name']}

Category: {result['category']}
Similarity: {result['similarity_score']}%
Creator: {creator}
Created: {created_at}
Content Length: {result['content_length']} characters
Chunk ID: {result['chunk_id']}

Content:
{result['content']}

{'-'*50}

"""
        
        return text_content
    
    def _handle_export_command(self, command: str):
        """Handle export commands in interactive mode"""
        if not self.last_search_results:
            print(f"{Fore.YELLOW}⚠️ No previous search results to export. Please perform a search first.")
            return
        
        parts = command.split()
        if len(parts) < 2:
            print(f"{Fore.RED}❌ Export format required. Usage: export <format> [filename]")
            print(f"{Fore.CYAN}Available formats: json, csv, markdown, txt")
            return
        
        export_format = parts[1].lower()
        output_file = parts[2] if len(parts) > 2 else None
        
        if export_format not in ['json', 'csv', 'markdown', 'md', 'txt', 'text']:
            print(f"{Fore.RED}❌ Unsupported format: {export_format}")
            print(f"{Fore.CYAN}Available formats: json, csv, markdown, txt")
            return
        
        print(f"{Fore.CYAN}💾 Exporting {len(self.last_search_results['results'])} results...")
        
        self.export_results(
            results=self.last_search_results['results'],
            query=self.last_search_results['query'],
            export_format=export_format,
            output_file=output_file,
            filters_applied=self.last_search_results['filters']
        )
    
    def get_filter_options(self) -> Dict[str, Any]:
        """Get available filter options from the collections"""
        filter_options = {
            'categories': [],
            'creators': [],
            'sources': [],
            'date_range': {'min': None, 'max': None},
            'content_length': {'min': 0, 'max': 10000}
        }
        
        # Standard categories
        filter_options['categories'] = [
            'legal_compliance', 'business_analysis', 'technical_development',
            'data_analytics', 'communication', 'research_strategy', 
            'project_management', 'ai_assistance', 'general'
        ]
        
        # Source types
        filter_options['sources'] = ['project', 'conversation']
        
        # Sample from collections to get dynamic filter options
        try:
            creators_set = set()
            dates = []
            content_lengths = []
            
            for collection_name, collection_info in self.collections.items():
                collection = collection_info['collection']
                
                # Sample some documents to extract filter values
                sample_results = collection.get(
                    limit=100,
                    include=['documents', 'metadatas']
                )
                
                for metadata in sample_results.get('metadatas', []):
                    # Collect creators
                    creator = metadata.get('creator_name') or metadata.get('message_sender')
                    if creator:
                        creators_set.add(creator)
                    
                    # Collect dates
                    created_at = metadata.get('created_at') or metadata.get('message_created_at')
                    if created_at:
                        dates.append(created_at[:10])  # YYYY-MM-DD format
                
                for content in sample_results.get('documents', []):
                    content_lengths.append(len(content))
            
            # Process collected data
            filter_options['creators'] = sorted(list(creators_set))[:50]  # Limit to 50
            
            if dates:
                filter_options['date_range']['min'] = min(dates)
                filter_options['date_range']['max'] = max(dates)
            
            if content_lengths:
                filter_options['content_length']['min'] = min(content_lengths)
                filter_options['content_length']['max'] = max(content_lengths)
                
        except Exception as e:
            print(f"Warning: Could not extract dynamic filter options: {e}")
        
        return filter_options
    
    def interactive_search(self):
        """Interactive search mode with help and filters"""
        
        print(f"\n{Fore.GREEN}🎯 Unified Claude Search Engine")
        print(f"{Fore.CYAN}{'='*50}")
        
        # Display collection stats
        stats = self.get_collection_stats()
        print(f"{Fore.YELLOW}📊 Loaded Collections:")
        for col_name, col_info in stats['collections'].items():
            print(f"   {col_info['name']}: {col_info['count']:,} documents")
        print(f"   Total: {stats['total_documents']:,} searchable chunks")
        
        print(f"\n{Fore.CYAN}💡 Search Tips:")
        print(f"   • Enter search terms: 'ADA accommodation disability'")
        print(f"   • Filter by category: 'category:legal_compliance ADA violations'")
        print(f"   • Filter by source: 'source:project database integration'")
        print(f"   • Filter by source: 'source:conversation claude assistance'")
        print(f"   • Type 'help' for more options")
        print(f"   • Type 'quit' to exit")
        
        while True:
            try:
                query = input(f"\n{Fore.WHITE}🔍 Search> ").strip()
                
                if not query:
                    continue
                    
                if query.lower() in ['quit', 'exit', 'q']:
                    print(f"{Fore.GREEN}👋 Goodbye!")
                    break
                    
                if query.lower() == 'help':
                    self._show_help()
                    continue
                
                # Parse filters from query
                category_filter, source_filter, clean_query = self._parse_query_filters(query)
                
                if not clean_query:
                    print(f"{Fore.YELLOW}⚠️ Please provide a search query")
                    continue
                
                # Perform search
                start_time = time.time()
                results = self.search_unified(
                    clean_query, 
                    n_results=10,
                    category_filter=category_filter,
                    source_filter=source_filter
                )
                search_time = time.time() - start_time
                
                # Display results
                self.display_results(results, clean_query)
                print(f"\n{Fore.CYAN}⏱️ Search completed in {search_time:.2f} seconds")
                
            except KeyboardInterrupt:
                print(f"\n{Fore.GREEN}👋 Goodbye!")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ Search error: {e}")
    
    def _parse_query_filters(self, query: str) -> Tuple[Optional[str], Optional[str], str]:
        """Parse category and source filters from query"""
        
        category_filter = None
        source_filter = None
        query_parts = []
        
        for part in query.split():
            if part.startswith('category:'):
                category_filter = part.split(':', 1)[1]
            elif part.startswith('source:'):
                source_filter = part.split(':', 1)[1]
            else:
                query_parts.append(part)
        
        clean_query = ' '.join(query_parts)
        return category_filter, source_filter, clean_query
    
    def _show_help(self):
        """Show detailed help information"""
        print(f"\n{Fore.GREEN}📖 Unified Search Help")
        print(f"{Fore.CYAN}{'='*50}")
        print(f"{Fore.YELLOW}Available Filters:")
        print(f"   category:CATEGORY  - Filter by content category")
        print(f"   source:TYPE        - Filter by source type (project/conversation)")
        print(f"\n{Fore.YELLOW}Categories:")
        categories = [
            'legal_compliance', 'business_analysis', 'technical_development',
            'data_analytics', 'communication', 'research_strategy', 
            'project_management', 'ai_assistance', 'general'
        ]
        for i, cat in enumerate(categories):
            if i % 3 == 0:
                print("   ", end="")
            print(f"{cat:<20}", end="")
            if (i + 1) % 3 == 0:
                print()
        if len(categories) % 3 != 0:
            print()
        
        print(f"\n{Fore.YELLOW}Example Searches:")
        print(f"   ADA accommodation disability")
        print(f"   category:technical_development database integration")
        print(f"   source:conversation claude assistance")
        print(f"   category:legal_compliance source:project")
        print(f"\n{Fore.YELLOW}Export Commands:")
        print(f"   export json              # Export last search as JSON")
        print(f"   export csv               # Export last search as CSV")
        print(f"   export markdown          # Export last search as Markdown")
        print(f"   export txt               # Export last search as text")
        print(f"   export json myfile.json  # Export with custom filename")
        
        print(f"\n{Fore.YELLOW}Conversation Commands:")
        print(f"   reconstruct <uuid>       # View full conversation by UUID")
        print(f"   list-conversations       # Show available conversations")
        print(f"   find-conversations <query> # Find conversations by content")

def main():
    """Main function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Unified search across Claude projects and conversations"
    )
    parser.add_argument(
        '--query', 
        help='Search query'
    )
    parser.add_argument(
        '--interactive', 
        action='store_true',
        help='Start interactive search mode'
    )
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
    parser.add_argument(
        '--n_results', 
        type=int, 
        default=10,
        help='Number of results to return (default: 10)'
    )
    parser.add_argument(
        '--category',
        help='Filter by category'
    )
    parser.add_argument(
        '--source',
        choices=['project', 'conversation'],
        help='Filter by source type'
    )
    parser.add_argument(
        '--export',
        choices=['json', 'csv', 'markdown', 'md', 'txt', 'text'],
        help='Export results to file in specified format'
    )
    parser.add_argument(
        '--output',
        help='Output file name for export (auto-generated if not specified)'
    )
    
    # Conversation reconstruction arguments
    parser.add_argument(
        '--list-conversations',
        action='store_true',
        help='List available conversations'
    )
    parser.add_argument(
        '--reconstruct',
        help='Reconstruct conversation by UUID'
    )
    parser.add_argument(
        '--find-conversations',
        help='Find conversations containing specific content'
    )
    parser.add_argument(
        '--conversation-limit',
        type=int,
        default=20,
        help='Limit number of conversations to list/find (default: 20)'
    )
    
    args = parser.parse_args()
    
    # Handle conversation reconstruction commands first
    if args.list_conversations or args.reconstruct or args.find_conversations:
        reconstructor = ConversationReconstructor(args.chroma_host, args.chroma_port)
        
        if args.list_conversations:
            print(f"{Fore.CYAN}📋 Available Conversations:")
            conversations = reconstructor.list_conversations(limit=args.conversation_limit)
            
            if not conversations:
                print(f"{Fore.YELLOW}⚠️ No conversations found")
                return
            
            for i, conv in enumerate(conversations, 1):
                print(f"\n{Fore.YELLOW}{i}. {conv['conversation_name']}")
                print(f"   UUID: {conv['conversation_uuid']}")
                print(f"   Chunks: {conv['chunk_count']}")
                print(f"   Categories: {', '.join(conv['categories'])}")
            
        elif args.reconstruct:
            conversation = reconstructor.reconstruct_conversation(args.reconstruct)
            if conversation:
                formatted = reconstructor.format_conversation_for_display(conversation)
                print(formatted)
            else:
                print(f"{Fore.RED}❌ Could not reconstruct conversation: {args.reconstruct}")
        
        elif args.find_conversations:
            print(f"{Fore.CYAN}🔍 Finding conversations containing: '{args.find_conversations}'")
            conversations = reconstructor.find_conversations_by_content(
                args.find_conversations, 
                args.conversation_limit
            )
            
            if not conversations:
                print(f"{Fore.YELLOW}⚠️ No conversations found matching: {args.find_conversations}")
                return
            
            for i, conv in enumerate(conversations, 1):
                print(f"\n{Fore.YELLOW}{i}. {conv['conversation_name']}")
                print(f"   UUID: {conv['conversation_uuid']}")
                print(f"   Relevance: {conv['relevance_score']}%")
                print(f"   Category: {conv['category']}")
                print(f"   Chunks Found: {conv['chunk_count']}")
        
        return
    
    # Initialize search engine for regular search operations
    engine = UnifiedSearchEngine(args.chroma_host, args.chroma_port)
    
    # Connect to database
    if not engine.connect():
        print(f"{Fore.RED}❌ Failed to connect to Chroma database")
        sys.exit(1)
    
    # Interactive mode
    if args.interactive or not args.query:
        engine.interactive_search()
    else:
        # Single query mode
        start_time = time.time()
        results = engine.search_unified(
            args.query,
            n_results=args.n_results,
            category_filter=args.category,
            source_filter=args.source
        )
        search_time = time.time() - start_time
        
        engine.display_results(results, args.query)
        print(f"\n{Fore.CYAN}⏱️ Search completed in {search_time:.2f} seconds")
        
        # Export results if requested
        if args.export and results:
            filters_applied = {
                'category': args.category,
                'source': args.source,
                'n_results': args.n_results
            }
            # Remove None values
            filters_applied = {k: v for k, v in filters_applied.items() if v}
            
            engine.export_results(
                results=results,
                query=args.query,
                export_format=args.export,
                output_file=args.output,
                filters_applied=filters_applied
            )

if __name__ == "__main__":
    main()