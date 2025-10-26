# Django Data Analysis System
# Django 数据分析系统

一个基于 Django 后端和 Vue.js 前端的智能数据分析系统。

## 📋 项目概述 (Project Overview)

本项目是一个集成了 AI 能力的数据分析平台，提供日志分析、向量检索等功能，并配有友好的聊天式交互界面。

### ✨ 主要特性 (Key Features)

- 🤖 **AI 驱动的对话式交互** - 通过聊天界面进行数据分析
- 📊 **日志数据分析** - 支持日志文件的导入和分析
- 🔍 **向量数据库检索** - 基于 ChromaDB 的高效向量检索
- 👥 **用户认证系统** - 安全的用户登录和会话管理
- 💬 **会话管理** - 保存和管理多个分析会话
- 🎨 **现代化界面** - 基于 Vue 3 的响应式用户界面

## 🏗️ 技术架构 (Technology Stack)

### 后端 (Backend)
- **框架**: Django (Python)
- **数据库**: SQLite + ChromaDB (向量数据库)
- **API**: RESTful API
- **认证**: Django Authentication

### 前端 (Frontend)
- **框架**: Vue 3
- **构建工具**: Vite
- **HTTP 客户端**: Axios
- **路由**: Vue Router
- **状态管理**: Vuex/Pinia

## 📁 项目结构 (Project Structure)

```
Django-Data-Analysis/
├── django_backend/          # Django 后端
│   ├── deepseek_api/       # API 应用模块
│   ├── deepseek_project/   # Django 项目配置
│   ├── data/               # 数据文件
│   │   ├── log/           # 日志数据
│   │   └── vector_stores/ # 向量数据库
│   ├── manage.py          # Django 管理脚本
│   └── topklogsystem.py   # 日志系统
│
├── vue_frontend/           # Vue.js 前端
│   ├── src/               # 源代码
│   │   ├── components/   # Vue 组件
│   │   ├── views/        # 页面视图
│   │   ├── api.js        # API 接口
│   │   ├── router.js     # 路由配置
│   │   └── store.js      # 状态管理
│   ├── public/           # 静态资源
│   └── package.json      # 依赖配置
│
├── CHANGELOG.md           # 变更日志
├── MODIFICATIONS_VISIBLE.md  # 修改可见性验证
└── README.md             # 项目说明文档 (本文件)
```

## 🚀 快速开始 (Quick Start)

### 前置要求 (Prerequisites)
- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 后端设置 (Backend Setup)

```bash
# 进入后端目录
cd django_backend

# 安装 Python 依赖 (如有 requirements.txt)
pip install -r requirements.txt

# 运行数据库迁移
python manage.py migrate

# 启动开发服务器
python manage.py runserver
```

### 前端设置 (Frontend Setup)

```bash
# 进入前端目录
cd vue_frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📚 API 文档 (API Documentation)

API 端点位于 `/api/` 路径下，主要包括：

- 用户认证相关接口
- 会话管理接口
- 消息处理接口
- 数据分析接口

详细的 API 文档请查看代码中的注释或生成 OpenAPI 文档。

## 🔧 开发说明 (Development)

### 数据库模型 (Database Models)
- `User` - 用户模型
- `Session` - 会话模型
- `Message` - 消息模型

### 关键组件 (Key Components)
- `ChatInput.vue` - 聊天输入组件
- `ChatMessage.vue` - 消息显示组件
- `SessionList.vue` - 会话列表组件

## 📝 变更日志 (Changelog)

查看 [CHANGELOG.md](./CHANGELOG.md) 了解项目的详细变更历史。

## 🤝 贡献指南 (Contributing)

欢迎提交 Issue 和 Pull Request！

## 📄 许可证 (License)

本项目的许可证信息请查看项目根目录。

## 👥 作者 (Authors)

- Chenkaixuan <chenkaixuan94@outlook.com>

---

**注意**: 本项目正在积极开发中，功能和 API 可能会有变化。

*最后更新: 2025-10-26*
