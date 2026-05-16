"""
诈骗检测 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from api.deps import get_db, get_current_user
from models.user import User
from models.anti_fraud import DetectionRecord, DetectionType, RiskLevel, FraudType
from schemas.common import ApiResponse
from services.anti_fraud import anti_fraud_service

router = APIRouter()


class TextDetectRequest(BaseModel):
    content: str = Field(description="待检测的文本内容")


@router.post("/text", summary="文本诈骗检测")
def detect_text(
    req: TextDetectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = anti_fraud_service.detect_fraud(req.content)

    # 保存检测记录
    record = DetectionRecord(
        user_id=current_user.id,
        detection_type=DetectionType.TEXT,
        input_content=req.content[:5000],
        risk_level=result.get("risk_level", "medium"),
        fraud_type=result.get("fraud_type"),
        analysis_result=result.get("analysis", ""),
        confidence=result.get("confidence", 0.5),
        suggestions=str(result.get("suggestions", [])),
    )
    db.add(record)
    db.commit()

    return ApiResponse.success(data=result)


@router.post("/image", summary="图片诈骗检测")
async def detect_image(
    file: UploadFile = File(...),
    description: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 读取图片
    content = await file.read()

    # 保存上传文件
    import os
    upload_dir = os.path.abspath("./uploads/detection")
    os.makedirs(upload_dir, exist_ok=True)
    import uuid
    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # 构建分析文本
    analysis_text = description or "用户上传了一张可疑截图，请分析是否存在诈骗风险。"

    # 尝试用VLM分析图片
    try:
        from services.vlm import vlm_service
        vlm_result = vlm_service.analyze_image(filepath, "请描述这张图片的内容，特别关注是否存在诈骗相关的元素，如：钓鱼链接、虚假客服、伪造证件、虚假转账截图等。")
        analysis_text = f"图片内容描述：{vlm_result}\n\n{analysis_text}"
    except Exception:
        pass

    result = anti_fraud_service.detect_fraud(analysis_text)

    # 保存记录
    record = DetectionRecord(
        user_id=current_user.id,
        detection_type=DetectionType.IMAGE,
        input_content=analysis_text[:5000],
        input_file_url=f"/uploads/detection/{filename}",
        risk_level=result.get("risk_level", "medium"),
        fraud_type=result.get("fraud_type"),
        analysis_result=result.get("analysis", ""),
        confidence=result.get("confidence", 0.5),
        suggestions=str(result.get("suggestions", [])),
    )
    db.add(record)
    db.commit()

    return ApiResponse.success(data=result)


@router.get("/history", summary="检测历史记录")
def get_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(DetectionRecord).filter(DetectionRecord.user_id == current_user.id)
    total = query.count()
    records = (
        query.order_by(DetectionRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ApiResponse.success(data={
        "total": total,
        "page": page,
        "pageSize": page_size,
        "items": [
            {
                "id": r.id,
                "detectionType": r.detection_type.value if r.detection_type else "text",
                "inputContent": (r.input_content or "")[:200],
                "riskLevel": r.risk_level.value if r.risk_level else "safe",
                "fraudType": r.fraud_type.value if r.fraud_type else None,
                "analysisResult": r.analysis_result,
                "confidence": r.confidence,
                "createdAt": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
            }
            for r in records
        ],
    })
