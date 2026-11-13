from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.ml import router as ml_router
from app.core.config import settings
from app.database import Base, SessionLocal, engine, init_db
from app.routes import assistant, emails
from app.services import state

logger = logging.getLogger("mailmind.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    try:
        init_db()
        db = SessionLocal()
        try:
            state.seed(db)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Startup initialization warning: {e}")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex or r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include All Routers
app.include_router(assistant.router)
app.include_router(emails.router)
app.include_router(ml_router)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    msgs = [f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "; ".join(msgs) or "Invalid request"})


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    origin = request.headers.get("origin", "")
    headers = {"Access-Control-Allow-Origin": origin} if origin else {}
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {type(exc).__name__}: {str(exc)}"},
        headers=headers
    )


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health",
        "status": "online"
    }
