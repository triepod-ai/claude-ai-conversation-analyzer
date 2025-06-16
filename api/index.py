#!/usr/bin/env python3
"""
AI Conversation Analyzer - Vercel Deployment
Minimal Flask app for portfolio demo
"""

from flask import Flask, render_template, jsonify
import json
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'portfolio-demo-key'

# Mock demo data
demo_stats = {
    'total_conversations': 1247,
    'total_chunks': 8934,
    'categories': {
        'technical_development': 324,
        'business_analysis': 189,
        'ai_ml_research': 267,
        'project_management': 156,
        'system_architecture': 203,
        'data_analytics': 108
    },
    'avg_chunk_size': 512,
    'system_health': 'excellent',
    'processing_speed': '398.4 conversations/second',
    'error_rate': '0%'
}

@app.route('/')
def index():
    """Portfolio homepage"""
    return jsonify({
        'message': 'AI Conversation Analyzer - Portfolio Demo',
        'status': 'active',
        'stats': demo_stats,
        'endpoints': {
            'search': '/api/search?query=your_query',
            'stats': '/api/stats',
            'health': '/api/health'
        }
    })

@app.route('/api/search')
def api_search():
    """Mock search API"""
    from flask import request
    
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    # Mock search results
    mock_results = [
        {
            'rank': 1,
            'content': f'Sample result for "{query}" - Advanced discussion about machine learning optimization techniques...',
            'similarity': 92,
            'source_name': 'ML Architecture Discussion',
            'category': 'ai_ml_research'
        },
        {
            'rank': 2,
            'content': f'Related content for "{query}" - System design patterns and scalability considerations...',
            'similarity': 87,
            'source_name': 'System Design Review',
            'category': 'system_architecture'
        }
    ]
    
    return jsonify({
        'results': mock_results,
        'total_found': len(mock_results),
        'query': query,
        'processing_time': round(random.uniform(0.1, 0.5), 3),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/stats')
def api_stats():
    """System statistics"""
    current_stats = demo_stats.copy()
    current_stats.update({
        'uptime': f"{random.randint(5, 30)} days",
        'memory_usage': f"{random.randint(150, 250)}MB",
        'cpu_usage': f"{random.randint(5, 25)}%",
        'last_updated': datetime.now().isoformat()
    })
    return jsonify(current_stats)

@app.route('/api/health')
def api_health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'system': 'operational',
        'database': 'connected',
        'search_engine': 'active',
        'performance': 'excellent',
        'timestamp': datetime.now().isoformat()
    })

# Vercel handler
def handler(request):
    return app