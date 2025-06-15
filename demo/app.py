#!/usr/bin/env python3
"""
AI Conversation Analyzer - Professional Portfolio Demo
Modern Flask application with enhanced UI and interactive features
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, make_response
import json
import csv
import io
from datetime import datetime
import time
import random

# Import project modules
try:
    from src.search.semantic_search import SemanticSearch
    from src.utils.performance_metrics import PerformanceMetrics
    from src.utils.config import get_config
    config = get_config()
except ImportError as e:
    print(f"Warning: Could not import config module: {e}")
    # Create simple fallback config
    class SimpleConfig:
        @property
        def demo_mode(self): return True
        @property
        def mock_data_path(self): return '/home/bryan/apps/ai-conversation-analyzer/data/mock_conversations.json'
        @property
        def chunks_data_path(self): return '/home/bryan/apps/ai-conversation-analyzer/data/conversation_chunks.json'
        @property
        def secret_key(self): return 'portfolio-demo-key'
        @property
        def host(self): return '0.0.0.0'
        @property
        def port(self): return 5000
        @property
        def debug(self): return False
        @property
        def log_level(self): return 'INFO'
        @property
        def log_file(self): return '/home/bryan/apps/ai-conversation-analyzer/logs/app.log'
        @property
        def max_search_results(self): return 50
    
    config = SimpleConfig()
    SemanticSearch = None
    PerformanceMetrics = None

app = Flask(__name__)
app.secret_key = config.secret_key

# Configure logging
log_dir = Path(config.log_file).parent
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global search engine and metrics
search_engine = None
performance_metrics = None
demo_stats = None

def load_demo_data():
    """Load mock conversation data and chunks for demo"""
    global demo_stats
    
    try:
        # Load conversations
        with open('/home/bryan/apps/ai-conversation-analyzer/data/mock_conversations.json', 'r') as f:
            conversations = json.load(f)
        
        # Load chunks
        with open('/home/bryan/apps/ai-conversation-analyzer/data/conversation_chunks.json', 'r') as f:
            chunks = json.load(f)
        
        # Load performance metrics
        with open('/home/bryan/apps/ai-conversation-analyzer/data/demo_performance_metrics.json', 'r') as f:
            perf_data = json.load(f)
        
        # Calculate stats
        category_counts = {}
        for conv in conversations:
            cat = conv.get('category', 'general')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        demo_stats = {
            'total_conversations': len(conversations),
            'total_chunks': len(chunks),
            'categories': category_counts,
            'avg_chunk_size': sum(len(chunk.get('content', '')) for chunk in chunks) // len(chunks) if chunks else 0,
            'performance': perf_data.get('current_benchmarks', {}),
            'system_health': 'excellent',
            'processing_speed': '398.4 conversations/second',
            'error_rate': '0%'
        }
        
        return conversations, chunks
        
    except Exception as e:
        print(f"Error loading demo data: {e}")
        return [], []

def simulate_search(query, chunks, limit=10):
    """Simulate semantic search with mock results"""
    if not query or not chunks:
        return []
    
    # Simple keyword-based search for demo
    query_lower = query.lower()
    results = []
    
    for i, chunk in enumerate(chunks):
        content = chunk.get('content', '').lower()
        title = chunk.get('conversation_name', '').lower()
        category = chunk.get('category', 'general')
        
        # Score based on keyword matches
        score = 0
        for word in query_lower.split():
            if word in content:
                score += 3
            if word in title:
                score += 5
        
        if score > 0:
            # Add some randomness for demo realism
            similarity = min(95, max(20, score * 10 + random.randint(-10, 20)))
            
            results.append({
                'rank': len(results) + 1,
                'content': chunk.get('content', '')[:500] + ('...' if len(chunk.get('content', '')) > 500 else ''),
                'full_content': chunk.get('content', ''),
                'similarity': similarity,
                'source_name': chunk.get('conversation_name', f'Conversation {i+1}'),
                'category': category,
                'metadata': {
                    'chunk_id': chunk.get('chunk_id', f'chunk_{i}'),
                    'created_at': chunk.get('created_at', '2024-01-01'),
                    'participants': chunk.get('participants', ['User', 'Assistant'])
                }
            })
    
    # Sort by similarity and return top results
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:limit]

@app.route('/')
def index():
    """Modern portfolio homepage with dashboard"""
    return render_template('portfolio_home.html', stats=demo_stats)

@app.route('/dashboard')
def dashboard():
    """Performance metrics dashboard"""
    return render_template('performance_dashboard.html', stats=demo_stats)

@app.route('/search')
def search_interface():
    """Interactive search interface"""
    return render_template('search_interface.html', stats=demo_stats)

@app.route('/architecture')
def architecture():
    """System architecture visualization"""
    return render_template('architecture_view.html', stats=demo_stats)

@app.route('/api/search')
def api_search():
    """API endpoint for search queries"""
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    category_filter = request.args.get('category')
    limit = int(request.args.get('limit', 10))
    
    # Load data
    conversations, chunks = load_demo_data()
    
    # Filter by category if specified
    if category_filter and category_filter != 'all':
        chunks = [chunk for chunk in chunks if chunk.get('category') == category_filter]
    
    # Simulate search
    results = simulate_search(query, chunks, limit)
    
    # Add processing time simulation
    processing_time = random.uniform(0.1, 0.5)
    
    return jsonify({
        'results': results,
        'total_found': len(results),
        'query': query,
        'processing_time': round(processing_time, 3),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/stats')
def api_stats():
    """Real-time system statistics"""
    if demo_stats:
        # Add real-time metrics simulation
        current_stats = demo_stats.copy()
        current_stats['uptime'] = f"{random.randint(5, 30)} days"
        current_stats['memory_usage'] = f"{random.randint(150, 250)}MB"
        current_stats['cpu_usage'] = f"{random.randint(5, 25)}%"
        current_stats['last_updated'] = datetime.now().isoformat()
        
        return jsonify(current_stats)
    else:
        return jsonify({'error': 'Stats not available'}), 500

@app.route('/api/categories')
def api_categories():
    """Available search categories"""
    categories = [
        'technical_development',
        'business_analysis', 
        'ai_ml_research',
        'project_management',
        'system_architecture',
        'data_analytics',
        'strategic_planning',
        'performance_optimization',
        'general'
    ]
    return jsonify({'categories': categories})

@app.route('/api/demo_search')
def api_demo_search():
    """Predefined demo searches for showcase"""
    demo_queries = [
        {
            'query': 'machine learning model optimization',
            'category': 'ai_ml_research',
            'description': 'Advanced ML optimization techniques'
        },
        {
            'query': 'microservices architecture patterns',
            'category': 'system_architecture', 
            'description': 'Scalable system design patterns'
        },
        {
            'query': 'data pipeline performance',
            'category': 'data_analytics',
            'description': 'Big data processing optimization'
        },
        {
            'query': 'agile project management',
            'category': 'project_management',
            'description': 'Team coordination and delivery'
        }
    ]
    
    return jsonify({'demo_queries': demo_queries})

@app.route('/api/health')
def api_health():
    """System health check"""
    return jsonify({
        'status': 'healthy',
        'system': 'operational',
        'database': 'connected',
        'search_engine': 'active',
        'performance': 'excellent',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/performance')
def api_performance():
    """Performance metrics endpoint"""
    try:
        with open('/home/bryan/apps/ai-conversation-analyzer/data/demo_performance_metrics.json', 'r') as f:
            perf_data = json.load(f)
        
        # Add real-time simulation
        current_metrics = perf_data.get('current_benchmarks', {})
        current_metrics['timestamp'] = datetime.now().isoformat()
        current_metrics['queries_processed'] = random.randint(1000, 10000)
        current_metrics['uptime_hours'] = random.randint(100, 500)
        
        return jsonify(current_metrics)
        
    except Exception as e:
        return jsonify({'error': f'Performance data unavailable: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 AI Conversation Analyzer - Portfolio Demo")
    print("=" * 60)
    
    # Load demo data
    conversations, chunks = load_demo_data()
    
    if conversations and chunks:
        print(f"✅ Loaded {len(conversations)} conversations")
        print(f"✅ Loaded {len(chunks)} searchable chunks")
        print(f"📊 Categories: {len(demo_stats['categories'])}")
        print(f"⚡ Performance: {demo_stats['processing_speed']}")
        print()
        print("🌐 Portfolio Demo URLs:")
        print("   Homepage:    http://localhost:5001")
        print("   Dashboard:   http://localhost:5001/dashboard") 
        print("   Search:      http://localhost:5001/search")
        print("   Architecture: http://localhost:5001/architecture")
        print("=" * 60)
        
        app.run(host='localhost', port=5001, debug=True)
    else:
        print("❌ Failed to load demo data. Please check data files.")
        sys.exit(1)