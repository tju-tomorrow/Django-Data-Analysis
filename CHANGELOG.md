# 变更日志 (CHANGELOG)

本文档记录了项目的所有重要变更。

## [未发布] - 2025-10-26

### 新增 (Added)
- 📝 添加了修改可见性验证文档 (MODIFICATIONS_VISIBLE.md)
- 📝 添加了本变更日志文件 (CHANGELOG.md)

### 说明 (Notes)
- 验证了仓库的最新修改可以被正常访问和查看
- 确认了所有代码结构完整且可用

---

## [初始版本] - 2025-10-21

### 新增 (Added)
- 🎉 初始化项目仓库
- 🔧 Django 后端框架搭建
  - deepseek_api 应用模块
  - deepseek_project 项目配置
  - 数据库模型定义
  - RESTful API 接口
  - 服务层实现
- 🎨 Vue.js 前端框架搭建
  - Vue 3 + Vite 项目初始化
  - 聊天界面组件
  - 登录页面
  - 会话管理组件
  - 路由配置
  - 状态管理
- 📊 数据文件
  - 日志数据 (20200.csv)
  - 向量数据库 (ChromaDB)
- 📄 配置文件
  - .gitignore (Python, Django, Vue)
  - package.json
  - vite.config.js

### 技术选型 (Technology Choices)
- **后端框架**: Django (Python Web Framework)
- **前端框架**: Vue 3 (Progressive JavaScript Framework)
- **构建工具**: Vite (Next Generation Frontend Tooling)
- **数据库**: SQLite + ChromaDB (Vector Database)
- **HTTP 客户端**: Axios (Promise based HTTP client)

### 文件统计 (File Statistics)
- 总文件数: 46 个文件
- 代码行数: 4688+ 行
- 包含二进制文件: 是 (数据库文件)

---

## 格式说明 (Format Guide)

本变更日志遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 规范，
并且本项目遵守 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

### 变更类型 (Types of Changes)
- `新增 (Added)` - 新功能
- `变更 (Changed)` - 现有功能的变更
- `弃用 (Deprecated)` - 即将移除的功能
- `移除 (Removed)` - 已移除的功能
- `修复 (Fixed)` - 任何问题修复
- `安全 (Security)` - 安全相关的修复或改进

---
*最后更新: 2025-10-26*
