# MiroFish 🐟

**简洁通用的群体智能引擎，预测万物**

MiroFish 是一个基于多智能体（Multi-Agent）技术的社交媒体舆情模拟平台，能够模拟 Twitter/Reddit 等社交媒体上的用户行为，预测舆情发展趋势。

## 📁 项目结构

```
MiroFish/
├── backend/           # Flask 后端服务
│   ├── app/          # 应用核心代码
│   ├── scripts/      # OASIS 模拟脚本
│   ├── requirements.txt
│   └── run.py        # 后端启动入口
├── frontend/          # Vue 3 前端
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .env.example       # 环境变量示例
├── docker-compose.yml # Docker 部署配置
├── package.json       # 根目录启动脚本
└── README.md
```

---

## 🚀 快速开始

### 前置要求

在开始之前，请确保已安装以下工具：

| 工具 | 版本要求 | 说明 | 安装检查 |
|------|---------|------|---------|
| **Node.js** | 18+ | 前端运行环境，包含 npm | `node -v` |
| **Python** | 3.11+ | 后端运行环境 | `python --version` |
| **uv** | 最新版 | Python 包管理器（替代 pip） | `uv --version` |

#### 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 Homebrew (macOS)
brew install uv
```

> ⚠️ 安装 uv 后需要**重新打开终端**或执行 `source ~/.zshrc` (macOS/Linux) 使其生效。

### 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入必要的 API 密钥
```

必需的环境变量：

```env
# LLM 配置（支持 OpenAI 格式的任意 LLM）
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# Zep Cloud 配置
ZEP_API_KEY=your_zep_api_key
```

---

## 📦 部署方式一：源码部署（开发推荐）

使用 `concurrently` 同时启动前后端，**跨平台兼容**（Windows/macOS/Linux）。

### 1. 安装依赖

```bash
# 一键安装所有依赖（根目录 + 前端 + 后端）
npm run setup:all
```

或者分步安装：

```bash
# 安装 Node 依赖（根目录 + 前端）
npm run setup

# 安装 Python 依赖（自动创建虚拟环境）
npm run setup:backend
```

### 2. 启动服务

```bash
# 同时启动前后端（在项目根目录执行）
npm run dev
```

服务地址：
- 前端：`http://localhost:3000`
- 后端 API：`http://localhost:5001`

### 单独启动

```bash
# 仅启动后端
npm run backend

# 仅启动前端
npm run frontend
```

---

## 🐳 部署方式二：Docker 部署（生产推荐）

### 前置要求

- Docker 20.10+
- Docker Compose v2+

### 启动服务

```bash
# 构建并启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

服务地址：
- 前端：`http://localhost:3000`
- 后端 API：`http://localhost:5001`

### 仅构建镜像

```bash
# 构建后端镜像
docker build -t mirofish-backend ./backend

# 构建前端镜像
docker build -t mirofish-frontend ./frontend
```

---

## 🛠 技术栈

### 后端
- **框架**: Flask 3.x
- **LLM 调用**: OpenAI SDK
- **图谱存储**: Zep Cloud
- **模拟引擎**: OASIS (camel-oasis)

### 前端
- **框架**: Vue 3 + Composition API
- **构建工具**: Vite
- **可视化**: D3.js
- **HTTP 客户端**: Axios

---

## ⚙️ 环境变量说明

| 变量名 | 必需 | 说明 | 默认值 |
|--------|------|------|--------|
| `LLM_API_KEY` | ✅ | LLM API 密钥 | - |
| `LLM_BASE_URL` | ❌ | LLM API 地址 | `https://api.openai.com/v1` |
| `LLM_MODEL_NAME` | ❌ | 模型名称 | `gpt-4o-mini` |
| `ZEP_API_KEY` | ✅ | Zep Cloud API 密钥 | - |
| `FLASK_DEBUG` | ❌ | 调试模式 | `true` |
| `FLASK_HOST` | ❌ | 后端监听地址 | `0.0.0.0` |
| `FLASK_PORT` | ❌ | 后端端口 | `5001` |

---

## 🐛 常见问题

### Q: 后端启动报错 "LLM_API_KEY 未配置"
A: 确保 `.env` 文件在项目根目录，且配置了正确的 API 密钥。

### Q: 前端无法连接后端
A: 检查后端是否正常运行在 5001 端口，前端开发服务器会自动代理 `/api/*` 请求。

### Q: OASIS 模拟启动失败
A: 确保已安装 `camel-oasis` 和 `camel-ai` 依赖，且 LLM API 配置正确。

### Q: 运行 `npm run setup:backend` 报错 "uv: command not found"
A: uv 未安装或未加入 PATH。请先安装 uv（参考前置要求），安装后**重新打开终端**再执行。

### Q: Windows 上 Python 虚拟环境激活失败
A: 使用 `.venv\Scripts\activate` 而不是 `source .venv/bin/activate`。

---

## 📄 License

Apache License 2.0
