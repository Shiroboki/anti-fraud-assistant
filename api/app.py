"""
FastAPI 应用入口
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

from schemas.common import ApiResponse
from api.middleware.signature import SignatureMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from api.v1 import auth, settings
from api.v1 import anti_fraud_chat, anti_fraud_detect, anti_fraud_case

logger = logging.getLogger(__name__)


class BadRequestError(HTTPException):
    def __init__(self, detail: str = "请求参数无效"):
        super().__init__(status_code=400, detail=detail)


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "认证失败"):
        super().__init__(status_code=401, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=403, detail=detail)


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(status_code=404, detail=detail)


class ServiceUnavailableError(HTTPException):
    def __init__(self, detail: str = "服务暂时不可用"):
        super().__init__(status_code=503, detail=detail)


if not config.JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY 未设置，请检查 config.py")

from models import init_db
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("多模态智能反诈助手 API 服务启动")
    logger.info("=" * 50)
    yield
    logger.info("多模态智能反诈助手 API 服务关闭")


app = FastAPI(
    title="多模态智能反诈助手 API",
    description="多模态智能反诈助手 - AI反诈问答、诈骗检测、案例学习",
    version="1.0.0",
    lifespan=lifespan,
)

_allowed_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

if config.API_SIGNATURE_ENABLED:
    app.add_middleware(
        SignatureMiddleware,
        static_key=config.API_STATIC_KEY,
        time_window=config.API_TIME_WINDOW,
    )

if config.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        default_limit=config.RATE_LIMIT_DEFAULT,
        default_window=60,
        path_limits={
            "/api/v1/auth/login": (config.RATE_LIMIT_AUTH, 60),
            "/api/v1/auth/register": (config.RATE_LIMIT_AUTH, 60),
            "/api/v1/auth/forgot-password": (config.RATE_LIMIT_AUTH, 60),
        },
    )

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证模块"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["系统设置"])
app.include_router(anti_fraud_chat.router, prefix="/api/v1/af/chat", tags=["反诈问答"])
app.include_router(anti_fraud_detect.router, prefix="/api/v1/af/detect", tags=["诈骗检测"])
app.include_router(anti_fraud_case.router, prefix="/api/v1/af/case", tags=["反诈案例"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (BadRequestError, UnauthorizedError, ForbiddenError,
                        NotFoundError, ServiceUnavailableError)):
        status_code = exc.status_code
        message = str(exc.detail)
    elif isinstance(exc, HTTPException):
        status_code = exc.status_code
        message = str(exc.detail)
    elif "not found" in str(exc).lower() or "不存在" in str(exc):
        status_code = 404
        message = str(exc)
    elif "unauthorized" in str(exc).lower() or "未授权" in str(exc) or "认证" in str(exc):
        status_code = 401
        message = "认证失败，请检查登录状态"
    elif "permission" in str(exc).lower() or "权限" in str(exc) or "禁止" in str(exc):
        status_code = 403
        message = "权限不足"
    elif "timeout" in str(exc).lower() or "超时" in str(exc):
        status_code = 504
        message = "请求超时，请稍后重试"
    else:
        status_code = 500
        message = f"服务器内部错误: {str(exc)}"
        logger.error(f"未处理异常: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status_code,
        content=ApiResponse.error(status_code, message).model_dump(),
    )


@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "service": "多模态智能反诈助手 API"}


AUDIO_CACHE_DIR = os.path.abspath("./data/audio_cache")


@app.get("/api/v1/audio/{filename}", tags=["音频"])
async def serve_audio(filename: str):
    safe_name = os.path.basename(filename)
    file_path = os.path.join(AUDIO_CACHE_DIR, safe_name)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"code": 404, "msg": "音频文件不存在"})
    with open(file_path, 'rb') as f:
        header = f.read(12)
    if header[0:3] == b'ID3' or header[0:4] == b'MPEG':
        media_type = "audio/mpeg"
    elif header[0:4] == b'RIFF' and b'WAVE' in header:
        media_type = "audio/wav"
    elif header[0:4] == b'OggS':
        media_type = "audio/ogg"
    elif header[0:4] == b'fLaC':
        media_type = "audio/flac"
    elif header[0:4] == b'\xff\xfb':
        media_type = "audio/mpeg"
    else:
        media_type = "audio/mpeg" if file_path.endswith(".mp3") else "audio/wav"
    return FileResponse(file_path, media_type=media_type)
