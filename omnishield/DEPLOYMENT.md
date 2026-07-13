DO # 🚀 OmniShield Deployment Guide

This comprehensive guide covers deploying OmniShield to various environments, from local development to production Kubernetes clusters.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Database Migrations](#database-migrations)
7. [Monitoring Setup](#monitoring-setup)
8. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Git

### Backend Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/omnishield.git
cd omnishield/backend

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your local configuration

# 5. Run database migrations
alembic upgrade head

# 6. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd ../frontend

# 1. Install dependencies
npm install

# 2. Create environment file
cp .env.local.example .env.local
# Edit with your API URL

# 3. Start development server
npm run dev

# Access at http://localhost:3000
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ --asyncio-mode=auto --cov=app

# Frontend tests (when implemented)
cd frontend
npm test
```

---

## Docker Deployment

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/omnishield.git
cd omnishield

# 2. Create environment file
cp .env.example .env
# Edit .env with your configuration

# 3. Build and start all services
docker-compose up --build -d

# 4. Check service status
docker-compose ps

# 5. View logs
docker-compose logs -f backend

# 6. Run database migrations
docker-compose exec backend alembic upgrade head

# 7. Create admin user (optional)
docker-compose exec backend python scripts/create_admin.py
```

### Services Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Useful Docker Commands

```bash
# Stop all services
docker-compose down

# Rebuild specific service
docker-compose up -d --no-deps --build backend

# View resource usage
docker-compose stats

# Clean up (WARNING: deletes volumes)
docker-compose down -v

# Scale workers
docker-compose up -d --scale worker=5

# Execute command in container
docker-compose exec backend python manage.py shell
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Strong JWT secret configured
- [ ] Database credentials secured
- [ ] CORS origins restricted
- [ ] SSL/TLS certificates ready
- [ ] Backup strategy configured
- [ ] Monitoring tools setup
- [ ] Rate limiting configured
- [ ] Environment variables validated

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: ${DOCKER_REGISTRY}/omnishield-backend:${VERSION}
    restart: always
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
      - CORS_ORIGINS=${CORS_ORIGINS}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  worker:
    image: ${DOCKER_REGISTRY}/omnishield-backend:${VERSION}
    command: celery -A app.core.celery_app.celery_app worker --loglevel=info
    restart: always
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '4'
          memory: 8G

  frontend:
    image: ${DOCKER_REGISTRY}/omnishield-frontend:${VERSION}
    restart: always
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - certbot-data:/var/www/certbot
    depends_on:
      - backend
      - frontend

  certbot:
    image: certbot/certbot
    volumes:
      - certbot-data:/var/www/certbot
      - certbot-conf:/etc/letsencrypt
    command: certonly --webroot --webroot-path=/var/www/certbot --email ${SSL_EMAIL} --agree-tos --no-eff-email -d ${DOMAIN}

volumes:
  certbot-data:
  certbot-conf:
```

### nginx Configuration

Create `nginx/nginx.conf`:

```nginx
upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
}

upstream frontend {
    least_conn;
    server frontend:3000 max_fails=3 fail_timeout=30s;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name omnishield.ai www.omnishield.ai;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name omnishield.ai www.omnishield.ai;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;

    # API Routes
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Upload size
        client_max_body_size 10M;
    }

    # Docs
    location /docs {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend Routes
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2)$ {
        proxy_pass http://frontend;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;
}
```

### Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying OmniShield..."

# Configuration
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"

# Pull latest images
echo "📦 Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# Stop old containers
echo "🛑 Stopping old containers..."
docker-compose -f docker-compose.prod.yml down

# Start new containers
echo "▶️ Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

# Health check
echo "🏥 Running health checks..."
curl -f http://localhost:8000/health || exit 1

# Clean up old images
echo "🧹 Cleaning up..."
docker image prune -f

echo "✅ Deployment complete!"
echo "Frontend: https://omnishield.ai"
echo "API: https://omnishield.ai/api/v1"
echo "Docs: https://omnishield.ai/docs"
```

Make executable:
```bash
chmod +x deploy.sh
```

Run deployment:
```bash
./deploy.sh production v4.0.0
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3 (optional)

### Create Namespace

```bash
kubectl create namespace omnishield
kubectl config set-context --current --namespace=omnishield
```

### Secrets

Create `k8s/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: omnishield-secrets
type: Opaque
stringData:
  jwt-secret: <your-jwt-secret>
  database-url: postgresql://user:pass@postgres:5432/omnishield
  redis-url: redis://redis:6379/0
```

Apply:
```bash
kubectl apply -f k8s/secrets.yaml
```

### Database Deployment

`k8s/postgres.yaml`:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: omnishield
        - name: POSTGRES_USER
          value: omnishield
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: omnishield-secrets
              key: db-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
```

### Backend Deployment

`k8s/backend.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: yourusername/omnishield-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: production
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: omnishield-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: omnishield-secrets
              key: redis-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: omnishield-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
```

### Apply All Manifests

```bash
kubectl apply -f k8s/
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Environment Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | Yes | `development` | Deployment environment |
| `JWT_SECRET` | Yes | - | Secret key for JWT signing |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `REDIS_URL` | Yes | - | Redis connection string |
| `CORS_ORIGINS` | No | `["*"]` | Allowed CORS origins (comma-separated) |
| `MAX_FILE_SIZE_MB` | No | `10` | Maximum upload size |
| `DEFAULT_RATE_LIMIT_PER_MINUTE` | No | `60` | API rate limit |
| `USE_GPU` | No | `false` | Enable GPU acceleration |
| `ENABLE_PROMETHEUS_METRICS` | No | `true` | Enable metrics export |
| `SENTRY_DSN` | No | - | Sentry error tracking DSN |

### Generate Secrets

```bash
# JWT Secret
openssl rand -hex 32

# Database Password
openssl rand -base64 32

# API Key
python -c "import secrets; print(f'ak_{secrets.token_urlsafe(32)}')"
```

---

## Database Migrations

### Create Migration

```bash
# Auto-generate migration
cd backend
alembic revision --autogenerate -m "add new field"

# Edit migration file if needed
# migrations/versions/xxxx_add_new_field.py
```

### Apply Migrations

```bash
# Local
alembic upgrade head

# Docker
docker-compose exec backend alembic upgrade head

# Kubernetes
kubectl exec -it <backend-pod> -- alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>
```

---

## Monitoring Setup

### Prometheus Configuration

`prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'omnishield-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Import dashboard IDs:
- FastAPI: 15868
- PostgreSQL: 9628
- Redis: 11835
- Celery: 10636

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check database is running
docker-compose ps postgres

# Check connection
docker-compose exec backend python -c "from app.core.database import engine; print(engine)"

# View PostgreSQL logs
docker-compose logs postgres
```

#### 2. Redis Connection Failed

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

#### 3. Model Loading Errors

```bash
# Check model files exist
docker-compose exec backend ls -lh ~/.nudenet/

# Test model loading
docker-compose exec backend python -c "from app.services.ai_moderation import get_detector; get_detector()"
```

#### 4. High Memory Usage

```bash
# Check container stats
docker stats

# Restart services
docker-compose restart backend worker

# Scale down workers
docker-compose up -d --scale worker=2
```

#### 5. Slow API Response

```bash
# Check database queries
docker-compose exec postgres psql -U omnishield -c "SELECT * FROM pg_stat_activity;"

# Check Redis cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace

# View API logs
docker-compose logs -f --tail=100 backend
```

### Useful Commands

```bash
# View all logs
docker-compose logs -f

# Shell into backend
docker-compose exec backend bash

# Database shell
docker-compose exec postgres psql -U omnishield

# Redis CLI
docker-compose exec redis redis-cli

# Test API endpoint
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

---

## Performance Tuning

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_logs_user_created ON moderation_logs(user_id, created_at DESC);

-- Analyze tables
ANALYZE moderation_logs;

-- Vacuum tables
VACUUM ANALYZE moderation_logs;
```

### Redis Tuning

```bash
# Set memory limit
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Enable persistence
redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### nginx Tuning

```nginx
# Increase worker connections
worker_processes auto;
worker_connections 4096;

# Enable caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;
```

---

## Backup & Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U omnishield omnishield > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T postgres psql -U omnishield omnishield < backup_20260706.sql
```

### Automated Backups

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/omnishield_$TIMESTAMP.sql.gz"

# Create backup
docker-compose exec -T postgres pg_dump -U omnishield omnishield | gzip > $BACKUP_FILE

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE s3://your-bucket/backups/

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup complete: $BACKUP_FILE"
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

---

## Support

- **Documentation**: https://docs.omnishield.ai
- **Issues**: https://github.com/yourusername/omnishield/issues
- **Email**: support@omnishield.ai

---

**Last Updated**: 2026-07-06  
**Version**: 4.0.0
