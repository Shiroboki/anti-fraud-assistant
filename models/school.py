"""
学校模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from datetime import datetime
from models import Base


class School(Base):
    """学校模型"""
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(String(64), unique=True, nullable=False, comment="学校ID")
    school_name = Column(String(128), nullable=False, comment="学校名称")
    school_code = Column(String(32), comment="学校代码")
    contact_person = Column(String(64), comment="联系人")
    contact_phone = Column(String(32), comment="联系电话")
    contact_email = Column(String(128), comment="联系邮箱")
    address = Column(String(256), comment="学校地址")
    status = Column(Boolean, default=True, comment="启用状态")
    config = Column(JSON, comment="学校配置")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "schoolId": self.school_id,
            "schoolName": self.school_name,
            "schoolCode": self.school_code,
            "contactPerson": self.contact_person,
            "contactPhone": self.contact_phone,
            "contactEmail": self.contact_email,
            "address": self.address,
            "status": self.status,
            "config": self.config,
            "createdAt": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updatedAt": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
