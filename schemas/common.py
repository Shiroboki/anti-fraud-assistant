"""
通用响应模型
"""
import uuid
from datetime import datetime
from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int = Field(default=200, description="状态码：200成功，4xx客户端错误，5xx服务端错误")
    msg: str = Field(default="操作成功", description="状态描述")
    data: Optional[T] = Field(default=None, description="业务数据")
    requestId: str = Field(
        default_factory=lambda: f"req{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}",
        description="请求唯一标识"
    )

    @classmethod
    def success(cls, data: Any = None, msg: str = "操作成功") -> "ApiResponse":
        """成功响应"""
        return cls(code=200, msg=msg, data=data)

    @classmethod
    def error(cls, code: int, msg: str) -> "ApiResponse":
        """错误响应"""
        return cls(code=code, msg=msg, data=None)


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=20, ge=1, le=100, description="每页数量")


class FileInfo(BaseModel):
    """文件信息"""
    fileName: str = Field(description="文件名")
    fileSize: int = Field(description="文件大小（字节）")
    pageCount: int = Field(description="页数")


class TaskStatus(BaseModel):
    """任务状态"""
    taskId: str = Field(description="任务ID")
    status: str = Field(description="状态：pending/processing/completed/failed")
    createdAt: str = Field(description="创建时间")
    completedAt: Optional[str] = Field(default=None, description="完成时间")
    error: Optional[str] = Field(default=None, description="错误信息")
