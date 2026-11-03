from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database import Base, SessionLocal, engine
from app.routes import assistant, emails
from app.services import state


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        state.seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(assistant.router)
app.include_router(emails.router)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    msgs = [f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "; ".join(msgs) or "Invalid request"})


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    # Error responses bypass CORS middleware, so add the header here or browsers report a misleading CORS error.
    origin = request.headers.get("origin", "")
    headers = {"Access-Control-Allow-Origin": origin} if origin in settings.cors_origins else {}
    return JSONResponse(status_code=500, content={"detail": f"Server error: {type(exc).__name__}"}, headers=headers)


@app.get("/")
def root():
    return {"name": settings.app_name, "docs": "/docs", "health": "/api/health"}
