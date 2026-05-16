"""
认证模块路由
"""
import config
import uuid
from datetime import datetime, timedelta

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from schemas.common import ApiResponse
from schemas.auth import UserCreate, UserLogin, Token, UserResponse
from services.auth import auth_service
from services.email import send_verification_email, send_password_reset_email
from models import get_db
from models.user import User, UserRole
from models.permission import Role, Permission

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@router.post("/register", response_model=ApiResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口
    """
    # 检查用户名是否已存在
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        return ApiResponse.error(400, "用户名或邮箱已存在")

    # 验证角色
    try:
        role = UserRole(user_data.role)
    except ValueError:
        return ApiResponse.error(400, "无效的角色类型，可选：admin/teacher/student")

    # 创建用户
    hashed_password = auth_service.get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        real_name=user_data.realName,
        role=role,
        school_id=user_data.schoolId,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 分配对应角色
    role_record = db.query(Role).filter(Role.name == user_data.role).first()
    if role_record:
        user.roles.append(role_record)
        db.commit()

    # 发送验证邮件
    verification_token = uuid.uuid4().hex
    user.verification_token = verification_token
    db.commit()
    send_verification_email(user.email, user.real_name or user.username, verification_token)

    return ApiResponse.success(
        data=user.to_dict(),
        msg="注册成功，验证邮件已发送到您的邮箱",
    )


@router.post("/login", response_model=ApiResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    用户登录接口（OAuth2标准）
    """
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return ApiResponse.error(401, "用户名或密码错误")

    # 生成JWT token
    access_token = auth_service.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value if isinstance(user.role, UserRole) else user.role,
        }
    )

    return ApiResponse.success(
        data={
            "accessToken": access_token,
            "tokenType": "bearer",
            "expiresIn": config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "userInfo": user.to_dict(),
        },
        msg="登录成功",
    )


@router.post("/login/json", response_model=ApiResponse)
async def login_json(
    req: dict,
    db: Session = Depends(get_db),
):
    """
    JSON格式登录接口（供小程序调用）
    支持角色登录
    """
    username = req.get("username", "")
    password = req.get("password", "")
    role = req.get("role", None)  # 可选，用于前端展示

    if not username or not password:
        return ApiResponse.error(400, "用户名和密码不能为空")

    user = auth_service.authenticate_user(db, username, password)
    if not user:
        return ApiResponse.error(401, "用户名或密码错误")

    # 如果指定了角色，验证角色是否匹配
    user_role = user.role.value if isinstance(user.role, UserRole) else user.role
    if role and role != user_role:
        role_map = {'student': '学生', 'teacher': '教师', 'admin': '管理员'}
        actual_role = role_map.get(user_role, user_role)
        raise HTTPException(status_code=403, detail=f"登录身份不匹配：该账户注册为{actual_role}，请选择正确的身份后重新登录")

    # 生成JWT token
    access_token = auth_service.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user_role,
        }
    )

    return ApiResponse.success(
        data={
            "accessToken": access_token,
            "tokenType": "bearer",
            "expiresIn": config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "userInfo": user.to_dict(),
        },
        msg="登录成功",
    )


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    刷新 JWT token 接口
    在 token 过期前调用，可获取新的 token（有效期重新计算）
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    # 验证当前 token
    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    username = payload.get("sub")
    user = auth_service.get_user_by_username(db, username)
    if not user or not user.is_active:
        return ApiResponse.error(401, "用户不存在或已禁用")

    # 生成新的 token
    new_token = auth_service.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value if isinstance(user.role, UserRole) else user.role,
        }
    )

    return ApiResponse.success(
        data={
            "accessToken": new_token,
            "tokenType": "bearer",
            "expiresIn": config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
        msg="Token 刷新成功",
    )


@router.get("/me", response_model=ApiResponse)
async def get_current_user_info(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    获取当前登录用户信息
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    username = payload.get("sub")
    user = auth_service.get_user_by_username(db, username)
    if not user:
        return ApiResponse.error(401, "用户不存在")

    # 获取用户角色和权限
    permissions = []
    for role in user.roles:
        for perm in role.permissions:
            permissions.append(perm.name)

    user_data = user.to_dict()
    user_data["permissions"] = list(set(permissions))

    return ApiResponse.success(data=user_data)


@router.get("/users", response_model=ApiResponse)
async def list_users(
    keyword: Optional[str] = None,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    获取用户列表（仅管理员）
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    role = payload.get("role")
    if role != "admin":
        return ApiResponse.error(403, "权限不足，需要管理员角色")

    query = db.query(User).filter(User.is_deleted == False)
    if keyword:
        query = query.filter(
            (User.username.contains(keyword)) | (User.email.contains(keyword))
        )
    users = query.order_by(User.id.desc()).all()
    user_list = [u.to_dict() for u in users]

    return ApiResponse.success(data=user_list)


@router.put("/users/{user_id}", response_model=ApiResponse)
async def update_user(
    user_id: int,
    req: dict,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    编辑用户（仅管理员）
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    if payload.get("role") != "admin":
        return ApiResponse.error(403, "权限不足，需要管理员角色")

    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        return ApiResponse.error(404, "用户不存在")

    if "role" in req and req["role"]:
        try:
            user.role = UserRole(req["role"])
        except ValueError:
            return ApiResponse.error(400, "无效的角色类型")
    if "isActive" in req:
        user.is_active = bool(req["isActive"])
    if "email" in req and req["email"]:
        user.email = req["email"]
    if "realName" in req:
        user.real_name = req["realName"]
    if "schoolId" in req:
        user.school_id = req["schoolId"] or None

    db.commit()
    db.refresh(user)

    return ApiResponse.success(data=user.to_dict(), msg="更新成功")


@router.delete("/users/{user_id}", response_model=ApiResponse)
async def delete_user(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    软删除用户（仅管理员）
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    if payload.get("role") != "admin":
        return ApiResponse.error(403, "权限不足，需要管理员角色")

    # 不能删除自己
    admin_user = auth_service.get_user_by_username(db, payload.get("sub"))
    if admin_user and admin_user.id == user_id:
        return ApiResponse.error(400, "不能删除当前登录用户")

    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        return ApiResponse.error(404, "用户不存在")

    user.is_deleted = True
    user.is_active = False
    db.commit()

    return ApiResponse.success(msg="删除成功")


@router.get("/roles", response_model=ApiResponse)
async def list_roles(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    获取角色列表（仅管理员）
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    role = payload.get("role")
    if role != "admin":
        return ApiResponse.error(403, "权限不足，需要管理员角色")

    roles = db.query(Role).all()
    role_list = [r.to_dict() for r in roles]

    return ApiResponse.success(data=role_list)


@router.get("/permissions", response_model=ApiResponse)
async def list_permissions(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    获取权限列表（仅管理员）
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    user_role = payload.get("role")
    if user_role != "admin":
        return ApiResponse.error(403, "权限不足，需要管理员角色")

    permissions = db.query(Permission).all()
    perm_list = [p.to_dict() for p in permissions]

    return ApiResponse.success(data=perm_list)


@router.put("/profile", response_model=ApiResponse)
async def update_profile(
    req: dict,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    更新当前用户信息
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    username = payload.get("sub")
    user = auth_service.get_user_by_username(db, username)
    if not user:
        return ApiResponse.error(401, "用户不存在")

    if "email" in req and req["email"]:
        user.email = req["email"]
    if "realName" in req and req["realName"]:
        user.real_name = req["realName"]
    if "schoolId" in req and req["schoolId"]:
        user.school_id = req["schoolId"]
    if "avatar" in req and req["avatar"]:
        user.avatar = req["avatar"]

    db.commit()
    db.refresh(user)

    return ApiResponse.success(data=user.to_dict(), msg="更新成功")


@router.post("/update-profile", response_model=ApiResponse)
async def update_profile_post(
    req: dict,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    更新当前用户信息
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    username = payload.get("sub")
    user = auth_service.get_user_by_username(db, username)
    if not user:
        return ApiResponse.error(401, "用户不存在")

    if "email" in req and req["email"]:
        user.email = req["email"]
    if "realName" in req and req["realName"]:
        user.real_name = req["realName"]
    if "schoolId" in req and req["schoolId"]:
        user.school_id = req["schoolId"]
    if "avatar" in req and req["avatar"]:
        user.avatar = req["avatar"]

    db.commit()
    db.refresh(user)

    return ApiResponse.success(data=user.to_dict(), msg="更新成功")


@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    req: dict,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    修改密码
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    username = payload.get("sub")
    user = auth_service.get_user_by_username(db, username)
    if not user:
        return ApiResponse.error(401, "用户不存在")

    current_password = req.get("currentPassword", "")
    new_password = req.get("newPassword", "")

    if not auth_service.verify_password(current_password, user.hashed_password):
        return ApiResponse.error(400, "当前密码错误")

    if len(new_password) < 6:
        return ApiResponse.error(400, "新密码长度不能少于6位")

    user.hashed_password = auth_service.get_password_hash(new_password)
    db.commit()

    return ApiResponse.success(msg="密码修改成功")


@router.post("/avatar/upload", response_model=ApiResponse)
async def upload_avatar(
    req: dict,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    上传头像（接收Base64图片并上传到OSS）

    请求体: { "image": "data:image/png;base64,xxxxx" }
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    username = payload.get("sub")
    user = auth_service.get_user_by_username(db, username)
    if not user:
        return ApiResponse.error(401, "用户不存在")

    image_data = req.get("image")
    if not image_data:
        return ApiResponse.error(400, "图片数据不能为空")

    try:
        import base64
        import uuid

        # 解析 Base64
        if "," in image_data:
            header, data = image_data.split(",", 1)
            # 提取 mime 类型
            mime = header.split(";")[0].replace("data:", "")
        else:
            data = image_data
            mime = "image/png"

        # 生成文件名
        ext = "png" if mime == "image/png" else "jpg"
        filename = f"avatar/{user.id}/{uuid.uuid4().hex[:12]}.{ext}"

        # 上传到 OSS
        file_content = base64.b64decode(data)

        import oss2

        auth = oss2.Auth(config.OSS_ACCESS_KEY_ID, config.OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, config.OSS_ENDPOINT, config.OSS_BUCKET_NAME)

        result = bucket.put_object(filename, file_content)
        if result.status == 200:
            avatar_url = f"{config.OSS_BASE_URL}/{filename}"
            # 更新用户头像
            user.avatar = avatar_url
            db.commit()
            db.refresh(user)
            return ApiResponse.success(data={"avatar": avatar_url}, msg="头像上传成功")
        else:
            return ApiResponse.error(500, "上传失败")

    except Exception as e:
        return ApiResponse.error(500, f"上传失败: {str(e)}")


@router.delete("/roles/{role_id}", response_model=ApiResponse)
async def delete_role(
    role_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    删除角色（仅管理员）
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    if payload.get("role") != "admin":
        return ApiResponse.error(403, "权限不足，需要管理员角色")

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return ApiResponse.error(404, "角色不存在")

    db.delete(role)
    db.commit()

    return ApiResponse.success(msg="删除成功")


@router.post("/roles", response_model=ApiResponse)
async def create_or_update_role(
    req: dict,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    创建或更新角色（仅管理员）
    """
    if not token:
        return ApiResponse.error(401, "未提供认证令牌")

    payload = auth_service.verify_token(token)
    if not payload:
        return ApiResponse.error(401, "无效的认证令牌")

    if payload.get("role") != "admin":
        return ApiResponse.error(403, "权限不足，需要管理员角色")

    role_id = req.get("id")
    if role_id:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return ApiResponse.error(404, "角色不存在")
        role.name = req.get("name", role.name)
        role.description = req.get("description", role.description)
    else:
        role = Role(
            name=req.get("name", ""),
            description=req.get("description", ""),
        )
        db.add(role)

    # 更新权限关联
    permission_ids = req.get("permissionIds", [])
    if permission_ids:
        permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        role.permissions = permissions

    db.commit()
    db.refresh(role)

    return ApiResponse.success(data=role.to_dict(), msg="保存成功")


@router.post("/forgot-password", response_model=ApiResponse)
async def forgot_password(req: dict, db: Session = Depends(get_db)):
    """请求密码重置"""
    email = req.get("email", "").strip()
    if not email:
        return ApiResponse.error(400, "请输入邮箱地址")

    user = db.query(User).filter(User.email == email, User.is_deleted == False).first()
    if not user:
        return ApiResponse.success(msg="如果该邮箱已注册，重置邮件将发送到您的邮箱")

    token = uuid.uuid4().hex
    user.reset_token = token
    user.reset_token_expires = datetime.now() + timedelta(hours=1)
    db.commit()

    send_password_reset_email(user.email, user.real_name or user.username, token)
    return ApiResponse.success(msg="如果该邮箱已注册，重置邮件将发送到您的邮箱")


@router.post("/reset-password", response_model=ApiResponse)
async def reset_password(req: dict, db: Session = Depends(get_db)):
    """通过令牌重置密码"""
    token = req.get("token", "").strip()
    new_password = req.get("newPassword", "")

    if not token:
        return ApiResponse.error(400, "缺少重置令牌")
    if len(new_password) < 6:
        return ApiResponse.error(400, "密码长度不能少于6位")

    user = db.query(User).filter(
        User.reset_token == token,
        User.is_deleted == False,
    ).first()

    if not user or not user.reset_token_expires:
        return ApiResponse.error(400, "无效的重置令牌")

    if datetime.now() > user.reset_token_expires:
        return ApiResponse.error(400, "重置令牌已过期，请重新申请")

    user.hashed_password = auth_service.get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return ApiResponse.success(msg="密码重置成功，请登录")


@router.post("/verify-email", response_model=ApiResponse)
async def verify_email(req: dict, db: Session = Depends(get_db)):
    """验证邮箱"""
    token = req.get("token", "").strip()
    if not token:
        return ApiResponse.error(400, "缺少验证令牌")

    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        return ApiResponse.error(400, "无效的验证令牌")

    user.email_verified = True
    user.verification_token = None
    db.commit()

    return ApiResponse.success(msg="邮箱验证成功")


@router.post("/resend-verification", response_model=ApiResponse)
async def resend_verification(req: dict, db: Session = Depends(get_db)):
    """重新发送验证邮件"""
    email = req.get("email", "").strip()
    if not email:
        return ApiResponse.error(400, "请输入邮箱地址")

    user = db.query(User).filter(User.email == email, User.is_deleted == False).first()
    if not user:
        return ApiResponse.success(msg="如果该邮箱已注册，验证邮件将发送到您的邮箱")

    if user.email_verified:
        return ApiResponse.success(msg="该邮箱已验证")

    token = uuid.uuid4().hex
    user.verification_token = token
    db.commit()

    send_verification_email(user.email, user.real_name or user.username, token)
    return ApiResponse.success(msg="验证邮件已发送")
