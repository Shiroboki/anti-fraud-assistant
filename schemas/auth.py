"""
认证相关 Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """用户注册请求"""
    username: str = Field(min_length=3, max_length=64, description="用户名")
    email: str = Field(description="邮箱")
    password: str = Field(min_length=6, max_length=128, description="密码")
    realName: Optional[str] = Field(default=None, description="真实姓名")
    role: str = Field(default="student", description="角色：admin/teacher/student")
    schoolId: Optional[str] = Field(default=None, description="学校ID")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(description="用户名")
    password: str = Field(description="密码")


class Token(BaseModel):
    """JWT Token响应"""
    accessToken: str = Field(description="访问令牌")
    tokenType: str = Field(default="bearer", description="令牌类型")
    expiresIn: int = Field(description="过期时间（秒）")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱")
    realName: Optional[str] = Field(default=None, description="真实姓名")
    role: str = Field(description="角色")
    schoolId: Optional[str] = Field(default=None, description="学校ID")
    isActive: bool = Field(description="是否启用")


class RoleResponse(BaseModel):
    """角色信息响应"""
    id: int = Field(description="角色ID")
    name: str = Field(description="角色名")
    description: Optional[str] = Field(default=None, description="角色描述")
    permissions: List[dict] = Field(default=[], description="权限列表")


class PermissionResponse(BaseModel):
    """权限信息响应"""
    id: int = Field(description="权限ID")
    name: str = Field(description="权限标识")
    description: Optional[str] = Field(default=None, description="权限描述")
    resource: str = Field(description="资源类型")
    action: str = Field(description="操作类型")
