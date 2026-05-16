"""
用户表模型
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from models import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    TEACHER = "teacher"  # 保留以兼容旧数据，前端已不使用
    STUDENT = "student"


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(128), unique=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(256), nullable=False, comment="密码哈希")
    real_name = Column(String(64), nullable=True, comment="真实姓名")
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False, comment="角色")
    school_id = Column(String(64), nullable=True, comment="学校ID")
    avatar = Column(String(256), nullable=True, comment="头像URL")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_deleted = Column(Boolean, default=False, comment="是否软删除")
    email_verified = Column(Boolean, default=False, comment="邮箱是否已验证")
    verification_token = Column(String(128), nullable=True, comment="邮箱验证令牌")
    reset_token = Column(String(128), nullable=True, comment="密码重置令牌")
    reset_token_expires = Column(DateTime, nullable=True, comment="重置令牌过期时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关系（与角色表多对多）
    roles = relationship("Role", secondary="user_roles", back_populates="users")

    def to_dict(self, include_sensitive=False):
        result = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "realName": self.real_name,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "schoolId": self.school_id,
            "avatar": self.avatar,
            "isActive": self.is_active,
            "isDeleted": self.is_deleted,
            "emailVerified": self.email_verified,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
        return result
