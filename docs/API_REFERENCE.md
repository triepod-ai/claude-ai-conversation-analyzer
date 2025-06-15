# Claude AI Conversation Analyzer - API Reference

## 🔌 API Overview

The Claude AI Conversation Analyzer provides a RESTful API for semantic search, performance monitoring, and system management. All endpoints return JSON responses and support CORS for frontend integration.

## 🚀 Base Information

- **Base URL**: `http://localhost:5000/api`
- **Authentication**: None required for demo mode
- **Rate Limiting**: 100 requests/minute (configurable)
- **Response Format**: JSON
- **CORS**: Enabled for development

## 📊 Core Endpoints

### Search API

#### Semantic Search
Search across Claude AI conversations using semantic similarity.

```http
GET /api/search
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query text |
| `limit` | integer | No | Number of results (default: 10, max: 50) |
| `category` | string | No | Filter by category |
| `project` | string | No | Filter by project name |
| `min_score` | float | No | Minimum similarity score (0.0-1.0) |

**Example Request:**
```bash
curl "http://localhost:5000/api/search?query=machine%20learning&limit=5&category=technical_development"
```

**Example Response:**
```json
{
  "status": "success",
  "query": "machine learning",
  "results": [
    {
      "id": "chunk_12345",
      "content": "Discussion about machine learning optimization techniques...",
      "similarity_score": 0.89,
      "category": "technical_development",
      "project_name": "AI System Architecture",
      "metadata": {
        "creator": "Claude AI",
        "created_date": "2024-06-15T10:30:00Z",
        "chunk_position": 3
      }
    }
  ],
  "total_results": 1,
  "processing_time_ms": 45,
  "cache_hit": false
}
```

#### Advanced Search
Multi-field search with complex filtering.

```http
POST /api/search/advanced
```

**Request Body:**
```json
{
  "query": "microservices architecture",
  "filters": {
    "categories": ["technical_development", "business_analysis"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-06-15"
    },
    "projects": ["System Design", "Architecture Review"]
  },
  "options": {
    "limit": 20,
    "min_score": 0.7,
    "include_metadata": true,
    "highlight_matches": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "results": [...],
  "facets": {
    "categories": {
      "technical_development": 12,
      "business_analysis": 3
    },
    "projects": {
      "System Design": 8,
      "Architecture Review": 7
    }
  },
  "search_metadata": {
    "total_time_ms": 67,
    "vector_search_time_ms": 45,
    "filtering_time_ms": 12,
    "ranking_time_ms": 10
  }
}
```

### Category API

#### List Categories
Get all available content categories with counts.

```http
GET /api/categories
```

**Response:**
```json
{
  "status": "success",
  "categories": [
    {
      "name": "technical_development",
      "display_name": "Technical Development",
      "description": "Code, APIs, databases, integrations",
      "count": 1247,
      "percentage": 26.8
    },
    {
      "name": "business_analysis", 
      "display_name": "Business Analysis",
      "description": "Requirements, processes, specifications",
      "count": 856,
      "percentage": 18.4
    }
  ],
  "total_chunks": 4647
}
```

#### Category Details
Get detailed information about a specific category.

```http
GET /api/categories/{category_name}
```

**Response:**
```json
{
  "status": "success",
  "category": {
    "name": "technical_development",
    "display_name": "Technical Development", 
    "description": "Code, APIs, databases, integrations",
    "count": 1247,
    "percentage": 26.8,
    "sample_keywords": ["API", "database", "microservices", "Docker"],
    "recent_activity": "2024-06-15T14:22:00Z"
  }
}
```

### Performance API

#### System Health
Check system health and availability.

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-15T15:30:00Z",
  "services": {
    "api": {
      "status": "healthy",
      "response_time_ms": 5
    },
    "database": {
      "status": "healthy", 
      "response_time_ms": 12,
      "connection_pool": "8/10 connections"
    },
    "cache": {
      "status": "healthy",
      "hit_rate": 87.5,
      "memory_usage_mb": 450
    }
  },
  "system": {
    "uptime_seconds": 86400,
    "memory_usage_mb": 1847,
    "cpu_usage_percent": 34.2
  }
}
```

#### Performance Metrics
Get detailed performance statistics.

```http
GET /api/metrics
```

**Response:**
```json
{
  "status": "success",
  "metrics": {
    "processing": {
      "conversations_per_second": 398.4,
      "total_conversations_processed": 1435,
      "total_chunks_generated": 46424,
      "error_rate_percent": 0.0
    },
    "search": {
      "average_response_time_ms": 45,
      "queries_per_minute": 1200,
      "cache_hit_rate_percent": 87.5,
      "total_queries_today": 15670
    },
    "system": {
      "memory_peak_mb": 1847,
      "memory_current_mb": 1234,
      "cpu_average_percent": 34.2,
      "uptime_hours": 24.0
    }
  },
  "timestamp": "2024-06-15T15:30:00Z"
}
```

#### Performance History
Get historical performance data.

```http
GET /api/metrics/history?period=24h&interval=1h
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | Time period (1h, 24h, 7d, 30d) |
| `interval` | string | Data interval (1m, 5m, 1h, 1d) |

**Response:**
```json
{
  "status": "success",
  "period": "24h",
  "interval": "1h", 
  "data": [
    {
      "timestamp": "2024-06-15T14:00:00Z",
      "queries_count": 1247,
      "avg_response_time_ms": 42,
      "cache_hit_rate": 89.2,
      "error_count": 0
    }
  ]
}
```

### Data Management API

#### Import Status
Check the status of data imports.

```http
GET /api/import/status
```

**Response:**
```json
{
  "status": "success",
  "imports": [
    {
      "id": "import_20240615_1500",
      "status": "completed",
      "started_at": "2024-06-15T15:00:00Z",
      "completed_at": "2024-06-15T15:03:36Z",
      "conversations_processed": 1435,
      "chunks_generated": 46424,
      "processing_rate": 398.4
    }
  ]
}
```

#### Collection Statistics
Get statistics about the current data collection.

```http
GET /api/collection/stats
```

**Response:**
```json
{
  "status": "success",
  "collection": {
    "name": "claude_project_chats",
    "total_chunks": 46424,
    "total_conversations": 1435,
    "categories": 9,
    "size_mb": 156.7,
    "last_updated": "2024-06-15T15:03:36Z"
  },
  "breakdown": {
    "by_category": {
      "technical_development": 12456,
      "business_analysis": 8967,
      "data_analytics": 7834
    },
    "by_project": {
      "System Architecture": 15678,
      "Performance Analysis": 12890,
      "API Design": 9876
    }
  }
}
```

## 🔧 Configuration API

#### Get Configuration
Retrieve current system configuration.

```http
GET /api/config
```

**Response:**
```json
{
  "status": "success",
  "config": {
    "search": {
      "max_results": 50,
      "default_limit": 10,
      "similarity_threshold": 0.7
    },
    "processing": {
      "chunk_size": 1200,
      "chunk_overlap": 200,
      "batch_size": 1000
    },
    "performance": {
      "cache_ttl_minutes": 30,
      "rate_limit_per_minute": 100,
      "max_concurrent_users": 100
    }
  }
}
```

## 🚨 Error Handling

### Error Response Format
All error responses follow a consistent format:

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_QUERY",
    "message": "Query parameter is required",
    "details": "The 'query' parameter must be provided for search requests"
  },
  "timestamp": "2024-06-15T15:30:00Z",
  "request_id": "req_12345"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_QUERY` | 400 | Missing or invalid query parameter |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `SEARCH_TIMEOUT` | 504 | Search operation timed out |
| `DATABASE_ERROR` | 503 | Database connection issue |
| `INVALID_CATEGORY` | 400 | Unknown category specified |
| `INVALID_LIMIT` | 400 | Limit exceeds maximum allowed |

## 📡 WebSocket API

### Real-time Updates
Connect to receive real-time performance updates.

```javascript
const ws = new WebSocket('ws://localhost:5000/ws/metrics');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Real-time metrics:', data);
};
```

**Message Format:**
```json
{
  "type": "metrics_update",
  "data": {
    "timestamp": "2024-06-15T15:30:00Z",
    "current_queries_per_minute": 1250,
    "avg_response_time_ms": 47,
    "active_users": 23
  }
}
```

## 🔐 Authentication (Production)

### API Key Authentication
For production deployments, API key authentication is available:

```http
Authorization: Bearer your_api_key_here
```

### Rate Limiting Headers
Response headers include rate limiting information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1623456000
```

## 📊 SDK Examples

### Python SDK Example
```python
import requests

class ClaudeAIAnalyzer:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
    
    def search(self, query, limit=10, category=None):
        params = {"query": query, "limit": limit}
        if category:
            params["category"] = category
        
        response = requests.get(f"{self.base_url}/search", params=params)
        return response.json()
    
    def get_metrics(self):
        response = requests.get(f"{self.base_url}/metrics")
        return response.json()

# Usage
analyzer = ClaudeAIAnalyzer()
results = analyzer.search("machine learning", limit=5)
print(f"Found {len(results['results'])} results")
```

### JavaScript SDK Example
```javascript
class ClaudeAIAnalyzer {
  constructor(baseUrl = 'http://localhost:5000/api') {
    this.baseUrl = baseUrl;
  }
  
  async search(query, options = {}) {
    const params = new URLSearchParams({
      query,
      limit: options.limit || 10,
      ...(options.category && { category: options.category })
    });
    
    const response = await fetch(`${this.baseUrl}/search?${params}`);
    return response.json();
  }
  
  async getMetrics() {
    const response = await fetch(`${this.baseUrl}/metrics`);
    return response.json();
  }
}

// Usage
const analyzer = new ClaudeAIAnalyzer();
const results = await analyzer.search('microservices architecture');
console.log(`Processing time: ${results.processing_time_ms}ms`);
```

## 🔗 Integration Examples

### cURL Examples
```bash
# Basic search
curl "http://localhost:5000/api/search?query=docker%20containers&limit=5"

# Health check
curl http://localhost:5000/api/health

# Performance metrics
curl http://localhost:5000/api/metrics

# Category information
curl http://localhost:5000/api/categories
```

### Postman Collection
A comprehensive Postman collection is available at `/docs/postman_collection.json` with all endpoints pre-configured for testing.

---

*This API provides comprehensive access to the Claude AI Conversation Analyzer's capabilities, enabling integration with external systems and custom applications.*