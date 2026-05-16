"""
反诈问答 API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from api.deps import get_db, get_current_user
from models.user import User
from models.anti_fraud import ChatSession, ChatMessage
from schemas.common import ApiResponse
from services.anti_fraud import anti_fraud_service

router = APIRouter()


class CreateSessionRequest(BaseModel):
    title: str = Field(default="反诈咨询", description="会话标题")


class SendMessageRequest(BaseModel):
    session_id: int = Field(description="会话ID")
    content: str = Field(description="消息内容")


@router.get("/sessions", summary="获取会话列表")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id, ChatSession.is_active == True)
        .order_by(ChatSession.updated_at.desc())
        .limit(50)
        .all()
    )
    return ApiResponse.success(data=[
        {
            "id": s.id,
            "title": s.title,
            "createdAt": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else None,
            "updatedAt": s.updated_at.strftime("%Y-%m-%d %H:%M:%S") if s.updated_at else None,
        }
        for s in sessions
    ])


@router.post("/sessions", summary="创建会话")
def create_session(
    req: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = ChatSession(user_id=current_user.id, title=req.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return ApiResponse.success(data={"id": session.id, "title": session.title})


@router.get("/sessions/{session_id}/messages", summary="获取会话消息")
def get_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        return ApiResponse.error(404, "会话不存在")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return ApiResponse.success(data=[
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "contentType": m.content_type,
            "createdAt": m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else None,
        }
        for m in messages
    ])


@router.post("/chat", summary="发送消息并获取AI回复")
def chat(
    req: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == req.session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        return ApiResponse.error(404, "会话不存在")

    # 保存用户消息
    user_msg = ChatMessage(session_id=req.session_id, role="user", content=req.content)
    db.add(user_msg)
    db.commit()

    # 获取历史消息构建上下文
    history_msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == req.session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in history_msgs[:-1]]  # 排除刚加的

    # 调用AI
    try:
        reply = anti_fraud_service.chat(req.content, history=history)
    except Exception as e:
        reply = f"抱歉，AI服务暂时不可用，请稍后重试。如有紧急情况请拨打96110反诈专线。\n\n错误详情：{str(e)}"

    # 保存AI回复
    ai_msg = ChatMessage(session_id=req.session_id, role="assistant", content=reply)
    db.add(ai_msg)
    db.commit()

    return ApiResponse.success(data={
        "reply": reply,
        "replyId": ai_msg.id,
    })
