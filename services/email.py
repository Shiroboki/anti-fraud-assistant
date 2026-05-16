"""
邮件服务（占位）
"""
import logging

logger = logging.getLogger(__name__)


def send_verification_email(email: str, username: str, token: str):
    logger.info(f"[邮件] 验证邮件 -> {email} (用户: {username}, token: {token[:8]}...)")


def send_password_reset_email(email: str, username: str, token: str):
    logger.info(f"[邮件] 密码重置 -> {email} (用户: {username}, token: {token[:8]}...)")
