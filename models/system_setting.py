"""
系统设置模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from models import Base


class SystemSetting(Base):
    """系统设置（键值对）"""
    __tablename__ = "system_setting"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(128), unique=True, nullable=False, index=True, comment="配置键")
    value = Column(Text, nullable=True, comment="配置值")
    description = Column(String(256), nullable=True, comment="说明")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updatedAt": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
