"""
语音识别 (ASR) 服务
"""
import os
import sys
import hashlib
import json
import base64
import tempfile
from typing import Optional, Dict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


class ASRService:
    """语音识别服务类"""

    _instance = None
    _cache_dir = "./data/asr_cache"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _init_components(self):
        """初始化组件"""
        if self._initialized:
            return
        
        # 创建识别结果缓存目录
        os.makedirs(self._cache_dir, exist_ok=True)
        self._initialized = True

    def _get_cache_key(self, audio_path: str) -> str:
        """生成缓存键"""
        content = f"{audio_path}_{os.path.getmtime(audio_path)}"
        return hashlib.md5(content.encode()).hexdigest()

    def recognize(self, audio_path: str, language: str = "zh-CN") -> Dict:
        """
        语音识别

        参数:
            audio_path: 音频文件路径
            language: 语言类型

        返回:
            dict: 包含识别文本和置信度
        """
        self._init_components()

        # 检查文件是否存在
        if not os.path.exists(audio_path):
            return {
                "text": "",
                "confidence": 0.0,
                "error": "音频文件不存在",
            }

        # 生成缓存键
        cache_key = self._get_cache_key(audio_path)
        cache_file = os.path.join(self._cache_dir, f"{cache_key}.json")

        # 检查缓存
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 调用 ASR 服务
        try:
            # 优先使用 DashScope paraformer
            if config.DASHSCOPE_API_KEY:
                return self._recognize_with_dashscope(audio_path, language, cache_file)
        except Exception as e:
            print(f"DashScope ASR 失败: {e}")

        try:
            return self._recognize_with_whisper(audio_path, language, cache_file)
        except Exception as e:
            print(f"whisper 识别失败: {e}")
            try:
                return self._recognize_with_speech_recognition(audio_path, language, cache_file)
            except Exception as e2:
                print(f"speech_recognition 识别失败: {e2}")
                return self._recognize_mock(audio_path, language, cache_file)

    def _recognize_with_dashscope(self, audio_path: str, language: str,
                                   cache_file: str) -> Dict:
        """使用 DashScope paraformer-realtime-v2 进行语音识别"""
        import dashscope
        from dashscope.audio.asr import Recognition
        from dashscope.audio.asr.recognition import RecognitionCallback
        import time

        dashscope.api_key = config.DASHSCOPE_API_KEY

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        print(f"  [ASR] 文件大小: {len(audio_data)} bytes, WAV 16kHz")

        if len(audio_data) < 100:
            raise Exception("音频文件过小")

        results = []
        finished = False

        class MyCallback(RecognitionCallback):
            def on_open(self):
                print("  [ASR] DashScope 连接已建立")

            def on_event(self, result):
                nonlocal finished
                if result and hasattr(result, "get_sentence"):
                    sentence = result.get_sentence()
                    if sentence and isinstance(sentence, dict):
                        text = sentence.get("text", "").strip()
                        if text:
                            results.append(text)
                            print(f"  [ASR] 片段: {text}")
                        if sentence.get("sentence_end") == 1:
                            finished = True

            def on_close(self):
                nonlocal finished
                finished = True
                print("  [ASR] DashScope 连接已关闭")

            def on_error(self, result):
                nonlocal finished
                finished = True
                print(f"  [ASR] DashScope 错误: {result}")

            def on_complete(self):
                nonlocal finished
                finished = True
                print("  [ASR] DashScope 识别完成")

        # 检测是否为 WAV 格式（前4字节为 RIFF），若是则跳过 44 字节头
        if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
            pcm_data = audio_data[44:]
            fmt = "pcm"
        else:
            pcm_data = audio_data
            fmt = "wav"

        recognition = Recognition(
            model="paraformer-realtime-v2",
            format=fmt,
            sample_rate=16000,
            language_hints=["zh"],
            callback=MyCallback(),
        )
        recognition.start()

        chunk_size = 3200
        for i in range(0, len(pcm_data), chunk_size):
            chunk = pcm_data[i:i + chunk_size]
            recognition.send_audio_frame(chunk)
            time.sleep(0.05)

        recognition.stop()

        for _ in range(100):
            if finished:
                break
            time.sleep(0.1)

        text = "".join(results).strip()
        print(f"  [ASR] DashScope 结果: {text[:200]}")

        output = {
            "text": text,
            "confidence": 0.95,
            "language": language,
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return output

    def _recognize_with_whisper(self, audio_path: str, language: str, 
                                 cache_file: str) -> Dict:
        """使用 whisper 进行语音识别"""
        import whisper

        # 加载模型
        model = whisper.load_model("base")
        
        # 识别
        result = model.transcribe(
            audio_path,
            language=language[:2],  # whisper 使用两位语言代码
        )

        output = {
            "text": result["text"].strip(),
            "confidence": result.get("confidence", 0.9),
            "language": language,
        }

        # 缓存结果
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return output

    def _recognize_with_speech_recognition(self, audio_path: str, language: str,
                                            cache_file: str) -> Dict:
        """使用 speech_recognition 进行语音识别"""
        import speech_recognition as sr
        from pydub import AudioSegment

        # 转换音频格式为 WAV（如果需要）
        temp_wav = audio_path
        if not audio_path.endswith('.wav'):
            temp_wav = audio_path.rsplit('.', 1)[0] + '_temp.wav'
            audio = AudioSegment.from_file(audio_path)
            audio.export(temp_wav, format='wav')

        # 识别
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=language)

        # 清理临时文件
        if temp_wav != audio_path and os.path.exists(temp_wav):
            os.remove(temp_wav)

        output = {
            "text": text.strip(),
            "confidence": 0.85,
            "language": language,
        }

        # 缓存结果
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return output

    def _recognize_mock(self, audio_path: str, language: str, 
                          cache_file: str) -> Dict:
        """模拟语音识别（用于测试）"""
        # 根据音频文件大小估算一些文本
        file_size = os.path.getsize(audio_path)
        
        # 生成模拟文本
        mock_texts = [
            "请问这个公式是什么意思？",
            "能解释一下这个概念吗？",
            "这个定理的应用场景是什么？",
            "如何理解这个知识点？",
            "这个实验的步骤是什么？",
        ]
        
        # 根据文件大小选择不同的模拟文本
        text_index = (file_size % len(mock_texts))
        text = mock_texts[text_index]

        output = {
            "text": text,
            "confidence": 0.5,  # 模拟识别的置信度较低
            "language": language,
            "is_mock": True,
        }

        # 缓存结果
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return output

    def recognize_from_url(self, voice_url: str, language: str = "zh-CN") -> Dict:
        """
        从URL识别语音

        参数:
            voice_url: 语音文件URL（支持 http/https URL、本地路径、base64 data-URL）
            language: 语言类型

        返回:
            dict: 包含识别文本和置信度
        """
        self._init_components()

        # 如果是 base64 data-URL（前端 FileReader.readAsDataURL 产生）
        if voice_url.startswith("data:"):
            try:
                # 解析 data:audio/webm;base64,AAAA...
                header, b64data = voice_url.split(",", 1)
                audio_bytes = base64.b64decode(b64data)
                # 从 header 推断扩展名
                ext = ".webm"
                if "wav" in header:
                    ext = ".wav"
                elif "mp3" in header:
                    ext = ".mp3"
                elif "ogg" in header:
                    ext = ".ogg"
                # 保存临时文件
                fd, temp_path = tempfile.mkstemp(suffix=ext, dir=self._cache_dir)
                with os.fdopen(fd, "wb") as f:
                    f.write(audio_bytes)
                try:
                    return self.recognize(temp_path, language)
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            except Exception as e:
                return {"text": "", "confidence": 0.0, "error": f"data-URL 解析失败: {e}"}

        # 如果是本地文件路径
        if os.path.exists(voice_url):
            return self.recognize(voice_url, language)

        # 如果是URL，下载文件
        try:
            import requests
            response = requests.get(voice_url, timeout=30)
            if response.status_code == 200:
                # 保存临时文件
                temp_path = os.path.join(self._cache_dir, "temp_audio.wav")
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                result = self.recognize(temp_path, language)
                
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                return result
            else:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "error": f"下载音频失败: {response.status_code}",
                }
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "error": f"下载音频失败: {str(e)}",
            }


# 全局 ASR 服务实例
asr_service = ASRService()
