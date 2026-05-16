"""
角色表和权限表模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from models import Base


# 用户-角色关联表（多对多）
user_roles = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)

# 角色-权限关联表（多对多）
role_permissions = Table(
    'role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    mysql_engine='InnoDB',
    mysql_charset='utf8mb4'
)


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False, comment="角色名：admin/teacher/student")
    description = Column(String(256), nullable=True, comment="角色描述")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": [p.to_dict() for p in self.permissions],
        }


class Permission(Base):
    """权限表"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False, comment="权限标识：resource:action")
    description = Column(String(256), nullable=True, comment="权限描述")
    resource = Column(String(64), nullable=False, comment="资源类型：course/progress/qa/lesson/user")
    action = Column(String(32), nullable=False, comment="操作：create/read/update/delete")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resource": self.resource,
            "action": self.action,
        }
