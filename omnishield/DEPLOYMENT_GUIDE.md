# OmniShield Deployment Guide

Complete deployment guide for the AI Content Moderation Platform.

## Tech Stack Summary

### Frontend
- **React 18** + TypeScript
- **Vite** - Build tool
- **React Router** - Routing
- **Axios** - HTTP client
- **TanStack Query** - State management
- **Recharts** - Charts
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Backend
- **FastAPI** - API framework
- **Python 3.11+**
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Redis** - Caching
- **Celery** - Task queue
- **JWT** - Authentication

### AI/ML Stack
- **PyTorch** - Deep learning
- **OpenCV** - Computer vision
- **NudeNet** - NSFW detection
- **YOLO (Ultralytics)** - Object detection
- **Transformers** - NLP models
- **PaddleOCR** - Text detection
- **Pillow** - Image processing
- **NumPy** - Numerical computing

### Storage
- **Cloudinary** - Image hosting (primary)
- **AWS S3** - Alternative storage (optional)

### Deployment
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **GitHub Actions** - CI/CD
- **Vercel** - Frontend hosting
- **Railway/Render** - Backend hosting

## Local Development

### Prerequisites

```bash
# Required
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

# Optional (for full features)
- CUDA toolkit (for GPU)
- Docker & Docker Compose
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp ../.env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Create tables
python create_tables.py

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend-react

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

### Redis & Celery

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

## Docker Deployment

### Build and Run

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild specific service
docker-compose up -d --build backend
```

### Services

- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Cloud Deployment

### 1. Frontend (Vercel)

```bash
cd frontend-react

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

**Environment Variables:**
```
VITE_API_URL=https://your-backend-api.com/api/v1
```

### 2. Backend (Railway)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to service
railway link

# Deploy
railway up
```

**Environment Variables:**
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET=your-secret-key
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
CORS_ORIGINS=https://your-frontend.vercel.app
ENVIRONMENT=production
```

### 3. Backend (Render)

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Deploy

### 4. Database (Railway PostgreSQL)

```bash
# Create PostgreSQL service
railway add postgresql

# Get connection string
railway variables
```

### 5. Redis (Railway Redis)

```bash
# Create Redis service
railway add redis

# Get connection string
railway variables
```

## Cloudinary Setup

1. Create account at https://cloudinary.com
2. Get credentials from Dashboard
3. Add to backend .env:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## AWS S3 Setup (Optional)

```env
AWS_REGION=us-east-1
S3_BUCKET_NAME=omnishield-storage
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
```

## GitHub Actions CI/CD

### Required Secrets

Go to Settings → Secrets and variables → Actions:

```
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID
RAILWAY_TOKEN
DOCKER_USERNAME
DOCKER_PASSWORD
```

### Workflow

1. Push to main branch
2. GitHub Actions runs tests
3. Builds Docker images
4. Deploys to Vercel (frontend)
5. Deploys to Railway (backend)

## SSL/HTTPS

### Nginx with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Monitoring

### Prometheus Metrics

Backend exposes metrics at `/metrics`

```bash
# Access metrics
curl http://localhost:8000/metrics
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:80
```

## Performance Optimization

### Backend

- Enable GPU: `USE_GPU=true`
- Increase workers: `uvicorn app.main:app --workers 4`
- Redis caching enabled by default
- Connection pooling for PostgreSQL

### Frontend

- Vite optimizes bundle size
- Code splitting with React.lazy()
- Image optimization with Cloudinary
- Nginx gzip compression

## Security Checklist

- [ ] Change JWT_SECRET in production
- [ ] Use strong database password
- [ ] Restrict CORS_ORIGINS
- [ ] Enable HTTPS
- [ ] Set secure cookie flags
- [ ] Configure rate limiting
- [ ] Enable Cloudflare (optional)
- [ ] Set up WAF rules
- [ ] Regular security updates

## Troubleshooting

### Backend not starting

```bash
# Check logs
docker-compose logs backend

# Verify database connection
docker-compose exec backend python -c "from app.core.database import engine; print(engine)"
```

### Frontend build fails

```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Redis connection failed

```bash
# Check Redis status
redis-cli ping  # Should return PONG

# Restart Redis
docker-compose restart redis
```

### Database migration issues

```bash
# Reset migrations
cd backend
alembic downgrade base
alembic upgrade head
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend workers
docker-compose up -d --scale backend=3

# Scale Celery workers
docker-compose up -d --scale celery=3
```

### Load Balancing

Use Nginx as load balancer:

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

## Cost Estimation

### Free Tier (Development)

- Vercel: Free (hobby)
- Railway: $5/month (500 hours)
- Cloudinary: Free (25 credits/month)
- GitHub Actions: 2000 min/month

### Production (Estimated)

- Vercel Pro: $20/month
- Railway Pro: $20/month
- Cloudinary: $99/month (Advanced)
- PostgreSQL: $15/month (managed)
- Redis: $10/month (managed)

**Total: ~$164/month**

## Support

- Documentation: `/docs`
- API Docs: `/api/v1/docs`
- Issues: GitHub Issues
- Email: support@omnishield.ai

## License

Proprietary - All Rights Reserved
