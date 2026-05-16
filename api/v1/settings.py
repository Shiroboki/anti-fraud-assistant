"""
系统设置 API - 管理员配置LLM等参数
"""
import json
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import get_db
from models.user import User, UserRole
from models.system_setting import SystemSetting
from api.deps import get_current_user
from schemas.common import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# 需要 admin 权限的设置项（这些值不能泄露给普通用户）
SENSITIVE_KEYS = {"dashscope_api_key", "mimo_api_key", "openai_api_key", "smtp_password"}


def _is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


def _get_setting(db: Session, key: str):
    return db.query(SystemSetting).filter(SystemSetting.key == key).first()


def _set_setting(db: Session, key: str, value: str, description: str = None):
    s = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if s:
        s.value = value
        if description:
            s.description = description
    else:
        s = SystemSetting(key=key, value=value, description=description)
        db.add(s)
    db.commit()
    return s


# 预设的默认配置项
DEFAULT_SETTINGS = [
    {"key": "chat_provider", "value": "tongyi", "description": "LLM服务提供商: tongyi / openai_compatible / ollama"},
    {"key": "chat_model_cloud", "value": "qwen-max", "description": "云端模型名称"},
    {"key": "chat_model_ollama", "value": "qwen3.5:9b", "description": "Ollama模型名称"},
    {"key": "ollama_url", "value": "http://localhost:11434", "description": "Ollama服务地址"},
    {"key": "dashscope_api_key", "value": "", "description": "通义千问API Key"},
    {"key": "openai_api_key", "value": "", "description": "OpenAI兼容API Key"},
    {"key": "openai_base_url", "value": "https://api.openai.com/v1", "description": "OpenAI兼容Base URL"},
    {"key": "chat_model_openai", "value": "gpt-4o-mini", "description": "OpenAI兼容模型名称"},
    {"key": "llm_max_concurrent", "value": "5", "description": "LLM最大并发数"},
    {"key": "system_name", "value": "AI模拟面试与能力提升平台", "description": "系统名称"},
    {"key": "interview_default_time_limit", "value": "30", "description": "默认面试时长（分钟）"},
    {"key": "interview_default_question_count", "value": "5", "description": "默认题目数量"},
    {"key": "digital_human_enabled", "value": "false", "description": "是否启用数字人"},
]


def _init_default_settings(db: Session):
    """初始化默认配置（补充缺失的配置项）"""
    existing = {s.key for s in db.query(SystemSetting.key).all()}
    added = False
    for s in DEFAULT_SETTINGS:
        if s["key"] not in existing:
            db.add(SystemSetting(key=s["key"], value=s["value"], description=s["description"]))
            added = True
    if added:
        db.commit()


@router.get("/list")
async def list_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有设置（敏感字段值隐藏）"""
    _init_default_settings(db)
    settings = db.query(SystemSetting).order_by(SystemSetting.id).all()
    result = []
    for s in settings:
        item = s.to_dict()
        if s.key in SENSITIVE_KEYS and item["value"]:
            item["value"] = "******"  # 脱敏
        result.append(item)
    return ApiResponse.success(data=result)


@router.get("/{key}")
async def get_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个设置"""
    s = _get_setting(db, key)
    if not s:
        return ApiResponse.error(404, f"配置项 {key} 不存在")
    result = s.to_dict()
    if key in SENSITIVE_KEYS and result["value"]:
        result["value"] = "******"
    return ApiResponse.success(data=result)


@router.put("/{key}")
async def update_setting(
    key: str,
    value: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新单个设置（仅管理员）"""
    if not _is_admin(current_user):
        return ApiResponse.error(403, "仅管理员可修改系统设置")

    s = _set_setting(db, key, value)
    return ApiResponse.success(data=s.to_dict(), msg="设置已更新")


@router.post("/batch")
async def batch_update_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量更新设置（仅管理员）"""
    if not _is_admin(current_user):
        return ApiResponse.error(403, "仅管理员可修改系统设置")

    updated = []
    for key, value in settings.items():
        # 跳过敏感key的批量写入（防止误传真实key）
        if key not in SENSITIVE_KEYS:
            s = _set_setting(db, key, str(value))
            updated.append(key)

    return ApiResponse.success(data={"updated": updated}, msg=f"已更新 {len(updated)} 项设置")


@router.post("/init")
async def init_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """初始化/重置默认设置（仅管理员）"""
    if not _is_admin(current_user):
        return ApiResponse.error(403, "仅管理员可修改系统设置")

    for s in DEFAULT_SETTINGS:
        _set_setting(db, s["key"], s["value"], s["description"])

    return ApiResponse.success(msg="默认设置已初始化")


@router.post("/test-llm")
async def test_llm_connection(
    config_data: dict,
    current_user: User = Depends(get_current_user),
):
    """测试LLM连接（仅管理员）"""
    if not _is_admin(current_user):
        return ApiResponse.error(403, "仅管理员可操作")

    provider = config_data.get("chat_provider", "tongyi")
    test_prompt = "请用一句话介绍你自己。"

    try:
        if provider == "ollama":
            from langchain_ollama import ChatOllama
            llm = ChatOllama(
                model=config_data.get("chat_model_ollama", "qwen3.5:9b"),
                base_url=config_data.get("ollama_url", "http://localhost:11434"),
                temperature=0.7,
            )
        elif provider == "openai_compatible":
            from langchain_openai import ChatOpenAI
            api_key = config_data.get("openai_api_key", "")
            if not api_key:
                return ApiResponse.error(400, "请先填写 API Key")
            llm = ChatOpenAI(
                model=config_data.get("chat_model_openai", "gpt-4o-mini"),
                api_key=api_key,
                base_url=config_data.get("openai_base_url", "https://api.openai.com/v1"),
                temperature=0.7,
            )
        else:  # tongyi
            from langchain_community.chat_models import ChatTongyi
            api_key = config_data.get("dashscope_api_key", "")
            if not api_key:
                return ApiResponse.error(400, "请先填写 API Key")
            llm = ChatTongyi(
                model=config_data.get("chat_model_cloud", "qwen-max"),
                dashscope_api_key=api_key,
                temperature=0.7,
            )

        from langchain_core.messages import HumanMessage
        result = llm.invoke([HumanMessage(content=test_prompt)])
        reply = result.content if hasattr(result, "content") else str(result)
        return ApiResponse.success(data={"reply": reply[:200]}, msg="连接成功")

    except Exception as e:
        logger.error(f"LLM连接测试失败: {e}")
        return ApiResponse.error(500, f"连接失败: {str(e)[:200]}")
