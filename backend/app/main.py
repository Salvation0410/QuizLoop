from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.errors import BusinessError
from app.db.session import build_engine, build_session_factory
from app.llm.provider import build_provider


def create_app() -> FastAPI:
    settings = get_settings()
    engine = build_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        engine.dispose()

    app = FastAPI(title="Quizeloop API", version="0.1.0", lifespan=lifespan)
    app.state.session_factory = build_session_factory(engine)
    app.state.provider = build_provider(settings)
    app.add_middleware(CORSMiddleware, allow_origins=[item.strip() for item in settings.cors_origins.split(",")], allow_methods=["*"], allow_headers=["*"])

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-Id", f"req_{uuid4().hex}")
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        return response

    @app.exception_handler(BusinessError)
    async def business_error(request: Request, exc: BusinessError):
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message, "data": None, "request_id": request.state.request_id})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"code": 4220, "message": "请求参数不合法", "data": {"errors": exc.errors()}, "request_id": request.state.request_id})

    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
