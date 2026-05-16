"""
反诈助手 - 数据库模型
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from models import Base


class FraudType(str, enum.Enum):
    """诈骗类型枚举"""
    PHISHING = "phishing"           # 钓鱼诈骗
    INVESTMENT = "investment"       # 投资理财诈骗
    IMPERSONATION = "impersonation" # 冒充公检法
    ROMANCE = "romance"             # 杀猪盘/网恋诈骗
    SHOPPING = "shopping"           # 网购退款诈骗
    PART_TIME = "part_time"         # 刷单兼职诈骗
    LOAN = "loan"                   # 贷款诈骗
    GAMING = "gaming"               # 游戏交易诈骗
    OTHER = "other"                 # 其他


class RiskLevel(str, enum.Enum):
    """风险等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionType(str, enum.Enum):
    """检测类型"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"


class ChatSession(Base):
    """反诈问答会话"""
    __tablename__ = "af_chat_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(128), default="反诈咨询", comment="会话标题")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """对话消息"""
    __tablename__ = "af_chat_message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("af_chat_session.id"), nullable=False, index=True)
    role = Column(String(16), nullable=False, comment="user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    content_type = Column(String(16), default="text", comment="text/image/voice")
    extra_data = Column(JSON, nullable=True, comment="附加数据")
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("ChatSession", back_populates="messages")


class FraudCase(Base):
    """反诈案例"""
    __tablename__ = "af_fraud_case"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False, comment="案例标题")
    content = Column(Text, nullable=False, comment="案例内容")
    fraud_type = Column(Enum(FraudType), default=FraudType.OTHER, comment="诈骗类型")
    source = Column(String(128), nullable=True, comment="来源")
    tags = Column(String(256), nullable=True, comment="标签，逗号分隔")
    is_published = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class DetectionRecord(Base):
    """诈骗检测记录"""
    __tablename__ = "af_detection_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    detection_type = Column(Enum(DetectionType), nullable=False, comment="检测类型")
    input_content = Column(Text, nullable=True, comment="输入文本/描述")
    input_file_url = Column(String(512), nullable=True, comment="上传文件URL")
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.SAFE, comment="风险等级")
    fraud_type = Column(Enum(FraudType), nullable=True, comment="识别的诈骗类型")
    analysis_result = Column(Text, nullable=True, comment="AI分析结果")
    confidence = Column(Float, default=0.0, comment="置信度0-1")
    suggestions = Column(Text, nullable=True, comment="防范建议")
    created_at = Column(DateTime, default=datetime.now)
