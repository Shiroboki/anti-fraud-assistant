"""
反诈案例库 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user
from models.user import User
from models.anti_fraud import FraudCase, FraudType
from schemas.common import ApiResponse
from services.anti_fraud import anti_fraud_service

router = APIRouter()


@router.get("/list", summary="获取案例列表")
def list_cases(
    fraud_type: str = Query(default=None, description="诈骗类型筛选"),
    keyword: str = Query(default=None, description="关键词搜索"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(FraudCase).filter(FraudCase.is_published == True)

    if fraud_type:
        query = query.filter(FraudCase.fraud_type == fraud_type)
    if keyword:
        query = query.filter(
            (FraudCase.title.contains(keyword)) | (FraudCase.content.contains(keyword))
        )

    total = query.count()
    cases = (
        query.order_by(FraudCase.created_at.desc())
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
                "id": c.id,
                "title": c.title,
                "content": c.content[:500],
                "fraudType": c.fraud_type.value if c.fraud_type else "other",
                "source": c.source,
                "tags": c.tags,
                "viewCount": c.view_count,
                "createdAt": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if c.created_at else None,
            }
            for c in cases
        ],
    })


@router.get("/detail/{case_id}", summary="获取案例详情")
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(FraudCase).filter(FraudCase.id == case_id).first()
    if not case:
        return ApiResponse.error(404, "案例不存在")

    case.view_count += 1
    db.commit()

    return ApiResponse.success(data={
        "id": case.id,
        "title": case.title,
        "content": case.content,
        "fraudType": case.fraud_type.value if case.fraud_type else "other",
        "source": case.source,
        "tags": case.tags,
        "viewCount": case.view_count,
        "createdAt": case.created_at.strftime("%Y-%m-%d %H:%M:%S") if case.created_at else None,
    })


@router.get("/types", summary="获取诈骗类型统计")
def get_type_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import func
    stats = (
        db.query(FraudCase.fraud_type, func.count(FraudCase.id))
        .filter(FraudCase.is_published == True)
        .group_by(FraudCase.fraud_type)
        .all()
    )
    return ApiResponse.success(data=[
        {"type": t.value if t else "other", "count": c}
        for t, c in stats
    ])


@router.post("/sync-from-knowledge", summary="从知识库同步案例到数据库")
def sync_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从knowledges目录加载案例数据到数据库（仅管理员）"""
    user_role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    if user_role != "admin":
        return ApiResponse.error(403, "仅管理员可执行此操作")

    cases = anti_fraud_service.load_knowledge_cases()
    added = 0
    for c in cases:
        # 检查是否已存在
        existing = db.query(FraudCase).filter(FraudCase.title == c["title"]).first()
        if existing:
            continue
        case = FraudCase(
            title=c["title"],
            content=c["content"],
            source=c["source"],
            fraud_type=FraudType.OTHER,
        )
        db.add(case)
        added += 1
    db.commit()

    return ApiResponse.success(data={"added": added, "total_loaded": len(cases)})
