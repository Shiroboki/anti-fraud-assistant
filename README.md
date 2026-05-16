# 多模态智能反诈助手

基于 AI 的反诈骗辅助平台，提供智能问答、诈骗检测、案例学习等功能。

## 功能特性

- **AI 反诈问答** — 基于大模型的反诈智能助手，支持多轮对话
- **诈骗检测** — 支持文本/图片输入，AI 分析诈骗风险等级
- **反诈案例库** — 分类展示真实诈骗案例，支持搜索筛选
- **用户系统** — 注册/登录/权限管理

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | MySQL 8.0 |
| AI 模型 | 通义千问 / Ollama (可切换) |
| 认证 | JWT |

## 项目结构

```
├── api/                    # 后端 API
│   ├── app.py              # FastAPI 入口
│   ├── deps.py             # 认证依赖注入
│   ├── middleware/          # 限流、签名中间件
│   └── v1/                 # API 路由
│       ├── auth.py         # 登录注册
│       ├── anti_fraud_chat.py    # 反诈问答
│       ├── anti_fraud_detect.py  # 诈骗检测
│       └── anti_fraud_case.py    # 反诈案例
├── models/                 # 数据库模型
│   ├── user.py             # 用户表
│   └── anti_fraud.py       # 反诈相关表
├── services/               # 业务服务
│   ├── anti_fraud.py       # 反诈 AI 服务
│   └── auth.py             # 认证服务
├── frontend/               # 前端项目
│   └── src/
│       ├── views/anti-fraud/  # 反诈页面
│       ├── api/antiFraud.js   # API 调用
│       └── router/index.js    # 路由配置
├── knowledges/             # 反诈知识库（PDF/JSON）
├── config.py               # 全局配置
├── main.py                 # 启动入口
└── requirements.txt        # Python 依赖
```

## 环境要求

- Python 3.10+
- Node.js 16+
- MySQL 8.0+

## 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/Shiroboki/anti-fraud-assistant.git
cd anti-fraud-assistant
```

### 2. 创建数据库

```sql
CREATE DATABASE anti_fraud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的数据库密码
MYSQL_DB=anti_fraud

# AI 模型配置（二选一）
# 方案一：通义千问（云端）
CHAT_PROVIDER=tongyi
DASHSCOPE_API_KEY=你的通义千问API Key

# 方案二：Ollama（本地）
# CHAT_PROVIDER=ollama
# CHAT_MODEL_OLLAMA=qwen3.5:9b
# OLLAMA_URL=http://localhost:11434
```

### 4. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 5. 启动后端

```bash
python main.py
```

后端默认运行在 `http://127.0.0.1:8000`，API 文档：`http://127.0.0.1:8000/docs`

### 6. 安装并启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`

### 7. 初始化数据

1. 访问 `http://localhost:5173` 注册账号或使用管理员账号登录
2. 用管理员账号登录后，进入反诈案例库页面，点击"从知识库导入案例"

## 管理员账号

首次启动时需要手动创建管理员账号：

```bash
python -c "
from models import init_db, SessionLocal
from models.user import User, UserRole
from passlib.context import CryptContext
init_db()
db = SessionLocal()
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto').hash('123456')
admin = User(username='admin', email='admin@example.com', hashed_password=pwd,
             real_name='管理员', role=UserRole.ADMIN, is_active=True, email_verified=True)
db.add(admin)
db.commit()
print('管理员创建成功: admin / 123456')
"
```

## API 接口

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `POST /api/v1/auth/login/json` | 登录 |
| 认证 | `POST /api/v1/auth/register` | 注册 |
| 问答 | `GET /api/v1/af/chat/sessions` | 会话列表 |
| 问答 | `POST /api/v1/af/chat/chat` | 发送消息 |
| 检测 | `POST /api/v1/af/detect/text` | 文本检测 |
| 检测 | `POST /api/v1/af/detect/image` | 图片检测 |
| 案例 | `GET /api/v1/af/case/list` | 案例列表 |
| 案例 | `POST /api/v1/af/case/sync-from-knowledge` | 同步知识库 |

完整 API 文档请访问：`http://127.0.0.1:8000/docs`

## 常见问题

**Q: 启动报错 `Unknown database 'anti_fraud'`**
A: 需要先在 MySQL 中创建数据库，参考"创建数据库"步骤。

**Q: AI 问答没有回复**
A: 检查 `.env` 中的 AI 模型配置是否正确，确保 API Key 有效或 Ollama 服务已启动。

**Q: 前端启动后页面空白**
A: 确保后端已启动，前端 vite 代理指向 `http://localhost:8000`。
