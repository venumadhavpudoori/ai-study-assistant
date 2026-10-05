from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.core.db import async_engine
from app.api.v1 import auth, workspaces, documents, conversations
from app.api.v1.auth import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(title="AI Study Assistant API", middleware=middleware)

# Setup rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error handling request: {exc}")
    origin = request.headers.get("origin")
    headers = {}
    if origin and (origin in settings.CORS_ORIGINS or any(origin.startswith(o) for o in ["http://localhost", "http://127.0.0.1"])):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers=headers,
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])

@app.get("/health")
async def health_check():
    try:
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
