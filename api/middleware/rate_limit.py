"""
基于内存的 API 限流中间件
"""
import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from schemas.common import ApiResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于滑动窗口的 IP 限流中间件"""

    def __init__(self, app, default_limit: int = 100, default_window: int = 60,
                 path_limits: dict = None):
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        # {ip: [(timestamp, path), ...]}
        self.requests: dict[str, list] = defaultdict(list)
        # 特殊路径限流配置: {path_prefix: (limit, window)}
        self.path_limits: dict[str, tuple[int, int]] = path_limits or {}

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup_old_entries(self, ip: str, window: int):
        now = time.time()
        self.requests[ip] = [
            (ts, path) for ts, path in self.requests[ip]
            if now - ts < window
        ]

    async def dispatch(self, request: Request, call_next):
        # 健康检查和 OPTIONS 预检请求不限流
        if request.url.path == "/health" or request.method == "OPTIONS":
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()
        path = request.url.path

        # 确定限流参数和匹配前缀
        limit = self.default_limit
        window = self.default_window
        matched_prefix = None
        for prefix, (l, w) in self.path_limits.items():
            if path.startswith(prefix):
                limit, window = l, w
                matched_prefix = prefix
                break

        # 清理过期记录
        self._cleanup_old_entries(client_ip, window)

        # 按匹配前缀统计请求数（有特殊限流的路径只统计同前缀请求）
        if matched_prefix:
            count = sum(1 for _, p in self.requests[client_ip] if p.startswith(matched_prefix))
        else:
            count = len(self.requests[client_ip])

        # 检查是否超限
        if count >= limit:
            return JSONResponse(
                status_code=429,
                content=ApiResponse.error(429, "请求过于频繁，请稍后重试").model_dump(),
            )

        # 记录请求
        self.requests[client_ip].append((now, path))

        return await call_next(request)
