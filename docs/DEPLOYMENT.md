# Claude AI Conversation Analyzer - Deployment Guide

## 🚀 Production Deployment

This guide covers deploying the Claude AI Conversation Analyzer in production environments, showcasing enterprise-ready deployment practices.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Memory**: 4GB+ RAM (8GB+ recommended for production)
- **Storage**: 10GB+ available disk space
- **CPU**: 2+ cores (4+ cores recommended for high load)

### Required Software
- **Docker**: 20.10+ and Docker Compose 2.0+
- **Python**: 3.9+ (if running without Docker)
- **Git**: For source code management
- **SSL Certificate**: For HTTPS in production

## 🏗️ Architecture Overview

### Production Architecture
```
Internet → Load Balancer → Application → Vector Database
    ↓           ↓             ↓              ↓
   SSL      Rate Limiting   Processing    ChromaDB
    ↓           ↓             ↓              ↓
Security → Monitoring → Performance → Data Storage
```

### Component Scaling
- **Web Application**: Horizontal scaling with load balancer
- **Vector Database**: ChromaDB with persistent storage
- **Cache Layer**: Redis for performance optimization
- **Monitoring**: Health checks and metrics collection

## 🐳 Docker Deployment (Recommended)

### Quick Production Deployment
```bash
# Clone repository
git clone https://github.com/yourusername/claude-ai-conversation-analyzer.git
cd claude-ai-conversation-analyzer

# Copy production environment
cp .env.example .env
# Edit .env with production configuration

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
curl http://localhost/api/health
```

### Production Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - FLASK_ENV=production
      - GUNICORN_WORKERS=4
      - GUNICORN_TIMEOUT=120
    volumes:
      - ./data:/app/data:ro
      - ./logs:/app/logs
    depends_on:
      - chroma
      - redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

  chroma:
    image: chromadb/chroma:latest
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
    volumes:
      - chroma_data:/chroma/chroma
    restart: unless-stopped

  redis:
    image: redis:alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  chroma_data:
  redis_data:
```

### Production Environment Configuration
```bash
# .env for production
FLASK_ENV=production
FLASK_SECRET_KEY=your-secure-secret-key-here

# Database Configuration
CHROMA_HOST=chroma
CHROMA_PORT=8000
REDIS_URL=redis://redis:6379

# Performance Settings
MAX_SEARCH_RESULTS=50
CHUNK_SIZE=1200
CHUNK_OVERLAP=200
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120

# Security
ENABLE_RATE_LIMITING=true
API_RATE_LIMIT=100
CORS_ORIGINS=https://yourdomain.com

# Monitoring
SENTRY_DSN=your-sentry-dsn-here
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

## 🌐 Cloud Platform Deployment

### AWS ECS Deployment
```yaml
# ecs-task-definition.json
{
  "family": "claude-ai-conversation-analyzer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "youraccount/claude-ai-conversation-analyzer:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/claude-ai-analyzer",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run Deployment
```yaml
# cloudrun.yml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: claude-ai-conversation-analyzer
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/PROJECT_ID/claude-ai-conversation-analyzer
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
```

### Kubernetes Deployment
```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-ai-conversation-analyzer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: claude-ai-analyzer
  template:
    metadata:
      labels:
        app: claude-ai-analyzer
    spec:
      containers:
      - name: app
        image: claude-ai-conversation-analyzer:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: claude-ai-analyzer-service
spec:
  selector:
    app: claude-ai-analyzer
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

## 🔒 Security Configuration

### SSL/TLS Setup
```nginx
# nginx.conf
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://app:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
}

# Rate limiting configuration
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
}
```

### Environment Security
```bash
# Use secure secret generation
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set secure file permissions
chmod 600 .env
chmod 600 ssl/*

# Use Docker secrets for sensitive data
docker secret create flask_secret_key /path/to/secret
```

## 📊 Monitoring & Observability

### Health Checks
```python
# Health check endpoint
@app.route('/api/health')
def health_check():
    """Comprehensive health check for load balancers."""
    try:
        # Check database connectivity
        collection = chroma_client.get_collection("claude_conversations")
        
        # Check Redis connectivity
        redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "services": {
                "database": "healthy",
                "cache": "healthy",
                "api": "healthy"
            }
        }, 200
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, 503
```

### Metrics Collection
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'claude-ai-analyzer'
    static_configs:
      - targets: ['app:5000']
    metrics_path: '/api/metrics'
    scrape_interval: 30s
```

### Logging Configuration
```python
# logging.conf
[loggers]
keys=root,app

[handlers]
keys=console,file,syslog

[formatters]
keys=json

[logger_root]
level=INFO
handlers=console,file

[logger_app]
level=INFO
handlers=file,syslog
qualname=app

[handler_file]
class=logging.handlers.RotatingFileHandler
args=('/app/logs/app.log', 'a', 10485760, 5)
formatter=json

[formatter_json]
class=pythonjsonlogger.jsonlogger.JsonFormatter
format=%(asctime)s %(name)s %(levelname)s %(message)s
```

## 🔧 Performance Optimization

### Production Optimizations
```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

### Database Optimization
```python
# ChromaDB optimization
chroma_client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST"),
    port=os.getenv("CHROMA_PORT"),
    settings=Settings(
        chroma_db_impl="clickhouse",
        clickhouse_host="localhost",
        clickhouse_port=8123,
        persist_directory="/chroma/data"
    )
)
```

### Caching Strategy
```python
# Redis caching configuration
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    decode_responses=True,
    health_check_interval=30
)

# Cache configuration
CACHE_TTL = 1800  # 30 minutes
CACHE_MAX_KEYS = 10000
```

## 📈 Scaling Guidelines

### Horizontal Scaling
```bash
# Scale application instances
docker-compose up --scale app=4

# Kubernetes scaling
kubectl scale deployment claude-ai-analyzer --replicas=5
```

### Load Testing
```bash
# Apache Bench testing
ab -n 1000 -c 10 http://localhost/api/search?query=test

# Artillery load testing
artillery run load-test.yml
```

### Performance Monitoring
```bash
# Monitor resource usage
docker stats claude-ai-conversation-analyzer

# Database performance
curl http://localhost/api/metrics | jq '.database'

# Application metrics
curl http://localhost/api/metrics | jq '.performance'
```

## 🚨 Troubleshooting

### Common Issues
```bash
# Container won't start
docker logs claude-ai-analyzer-app

# Database connection issues
docker exec -it claude-ai-analyzer-chroma chroma --version

# Performance issues
docker exec -it claude-ai-analyzer-app htop

# SSL certificate issues
openssl x509 -in cert.pem -text -noout
```

### Performance Debugging
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Profile API endpoints
from flask_profiler import Profiler
profiler = Profiler()
profiler.init_app(app)
```

## 📋 Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrations completed
- [ ] Load testing performed
- [ ] Security scan completed
- [ ] Backup strategy implemented

### Post-deployment
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Log aggregation working
- [ ] Performance metrics baseline
- [ ] Disaster recovery tested
- [ ] Documentation updated

## 🔄 CI/CD Pipeline

### GitHub Actions Deployment
```yaml
# .github/workflows/deploy.yml
name: Production Deployment

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker image
      run: |
        docker build -t ${{ secrets.REGISTRY }}/claude-ai-analyzer:${{ github.ref_name }} .
        docker push ${{ secrets.REGISTRY }}/claude-ai-analyzer:${{ github.ref_name }}
    
    - name: Deploy to production
      run: |
        ssh ${{ secrets.PRODUCTION_HOST }} "
          docker pull ${{ secrets.REGISTRY }}/claude-ai-analyzer:${{ github.ref_name }}
          docker-compose up -d
        "
```

---

*This deployment guide demonstrates enterprise-ready deployment practices, showcasing DevOps expertise and production system management capabilities.*