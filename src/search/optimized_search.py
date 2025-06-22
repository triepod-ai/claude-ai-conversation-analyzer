#!/usr/bin/env python3
"""
Optimized Search Engine with Redis Caching and Performance Enhancements
High-performance semantic search with caching, connection pooling, and optimization
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from difflib import SequenceMatcher

# Import our Redis caching layer
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from redis_cache import cached_search, cached_stats, cache, get_cache_health

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Business Strategy Vocabulary Mapping
BUSINESS_VOCABULARY = {
    "exit_strategies": ["severance negotiation", "departure planning", "transition strategy", "career transition", "employment exit"],
    "entrepreneurial_settlement": ["business opportunity conversion", "consulting transition", "alternative arrangement", "business opportunity"],
    "leverage": ["utilize", "capitalize on", "employ strategically", "take advantage of", "maximize"],
    "consulting": ["advisory", "professional services", "expertise", "guidance", "consultation"],
    "triepod": ["tripod", "tri-pod", "triad", "three-pod"],  # Common variations
    "severance": ["separation package", "exit package", "departure benefits", "termination benefits"],
    "business_opportunity": ["commercial opportunity", "venture", "business venture", "entrepreneurial chance"],
    "settlement": ["agreement", "arrangement", "resolution", "deal", "negotiated outcome"],
    "favorable_outcome": ["positive result", "beneficial arrangement", "advantageous deal", "win-win"],
    "strategic_planning": ["business strategy", "planning", "strategic thinking", "roadmap"]
}

# Common proper noun variations
PROPER_NOUN_VARIATIONS = {
    "triepod": ["tripod", "tri-pod", "triad"],
    "claude": ["cloud", "claud"],
    "ai": ["artificial intelligence", "machine learning", "ml"]
}

def fuzzy_match_score(term1: str, term2: str) -> float:
    """Calculate fuzzy matching score between two terms"""
    return SequenceMatcher(None, term1.lower(), term2.lower()).ratio()

def expand_business_query(query: str) -> List[str]:
    """Expand query with business vocabulary synonyms"""
    expanded_queries = [query]
    query_lower = query.lower()
    
    # Check for business terms and add synonyms
    for key, synonyms in BUSINESS_VOCABULARY.items():
        if key.replace("_", " ") in query_lower or key.replace("_", "") in query_lower:
            for synonym in synonyms:
                if synonym not in query_lower:
                    expanded_queries.append(f"{query} {synonym}")
    
    # Check for proper noun variations
    words = query_lower.split()
    for word in words:
        for proper_noun, variations in PROPER_NOUN_VARIATIONS.items():
            if fuzzy_match_score(word, proper_noun) > 0.8:
                for variation in variations:
                    if variation != word:
                        expanded_query = query.replace(word, variation)
                        expanded_queries.append(expanded_query)
    
    return expanded_queries

def calculate_recency_boost(created_at: str) -> float:
    """Calculate recency boost factor for search results"""
    try:
        if not created_at:
            return 1.0
            
        # Parse the timestamp
        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        current_date = datetime.now(created_date.tzinfo)
        
        # Calculate days difference
        days_diff = (current_date - created_date).days
        
        # Boost recent content (last 30 days get significant boost)
        if days_diff <= 7:
            return 1.5  # 50% boost for last week
        elif days_diff <= 30:
            return 1.2  # 20% boost for last month
        elif days_diff <= 90:
            return 1.0  # No boost for last 3 months
        else:
            return 0.9  # Slight penalty for older content
            
    except Exception:
        return 1.0  # Default to no boost if parsing fails

@dataclass
class SearchResult:
    """Optimized search result with caching metadata"""
    content: str
    conversation_name: str
    sender: str
    created_at: str
    relevance_score: float
    metadata: Dict[str, Any]
    cached: bool = False
    response_time_ms: float = 0.0

class OptimizedSearchEngine:
    """High-performance search engine with Redis caching and optimizations"""
    
    def __init__(self, 
                 chroma_path: str = "./chroma_db",
                 collection_name: str = "personal_claude_conversations",
                 max_workers: int = 4):
        """
        Initialize optimized search engine
        
        Args:
            chroma_path: Path to ChromaDB database
            collection_name: Name of the collection to search
            max_workers: Maximum threads for parallel processing
        """
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.max_workers = max_workers
        self._connection_pool = {}
        self._lock = threading.Lock()
        
        # Initialize ChromaDB with optimized settings
        self._init_chroma_client()
        
        logger.info(f"✅ Optimized Search Engine initialized")
        logger.info(f"📊 Cache status: {'Available' if cache.is_available else 'Disabled'}")
    
    def _init_chroma_client(self):
        """Initialize ChromaDB client with performance optimizations"""
        if not chromadb:
            raise ImportError("ChromaDB not available")
            
        try:
            # Use new ChromaDB client configuration
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_path
            )
            
            # Get collection with caching
            self.collection = self.chroma_client.get_collection(
                name=self.collection_name
            )
            
            logger.info(f"✅ ChromaDB client initialized with optimizations")
            
        except Exception as e:
            logger.error(f"❌ ChromaDB initialization failed: {e}")
            raise
    
    def _get_connection(self, thread_id: str = None) -> chromadb.Collection:
        """Get thread-safe ChromaDB connection from pool"""
        if not thread_id:
            thread_id = str(threading.current_thread().ident)
            
        with self._lock:
            if thread_id not in self._connection_pool:
                # Create new connection for this thread
                try:
                    client = chromadb.PersistentClient(path=self.chroma_path)
                    collection = client.get_collection(name=self.collection_name)
                    self._connection_pool[thread_id] = collection
                    logger.debug(f"Created new connection for thread {thread_id}")
                except Exception as e:
                    logger.error(f"Failed to create connection: {e}")
                    return self.collection  # Fallback to main connection
                    
            return self._connection_pool[thread_id]
    
    @cached_search(ttl=1800)  # Cache for 30 minutes
    def search(self, 
               query: str,
               n_results: int = 10,
               where: Optional[Dict] = None,
               similarity_threshold: float = 0.0,
               enable_business_expansion: bool = True,
               enable_recency_boost: bool = True) -> Dict[str, Any]:
        """
        Perform optimized semantic search with caching and enhanced features
        
        Args:
            query: Search query string
            n_results: Maximum number of results
            where: Metadata filter conditions
            similarity_threshold: Minimum similarity score
            enable_business_expansion: Enable business vocabulary expansion
            enable_recency_boost: Enable temporal relevance boosting
            
        Returns:
            Optimized search results with performance metadata
        """
        start_time = time.time()
        
        try:
            # Expand query with business vocabulary if enabled
            search_queries = [query]
            if enable_business_expansion:
                expanded_queries = expand_business_query(query)
                search_queries.extend(expanded_queries[:3])  # Limit to avoid too many queries
                logger.debug(f"Expanded {len(search_queries)} queries from: {query}")
            
            # Use thread-safe connection
            collection = self._get_connection()
            
            # Perform multiple searches for expanded queries
            all_results = []
            for search_query in search_queries:
                search_result = collection.query(
                    query_texts=[search_query],
                    n_results=min(n_results * 2, 50),  # Get more results to allow for deduplication
                    where=where,
                    include=["documents", "metadatas", "distances"]
                )
                if search_result.get('documents') and search_result['documents'][0]:
                    all_results.append(search_result)
            
            # Merge and deduplicate results
            if all_results:
                search_results = self._merge_search_results(all_results, n_results)
            else:
                search_results = {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            
            # Process and filter results
            processed_results = self._process_search_results(
                search_results, 
                similarity_threshold,
                start_time,
                enable_recency_boost
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "results": processed_results,
                "query": query,
                "expanded_queries": search_queries if enable_business_expansion else [query],
                "total_results": len(processed_results),
                "execution_time_ms": execution_time,
                "cached": False,  # This will be True if served from cache
                "cache_status": "available" if cache.is_available else "disabled",
                "enhancements": {
                    "business_expansion": enable_business_expansion,
                    "recency_boost": enable_recency_boost,
                    "fuzzy_matching": True
                }
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "results": [],
                "query": query,
                "total_results": 0,
                "error": str(e),
                "execution_time_ms": (time.time() - start_time) * 1000
            }
    
    def _merge_search_results(self, all_results: List[Dict], max_results: int) -> Dict:
        """Merge and deduplicate results from multiple searches"""
        merged_docs = []
        merged_metadatas = []
        merged_distances = []
        seen_docs = set()
        
        # Combine all results
        for result in all_results:
            if result.get('documents') and result['documents'][0]:
                docs = result['documents'][0]
                metas = result.get('metadatas', [[]])[0]
                dists = result.get('distances', [[]])[0]
                
                for doc, meta, dist in zip(docs, metas, dists):
                    # Use first 100 chars as deduplication key
                    doc_key = doc[:100] if doc else ""
                    if doc_key not in seen_docs:
                        seen_docs.add(doc_key)
                        merged_docs.append(doc)
                        merged_metadatas.append(meta)
                        merged_distances.append(dist)
                        
                        if len(merged_docs) >= max_results * 2:  # Limit for processing
                            break
                            
                if len(merged_docs) >= max_results * 2:
                    break
        
        return {
            "documents": [merged_docs],
            "metadatas": [merged_metadatas], 
            "distances": [merged_distances]
        }
    
    def _process_search_results(self, 
                               search_results: Dict,
                               similarity_threshold: float,
                               start_time: float,
                               enable_recency_boost: bool = True) -> List[SearchResult]:
        """Process raw ChromaDB results into optimized format"""
        processed = []
        
        if not search_results.get('documents') or not search_results['documents'][0]:
            return processed
        
        documents = search_results['documents'][0]
        metadatas = search_results.get('metadatas', [[]])[0]
        distances = search_results.get('distances', [[]])[0]
        
        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
            # Convert distance to similarity score
            similarity_score = 1.0 - distance
            
            # Apply recency boost if enabled
            final_score = similarity_score
            if enable_recency_boost and metadata.get('created_at'):
                recency_multiplier = calculate_recency_boost(metadata['created_at'])
                final_score = similarity_score * recency_multiplier
            
            # Apply similarity threshold filter (use final score)
            if final_score < similarity_threshold:
                continue
            
            # Create optimized result object
            result = SearchResult(
                content=doc,
                conversation_name=metadata.get('conversation_name', f'Conversation {i+1}'),
                sender=metadata.get('sender', 'unknown'),
                created_at=metadata.get('created_at', ''),
                relevance_score=final_score,  # Use boosted score
                metadata=metadata,
                cached=False,
                response_time_ms=(time.time() - start_time) * 1000
            )
            
            processed.append(result)
        
        # Sort by relevance score (now includes recency boost)
        processed.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return processed
    
    @cached_search(ttl=3600)  # Cache for 1 hour
    def batch_search(self, 
                     queries: List[str],
                     n_results: int = 5) -> Dict[str, Any]:
        """
        Perform optimized batch search with parallel processing
        
        Args:
            queries: List of search queries
            n_results: Results per query
            
        Returns:
            Batch search results with performance metrics
        """
        start_time = time.time()
        
        # Use ThreadPoolExecutor for parallel searches
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all search tasks
            future_to_query = {
                executor.submit(self._single_search, query, n_results): query
                for query in queries
            }
            
            # Collect results as they complete
            batch_results = {}
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    batch_results[query] = future.result()
                except Exception as e:
                    logger.error(f"Batch search error for '{query}': {e}")
                    batch_results[query] = {"error": str(e), "results": []}
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "batch_results": batch_results,
            "total_queries": len(queries),
            "total_execution_time_ms": total_time,
            "average_time_per_query_ms": total_time / len(queries) if queries else 0,
            "parallel_processing": True
        }
    
    def _single_search(self, query: str, n_results: int) -> Dict[str, Any]:
        """Perform single search for batch processing"""
        try:
            collection = self._get_connection()
            search_results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            return self._process_search_results(search_results, 0.0, time.time())
        except Exception as e:
            return {"error": str(e), "results": []}
    
    @cached_stats(ttl=300)  # Cache stats for 5 minutes
    def get_search_stats(self) -> Dict[str, Any]:
        """Get comprehensive search engine statistics"""
        start_time = time.time()
        
        try:
            collection = self._get_connection()
            
            # Get collection statistics
            collection_count = collection.count()
            
            # Get cache statistics
            cache_stats = get_cache_health()
            
            # Connection pool stats
            pool_stats = {
                "active_connections": len(self._connection_pool),
                "max_workers": self.max_workers
            }
            
            stats_time = (time.time() - start_time) * 1000
            
            return {
                "collection_stats": {
                    "name": self.collection_name,
                    "total_documents": collection_count,
                    "database_path": self.chroma_path
                },
                "cache_stats": cache_stats,
                "connection_pool": pool_stats,
                "performance": {
                    "stats_generation_time_ms": stats_time,
                    "optimization_status": "enabled"
                },
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "cache_stats": get_cache_health()
            }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Run performance optimization routines"""
        start_time = time.time()
        optimizations = []
        
        try:
            # 1. Clear old cache entries
            if cache.is_available:
                cleared = cache.clear_pattern("claude_api:*search*:*")
                optimizations.append(f"Cleared {cleared} old cache entries")
            
            # 2. Optimize connection pool
            with self._lock:
                old_count = len(self._connection_pool)
                self._connection_pool.clear()
                optimizations.append(f"Reset {old_count} connection pool entries")
            
            # 3. Force garbage collection
            import gc
            collected = gc.collect()
            optimizations.append(f"Garbage collected {collected} objects")
            
            optimization_time = (time.time() - start_time) * 1000
            
            return {
                "status": "completed",
                "optimizations_performed": optimizations,
                "optimization_time_ms": optimization_time,
                "next_optimization": "recommended in 1 hour"
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e),
                "optimization_time_ms": (time.time() - start_time) * 1000
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of search engine"""
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy"
        }
        
        # Test ChromaDB connection
        try:
            collection = self._get_connection()
            count = collection.count()
            health_data["chromadb"] = {
                "status": "connected",
                "document_count": count,
                "collection": self.collection_name
            }
        except Exception as e:
            health_data["chromadb"] = {"status": "error", "error": str(e)}
            health_data["status"] = "degraded"
        
        # Test cache
        health_data["cache"] = get_cache_health()
        
        # Test search performance
        try:
            start = time.time()
            test_result = self.search("test", n_results=1)
            search_time = (time.time() - start) * 1000
            
            health_data["search_performance"] = {
                "test_query_time_ms": search_time,
                "status": "fast" if search_time < 100 else "slow" if search_time < 500 else "very_slow"
            }
        except Exception as e:
            health_data["search_performance"] = {"status": "error", "error": str(e)}
            health_data["status"] = "degraded"
        
        return health_data

# Global optimized search engine instance
optimized_engine = None

def get_optimized_engine() -> OptimizedSearchEngine:
    """Get global optimized search engine instance"""
    global optimized_engine
    if optimized_engine is None:
        optimized_engine = OptimizedSearchEngine()
    return optimized_engine

if __name__ == "__main__":
    # Test the optimized search engine
    print("🚀 Testing Optimized Search Engine...")
    
    engine = OptimizedSearchEngine()
    
    # Health check
    health = engine.health_check()
    print(f"Health Status: {health['status']}")
    
    # Performance test
    start_time = time.time()
    results = engine.search("optimization", n_results=5)
    search_time = (time.time() - start_time) * 1000
    
    print(f"Search Results: {results['total_results']} found in {search_time:.1f}ms")
    
    # Cache test
    start_time = time.time()
    cached_results = engine.search("optimization", n_results=5)  # Should be cached
    cached_time = (time.time() - start_time) * 1000
    
    print(f"Cached Search: {cached_results['total_results']} found in {cached_time:.1f}ms")
    print(f"Performance Improvement: {(search_time/cached_time):.1f}x faster with cache")
    
    # Stats
    stats = engine.get_search_stats()
    print(f"Database: {stats['collection_stats']['total_documents']} documents")
    print(f"Cache: {stats['cache_stats']['connection_status']}")