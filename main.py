from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.middleware.rate_limit import limiter
from app.routers import analytics, auth, calls, companies, contacts, emails, health, leads, meetings, telegram
from app.services.scheduler import start_scheduler, stop_scheduler
from app.utils.logging import setup_logging, get_logger

settings = get_settings()
setup_logging(settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", env=settings.app_env)
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("app_shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Production-ready AI Sales Assistant CRM",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


api_prefix = settings.api_prefix
app.include_router(auth.router, prefix=api_prefix)
app.include_router(companies.router, prefix=api_prefix)
app.include_router(contacts.router, prefix=api_prefix)
app.include_router(leads.router, prefix=api_prefix)
app.include_router(emails.router, prefix=api_prefix)
app.include_router(meetings.router, prefix=api_prefix)
app.include_router(analytics.router, prefix=api_prefix)
app.include_router(calls.router, prefix=api_prefix)
app.include_router(telegram.router, prefix=api_prefix)
app.include_router(health.router, prefix=api_prefix)


@app.get("/")
def root():
    return {"message": settings.app_name, "docs": "/docs", "health": f"{api_prefix}/health"}
