"""
AI模拟面试与能力提升平台 - 统一配置
"""

import os


# 模型配置
_chat_provider = os.environ.get("CHAT_PROVIDER", "tongyi")
CHAT_PROVIDER = _chat_provider
CHAT_MODEL_OLLAMA = "qwen3.5:9b"
CHAT_MODEL_CLOUD = "qwen-max"
OLLAMA_URL = "http://localhost:11434"


# JWT 配置（持久化密钥文件，重启不丢失）
_JWT_SECRET_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", ".jwt_secret"
)

if os.path.exists(_JWT_SECRET_FILE):
    with open(_JWT_SECRET_FILE, "r") as _f:
        JWT_SECRET_KEY = _f.read().strip()
elif (
    os.environ.get("JWT_SECRET_KEY") and len(os.environ.get("JWT_SECRET_KEY", "")) >= 16
):
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
else:
    import uuid as _uuid

    JWT_SECRET_KEY = _uuid.uuid4().hex
    os.makedirs(os.path.dirname(_JWT_SECRET_FILE), exist_ok=True)
    with open(_JWT_SECRET_FILE, "w") as _f:
        _f.write(JWT_SECRET_KEY)

JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
)


# API 签名配置
API_STATIC_KEY = os.environ.get("API_STATIC_KEY", "")
API_TIME_WINDOW = int(os.environ.get("API_TIME_WINDOW", "300"))
API_SIGNATURE_ENABLED = (
    os.environ.get("API_SIGNATURE_ENABLED", "false").lower() == "true"
)

# API 限流配置
RATE_LIMIT_ENABLED = (
    os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
)
RATE_LIMIT_DEFAULT = int(os.environ.get("RATE_LIMIT_DEFAULT", "100"))
RATE_LIMIT_AUTH = int(os.environ.get("RATE_LIMIT_AUTH", "30"))


# 数据库配置（MySQL）
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DB = os.environ.get("MYSQL_DB", "anti_fraud")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4",
)

OSS_ACCESS_KEY_ID = os.environ.get("OSS_ACCESS_KEY_ID", "")
OSS_ACCESS_KEY_SECRET = os.environ.get("OSS_ACCESS_KEY_SECRET", "")
OSS_BUCKET_NAME = os.environ.get("OSS_BUCKET_NAME", "ai-course0411")
OSS_ENDPOINT = os.environ.get("OSS_ENDPOINT", "https://oss-cn-beijing.aliyuncs.com")
OSS_BASE_URL = os.environ.get(
    "OSS_BASE_URL", "https://ai-course0411.oss-cn-beijing.aliyuncs.com"
)


# API Keys
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
CHAT_MODEL_OPENAI = os.environ.get("CHAT_MODEL_OPENAI", "gpt-4o-mini")

# LiveTalking 数字人服务配置
LIVE_TALKING_URL = os.environ.get("LIVE_TALKING_URL", "http://127.0.0.1:8010")

# SMTP 邮件配置
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "")
SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "true").lower() == "true"
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "false").lower() == "true"

# 前端地址（用于邮件中的链接）
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


# ========== 面试系统配置 ==========

# 面试系统名称
INTERVIEW_SYSTEM_NAME = os.environ.get(
    "INTERVIEW_SYSTEM_NAME", "多模态智能反诈助手"
)

# 默认面试时长（分钟）
INTERVIEW_DEFAULT_TIME_LIMIT = int(os.environ.get("INTERVIEW_DEFAULT_TIME_LIMIT", "30"))

# 每场面试默认题目数量
INTERVIEW_DEFAULT_QUESTION_COUNT = int(
    os.environ.get("INTERVIEW_DEFAULT_QUESTION_COUNT", "5")
)

# 面试题目库路径
INTERVIEW_QUESTION_BANK_PATH = os.environ.get(
    "INTERVIEW_QUESTION_BANK_PATH", "./data/interview_questions"
)

# 面试报告存储路径
INTERVIEW_REPORT_PATH = os.environ.get(
    "INTERVIEW_REPORT_PATH", "./data/interview_reports"
)

# 是否启用数字人面试官（默认关闭）
INTERVIEW_DIGITAL_HUMAN_ENABLED = (
    os.environ.get("INTERVIEW_DIGITAL_HUMAN_ENABLED", "false").lower() == "true"
)

# 面试评估配置
INTERVIEW_SCORE_THRESHOLD = 70  # 及格分数线
INTERVIEW_EXCELLENT_THRESHOLD = 85  # 优秀分数线

# Celery 配置
CELERY_ENABLED = os.environ.get("CELERY_ENABLED", "false").lower() == "true"
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
