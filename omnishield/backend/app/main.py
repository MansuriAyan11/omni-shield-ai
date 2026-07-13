from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.api import auth, keys, moderate, analytics

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise AI-powered Image Moderation Platform API with Multi-Model Detection",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "OmniShield Support",
        "email": "support@omnishield.ai",
        "url": "https://omnishield.ai"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Set up CORS middleware - Allow all origins in development
if settings.ENVIRONMENT == "production":
    cors_origins = settings.cors_origins_list
else:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add security headers
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # API versioning header
    response.headers["X-API-Version"] = settings.VERSION
    
    return response

# Register endpoints under prefix /api/v1
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(keys.router, prefix=settings.API_V1_STR)
app.include_router(moderate.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health"])
def root():
    """Root endpoint with API information"""
    return {
        "success": True,
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "features": {
            "multi_model_detection": True,
            "models": ["nsfw", "violence", "weapons", "faces", "text"],
            "oauth_providers": ["google", "github"] if settings.GOOGLE_CLIENT_ID else []
        }
    }

@app.get("/health", tags=["Health"])
def health():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "operational",
            "database": "operational",
            "cache": "operational"
        }
    }

# Prometheus metrics endpoint (if enabled)
if settings.ENABLE_PROMETHEUS_METRICS:
    try:
        from prometheus_client import make_asgi_app
        
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        logger.info("Prometheus metrics endpoint enabled at /metrics")
    except ImportError:
        logger.warning("prometheus-client not installed, metrics endpoint disabled")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} starting up...")
    logger.info(f"📝 Environment: {settings.ENVIRONMENT}")
    logger.info(f"📚 API Documentation: /docs")
    logger.info(f"🔒 CORS Origins: {cors_origins}")
    
    if settings.ENVIRONMENT == "production" and settings.CORS_ORIGINS == ["*"]:
        logger.warning("⚠️  CORS is allowing all origins in production!")
    
    logger.info("✅ API successfully loaded and configured")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"🛑 {settings.PROJECT_NAME} shutting down...")
