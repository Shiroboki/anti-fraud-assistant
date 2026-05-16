"""
语音合成 (TTS) 服务
支持 LaTeX 公式转语音、SSML 场景化语音
"""
import os
import sys
import re
import hashlib
import json
from typing import Optional, List, Dict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


class TTSService:
    """语音合成服务类"""

    _instance = None
    _cache_dir = "./data/audio_cache"

    # 场景化语音配置（edge-tts 支持 rate/pitch 调节）
    SCENE_VOICES = {
        "opening": {"voice": "zh-CN-YunjianNeural", "rate": "+10%", "pitch": "+5Hz"},
        "knowledge": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "-5%", "pitch": "+0Hz"},
        "example": {"voice": "zh-CN-XiaoyiNeural", "rate": "+0%", "pitch": "+2Hz"},
        "summary": {"voice": "zh-CN-YunxiNeural", "rate": "+5%", "pitch": "+0Hz"},
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _init_components(self):
        """初始化组件"""
        if self._initialized:
            return
        
        # 创建音频缓存目录
        os.makedirs(self._cache_dir, exist_ok=True)
        self._initialized = True

    def _get_cache_key(self, text: str, voice_type: str, audio_format: str) -> str:
        """生成缓存键"""
        content = f"{text}_{voice_type}_{audio_format}"
        return hashlib.md5(content.encode()).hexdigest()

    def synthesize(self, text: str, voice_type: str = "female_standard",
                   audio_format: str = "mp3", section_type: str = None) -> Dict:
        """
        语音合成

        参数:
            text: 要合成的文本
            voice_type: 语音类型
            audio_format: 音频格式
            section_type: 章节类型 (opening/knowledge/example/summary) 用于场景化语音

        返回:
            dict: 包含音频文件路径和信息
        """
        self._init_components()

        # LaTeX 公式转语音文本
        from services.latex_to_speech import extract_and_convert_formulas
        text = extract_and_convert_formulas(text)

        # 清理：移除所有残留的 XML/SSML 标签和 URL
        text = text.strip()

        # 匹配 XML/SSML 标签：<tag ...> 或 </tag>
        # 要求 < 后跟字母，以避免误匹配数学比较符号 (如 3 < 5)
        text = re.sub(r'<\/?[a-zA-Z][^>]*>', '', text)
        # 移除 URL
        text = re.sub(r'http[s]?://\S+', '', text)
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text).strip()

        # 移除 URL
        text = re.sub(r'http[s]?://\S+', '', text)
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text).strip()

        # voice_type 直接使用用户选择的音色，不根据场景切换
        # （scene 音色切换会导致同一音频内音色不一致）

        # 生成缓存键
        cache_key = self._get_cache_key(text, voice_type, audio_format)
        audio_filename = f"{cache_key}.{audio_format}"
        audio_path = os.path.join(self._cache_dir, audio_filename)

        # 检查缓存
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            # 确保文件不是空的或太小的（无效的音频文件）
            if file_size > 1000:  # 至少1KB
                return {
                    "audioUrl": f"/api/v1/audio/{audio_filename}",
                    "audioPath": audio_path,
                    "fileSize": file_size,
                    "cached": True,
                }
            else:
                # 文件太小，删除并重新生成
                os.remove(audio_path)

        # 调用 TTS 服务
        try:
            # 尝试使用 edge-tts (免费的 TTS 服务)
            return self._synthesize_with_edge_tts(text, voice_type, audio_format, audio_path)
        except Exception as e:
            print(f"edge-tts 合成失败: {e}")
            try:
                # 尝试使用 pyttsx3 (离线 TTS)
                return self._synthesize_with_pyttsx3(text, voice_type, audio_format, audio_path)
            except Exception as e2:
                print(f"pyttsx3 合成失败: {e2}")
                # 使用简单的文本生成模拟音频
                return self._synthesize_mock(text, voice_type, audio_format, audio_path)

    def _synthesize_with_edge_tts(self, text: str, voice_type: str,
                                   audio_format: str, audio_path: str) -> Dict:
        """使用 edge-tts 进行语音合成"""
        import asyncio
        import edge_tts

        # 语音类型映射
        voice_map = {
            "female_standard": "zh-CN-XiaoxiaoNeural",
            "male_standard": "zh-CN-YunxiNeural",
            "female_warm": "zh-CN-XiaoyiNeural",
            "male_deep": "zh-CN-YunjianNeural",
        }

        # 解析 voice
        if voice_type.startswith("zh-CN-"):
            voice = voice_type
        else:
            voice = voice_map.get(voice_type, "zh-CN-XiaoxiaoNeural")

        async def _synthesize():
            # edge-tts 的 Communicate 直接接收文本，不使用 SSML
            # 因为 edge-tts 的 Python SDK 不支持内联 prosody 参数
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(audio_path)

        def _run_async():
            import asyncio as _asyncio
            loop = _asyncio.new_event_loop()
            _asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_synthesize())
            finally:
                loop.close()

        from concurrent.futures import ThreadPoolExecutor
        _pool = ThreadPoolExecutor(max_workers=1)
        _pool.submit(_run_async).result(timeout=30)
        _pool.shutdown(wait=False)

        # 验证文件生成成功
        if not os.path.exists(audio_path):
            raise Exception(f"edge-tts 音频文件未生成: {audio_path}")

        file_size = os.path.getsize(audio_path)
        if file_size < 1000:  # 文件太小说明生成失败
            raise Exception(f"edge-tts 音频文件过小 ({file_size} bytes): {audio_path}")

        audio_filename = os.path.basename(audio_path)
        return {
            "audioUrl": f"/api/v1/audio/{audio_filename}",
            "audioPath": audio_path,
            "fileSize": file_size,
            "cached": False,
        }

    def _synthesize_with_pyttsx3(self, text: str, voice_type: str, 
                                   audio_format: str, audio_path: str) -> Dict:
        """使用 pyttsx3 进行语音合成"""
        import pyttsx3

        engine = pyttsx3.init()
        
        # 设置语音属性
        voices = engine.getProperty('voices')
        if voices:
            # 尝试选择中文语音
            for voice in voices:
                if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break

        # 设置语速
        rate = engine.getProperty('rate')
        if voice_type == "fast":
            engine.setProperty('rate', rate + 50)
        elif voice_type == "slow":
            engine.setProperty('rate', rate - 50)

        # 保存音频
        engine.save_to_file(text, audio_path)
        engine.runAndWait()

        # 验证文件生成成功
        if not os.path.exists(audio_path):
            raise Exception(f"pyttsx3 音频文件未生成: {audio_path}")

        file_size = os.path.getsize(audio_path)
        if file_size < 1000:  # 文件太小说明生成失败
            raise Exception(f"pyttsx3 音频文件过小 ({file_size} bytes): {audio_path}")

        audio_filename = os.path.basename(audio_path)
        return {
            "audioUrl": f"/api/v1/audio/{audio_filename}",
            "audioPath": audio_path,
            "fileSize": file_size,
            "cached": False,
        }

    def _synthesize_mock(self, text: str, voice_type: str,
                          audio_format: str, audio_path: str) -> Dict:
        """Mock 不再使用，直接抛异常让上层处理"""
        raise Exception("edge-tts 和 pyttsx3 均不可用，无法生成语音")

    def synthesize_sections(self, sections: List[Dict], voice_type: str = "female_standard",
                            audio_format: str = "mp3", 
                            section_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        批量合成章节音频

        参数:
            sections: 章节列表，每个章节包含 sectionId 和 content
            voice_type: 语音类型
            audio_format: 音频格式
            section_ids: 指定要合成的章节ID列表

        返回:
            list: 章节音频信息列表
        """
        results = []
        total_duration = 0

        for section in sections:
            section_id = section.get("sectionId", "")
            content = section.get("content", "")
            section_name = section.get("sectionName", "")

            # 如果指定了 section_ids，只合成指定的章节
            if section_ids and section_id not in section_ids:
                continue

            if not content:
                continue

            # 根据 section 名称推断类型，用于场景化语音
            section_type = self._infer_section_type(section_name)

            # 合成音频（传入 section_type 以启用场景化语音 + LaTeX转换）
            result = self.synthesize(content, voice_type, audio_format, section_type=section_type)
            
            # 计算时长（根据文本长度估算）
            estimated_duration = max(1, len(content) * 0.15)  # 约每秒6-7个字
            total_duration += estimated_duration

            results.append({
                "sectionId": section_id,
                "audioUrl": result["audioUrl"],
                "duration": round(estimated_duration, 1),
            })

        return {
            "sectionAudios": results,
            "totalDuration": round(total_duration, 1),
        }

    @staticmethod
    def _infer_section_type(section_name: str) -> str:
        """根据章节名称推断类型"""
        name = section_name.lower() if section_name else ""
        if any(k in name for k in ["开场", "引入", "介绍", "前言"]):
            return "opening"
        if any(k in name for k in ["总结", "回顾", "结语", "小结"]):
            return "summary"
        if any(k in name for k in ["例", "练习", "应用", "例题"]):
            return "example"
        return "knowledge"


# 全局 TTS 服务实例
tts_service = TTSService()
