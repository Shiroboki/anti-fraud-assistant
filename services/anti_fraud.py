"""
反诈助手服务
提供反诈问答、诈骗检测等AI能力
"""
import os
import sys
import json
import time
from typing import Optional, List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

# 反诈专家系统提示词
ANTI_FRAUD_SYSTEM_PROMPT = """你是一名专业的反诈骗智能助手，隶属于国家反诈中心AI系统。你的职责是：

1. **识别诈骗**：帮助用户识别各种类型的诈骗手段，包括但不限于：刷单诈骗、冒充公检法、杀猪盘、贷款诈骗、网购退款诈骗、投资理财诈骗、游戏交易诈骗等。
2. **分析风险**：当用户描述可疑情况时，分析其中的诈骗特征，给出风险评估。
3. **提供防范建议**：针对不同诈骗类型，给出具体的防范措施和应对建议。
4. **普及反诈知识**：用通俗易懂的语言普及反诈知识，提高用户的防骗意识。

回复要求：
- 语言亲切、通俗易懂，适合普通群众理解
- 如果判断可能是诈骗，明确提醒用户风险等级（低/中/高/极高）
- 给出具体的"三不"建议：不轻信、不透露、不转账
- 必要时建议用户拨打96110反诈专线或110报警
- 回复控制在300字以内，重点突出"""

# 诈骗检测提示词
DETECTION_PROMPT = """你是一名反诈骗分析专家。请分析以下内容是否存在诈骗风险。

请严格按照以下JSON格式返回结果：
{
    "risk_level": "safe/low/medium/high/critical",
    "fraud_type": "phishing/investment/impersonation/romance/shopping/part_time/loan/gaming/other/null",
    "confidence": 0.0到1.0之间的浮点数,
    "analysis": "详细分析说明",
    "suggestions": ["防范建议1", "防范建议2"]
}

诈骗特征参考：
- 要求转账到"安全账户"
- 索要银行卡号、密码、验证码
- 声称中奖、退款需要先缴费
- 高回报低风险的投资承诺
- 冒充公检法要求配合调查
- 网恋后引导投资/博彩
- 刷单返利
- 贷款前收取手续费/保证金"""


class AntiFraudService:
    """反诈助手服务"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _init_llm(self):
        """初始化LLM"""
        import time as _time
        now = _time.time()
        if not hasattr(self, "_config_cache") or now - getattr(self, "_config_cache_time", 0) > 60:
            self._config_cache = self._load_runtime_config()
            self._config_cache_time = now
            self._llm = None

        cfg = self._config_cache
        if not hasattr(self, "_llm") or self._llm is None:
            if cfg["chat_provider"] == "ollama":
                from langchain_ollama import ChatOllama
                self._llm = ChatOllama(
                    model=cfg["chat_model_ollama"],
                    base_url=cfg["ollama_url"],
                    temperature=0.7,
                )
            elif cfg["chat_provider"] == "openai_compatible":
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model=cfg["chat_model_openai"],
                    api_key=cfg["openai_api_key"],
                    base_url=cfg["openai_base_url"],
                    temperature=0.7,
                )
            else:
                from langchain_community.chat_models import ChatTongyi
                self._llm = ChatTongyi(
                    model=cfg["chat_model_cloud"],
                    dashscope_api_key=cfg["dashscope_api_key"],
                    temperature=0.7,
                )
        return self._llm

    def _load_runtime_config(self) -> dict:
        try:
            from models import SessionLocal
            from models.system_setting import SystemSetting
            db = SessionLocal()
            try:
                settings = {s.key: s.value for s in db.query(SystemSetting).all()}
                return {
                    "chat_provider": settings.get("chat_provider", config.CHAT_PROVIDER),
                    "chat_model_cloud": settings.get("chat_model_cloud", config.CHAT_MODEL_CLOUD),
                    "chat_model_ollama": settings.get("chat_model_ollama", config.CHAT_MODEL_OLLAMA),
                    "ollama_url": settings.get("ollama_url", config.OLLAMA_URL),
                    "dashscope_api_key": settings.get("dashscope_api_key", config.DASHSCOPE_API_KEY),
                    "openai_api_key": settings.get("openai_api_key", config.OPENAI_API_KEY),
                    "openai_base_url": settings.get("openai_base_url", config.OPENAI_BASE_URL),
                    "chat_model_openai": settings.get("chat_model_openai", config.CHAT_MODEL_OPENAI),
                }
            finally:
                db.close()
        except Exception:
            return {
                "chat_provider": config.CHAT_PROVIDER,
                "chat_model_cloud": config.CHAT_MODEL_CLOUD,
                "chat_model_ollama": config.CHAT_MODEL_OLLAMA,
                "ollama_url": config.OLLAMA_URL,
                "dashscope_api_key": config.DASHSCOPE_API_KEY,
                "openai_api_key": config.OPENAI_API_KEY,
                "openai_base_url": config.OPENAI_BASE_URL,
                "chat_model_openai": config.CHAT_MODEL_OPENAI,
            }

    def chat(self, user_message: str, history: List[Dict[str, str]] = None) -> str:
        """反诈问答"""
        llm = self._init_llm()
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        messages = [SystemMessage(content=ANTI_FRAUD_SYSTEM_PROMPT)]
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=user_message))

        response = llm.invoke(messages)
        return response.content

    def detect_fraud(self, text: str) -> dict:
        """诈骗检测分析"""
        llm = self._init_llm()
        from langchain_core.messages import SystemMessage, HumanMessage

        messages = [
            SystemMessage(content=DETECTION_PROMPT),
            HumanMessage(content=f"请分析以下内容是否存在诈骗风险：\n\n{text}"),
        ]

        response = llm.invoke(messages)
        content = response.content

        # 尝试解析JSON
        try:
            # 提取JSON部分
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            result = json.loads(content)
            return result
        except (json.JSONDecodeError, IndexError):
            return {
                "risk_level": "medium",
                "fraud_type": "other",
                "confidence": 0.5,
                "analysis": content,
                "suggestions": ["建议拨打96110反诈专线咨询", "不要轻易转账汇款"],
            }

    def load_knowledge_cases(self) -> List[dict]:
        """从knowledges目录加载反诈案例数据"""
        cases = []
        cases_dir = os.path.join(os.path.dirname(__file__), "..", "knowledges", "网络爬取的反诈案例")
        if not os.path.exists(cases_dir):
            return cases
        for filename in os.listdir(cases_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(cases_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                source = data.get("website_name", filename)
                for item in data.get("source_data", []):
                    cases.append({
                        "title": item.get("title", ""),
                        "content": item.get("content", "")[:2000],
                        "source": source,
                    })
            except Exception:
                continue
        return cases


anti_fraud_service = AntiFraudService()
