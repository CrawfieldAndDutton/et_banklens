import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.database import Base, apply_sqlite_migrations, engine
from app.limiter import limiter
from app.routers import audit, auth, bsi, customers, dashboard, health, omnichannel, signals
from app.seed import run_seed

logger = logging.getLogger("banklens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    apply_sqlite_migrations()
    run_seed(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="BankLens API (hackathon)",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    if settings.is_production:
        application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            return response

    application.add_middleware(SecurityHeadersMiddleware)

    @application.middleware("http")
    async def generic_error_sanitizer(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled error")
            if settings.is_production:
                return JSONResponse(status_code=500, content={"detail": "Internal server error"})
            raise

    application.include_router(health.router, prefix="/api/v1")
    application.include_router(auth.router, prefix="/api/v1")
    application.include_router(dashboard.router, prefix="/api/v1")
    application.include_router(customers.router, prefix="/api/v1")
    application.include_router(bsi.router, prefix="/api/v1")
    application.include_router(signals.router, prefix="/api/v1")
    application.include_router(audit.router, prefix="/api/v1")
    application.include_router(omnichannel.router, prefix="/api/v1")

    @application.get("/")
    def root():
        return {
            "message": "BankLens hackathon backend: BSI, signals, omnichannel (WhatsApp/email), audit, optional OpenAI.",
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    return application


app = create_app()
