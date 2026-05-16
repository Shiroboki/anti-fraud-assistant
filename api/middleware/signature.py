"""
签名验证中间件
按照API设计规范实现MD5签名验证
"""
import hashlib
import time
from datetime import datetime
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SignatureMiddleware(BaseHTTPMiddleware):
    """MD5签名验证中间件"""

    def __init__(self, app, static_key: str, time_window: int = 300):
        super().__init__(app)
        self.static_key = static_key
        self.time_window = time_window

    async def dispatch(self, request: Request, call_next):
        # 跳过无需验证的接口
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths:
            return await call_next(request)

        # 获取查询参数
        params = dict(request.query_params)
        enc = params.pop("enc", None)
        time_str = params.get("time")

        # 检查签名参数
        if not enc:
            return JSONResponse(
                status_code=403,
                content={"code": 403, "msg": "缺少签名参数 enc", "data": None}
            )

        if not time_str:
            return JSONResponse(
                status_code=403,
                content={"code": 403, "msg": "缺少时间参数 time", "data": None}
            )

        # 验证时间窗口
        try:
            req_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            diff = abs((now - req_time).total_seconds())
            if diff > self.time_window:
                return JSONResponse(
                    status_code=403,
                    content={"code": 403, "msg": "请求已过期", "data": None}
                )
        except ValueError:
            return JSONResponse(
                status_code=403,
                content={"code": 403, "msg": "时间格式错误，应为 yyyy-MM-dd HH:mm:ss", "data": None}
            )

        # 计算签名
        # 按参数名ASCII升序排列所有非空请求参数
        sorted_params = "".join(
            f"{k}{v}" for k, v in sorted(params.items()) if v
        )
        sign_str = f"{sorted_params}{self.static_key}{time_str}"
        expected_enc = hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

        if enc.upper() != expected_enc.upper():
            return JSONResponse(
                status_code=403,
                content={"code": 403, "msg": "签名验证失败", "data": None}
            )

        return await call_next(request)
