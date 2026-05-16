"""
文本处理工具
从 pipeline.py 中提取
"""
import re


def normalize_text(text: str) -> str:
    """
    清理文本：合并连续空格/制表符，合并3个以上连续换行，移除首尾空格

    参数:
        text: 原始文本

    返回:
        清理后的文本
    """
    if not text:
        return ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, max_size: int = 500) -> list:
    """
    分块文本：优先按段落切分，不在段落中间切断

    参数:
        text: 要分块的文本
        max_size: 每个块的最大字符数

    返回:
        分块后的文本列表
    """
    if not text:
        return []
    if max_size <= 0:
        return [text]

    paragraphs = text.split("\n")
    chunks = []
    current_parts = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_len = len(para)

        if para_len > max_size:
            if current_parts:
                chunks.append("\n".join(current_parts))
                current_parts = []
                current_len = 0
            sub_parts = re.split(r"(?<=[。！？；])", para)
            sub_chunk = ""
            for sp in sub_parts:
                sp = sp.strip()
                if not sp:
                    continue
                if sub_chunk and len(sub_chunk) + len(sp) + 1 > max_size:
                    chunks.append(sub_chunk)
                    sub_chunk = sp
                else:
                    sub_chunk = (sub_chunk + " " + sp).strip() if sub_chunk else sp
            if sub_chunk:
                chunks.append(sub_chunk)
            continue

        added_len = para_len + (1 if current_parts else 0)
        if current_len + added_len > max_size and current_parts:
            chunks.append("\n".join(current_parts))
            current_parts = [para]
            current_len = para_len
        else:
            current_parts.append(para)
            current_len += added_len

    if current_parts:
        chunks.append("\n".join(current_parts))
    return chunks
