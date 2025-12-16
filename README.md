# CS2-YCY-Link

<div align="center">

**CS2 游戏事件触发 YCY 设备联动系统**

一个将 Counter-Strike 2 游戏事件与 YCY 设备实时联动的智能系统

[快速开始](#快速开始) • [功能特性](#功能特性) • [打包部署](#打包部署) • [常见问题](#常见问题)

</div>

---

## 📖 简介

CS2-YCY-Link 是一个创新的游戏联动系统，能够实时监听 CS2 游戏中的各种事件（如玩家受伤、死亡、闪光等），并通过腾讯云即时通讯（IM）将指令发送到 YCY 设备端，实现游戏与物理设备的沉浸式互动体验。

### 🎯 核心特点

- **🔄 前后端分离架构**: 后端专注于游戏事件监听，前端直接连接腾讯云 IM 发送指令
- **⚡ 实时通信**: 基于 WebSocket 实现毫秒级的事件响应
- **🎨 可视化配置**: 无需编码，在 Web 界面即可配置事件与指令的映射关系
- **🔒 安全可靠**: Token 在前端管理，不经过后端存储，保护隐私安全
- **🎮 即插即用**: 简单配置即可开始使用，支持自定义事件和指令
- **📦 一键打包**: 支持打包成独立可执行文件，无需安装依赖

## 🏗️ 系统架构

```
┌─────────────┐
│   CS2 游戏   │
│             │
└──────┬──────┘
       │ GSI (游戏状态数据)
       │ HTTP POST
       ▼
┌─────────────────────────────────────────────────────────┐
│                    Python 后端 (FastAPI)                 │
│                      端口: 8001                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ • 接收 CS2 游戏状态 (GSI)                         │  │
│  │ • 解析游戏事件并检测触发条件                      │  │
│  │ • 调用 Node.js IM 服务发送指令                    │  │
│  │ • 通过 WebSocket 通知前端                         │  │
│  │ • 提供前端静态文件服务                            │  │
│  └──────────────────────────────────────────────────┘  │
└───────┬─────────────────────────────────┬───────────────┘
        │ HTTP POST                       │ WebSocket
        │ /api/send-command               │ /ws/game-events
        ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│  Node.js IM 服务 │              │   前端页面       │
│   端口: 3001     │              │   (Vue 3)       │
│  ┌───────────┐  │              │  ┌───────────┐  │
│  │ • 维持 IM  │  │              │  │ • 实时显示 │  │
│  │   长连接   │  │              │  │   游戏状态 │  │
│  │ • 接收指令 │  │              │  │ • 事件配置 │  │
│  │   请求     │  │              │  │ • 日志监控 │  │
│  │ • 发送 IM  │  │              │  └───────────┘  │
│  │   消息     │  │              └─────────────────┘
│  └───────────┘  │
└────────┬────────┘
         │ Tencent Cloud IM SDK
         │ C2C 消息
         ▼
┌─────────────────┐
│   腾讯云 IM      │
│   (即时通讯)     │
└────────┬────────┘
         │ IM 消息推送
         ▼
┌─────────────────┐
│   YCY 设备端     │
│  (接收并执行)    │
└─────────────────┘
```

### 工作流程

1. **CS2 游戏** 通过 GSI (Game State Integration) 接口实时发送游戏状态到 Python 后端
2. **Python 后端** 解析游戏状态，检测事件触发条件（如受伤、死亡、闪光等）
3. **触发指令** 当事件触发时，后端调用 Node.js IM 服务的 HTTP API 发送指令
4. **IM 服务处理** Node.js IM 服务通过腾讯云 IM SDK 将指令发送到 YCY 设备
5. **设备响应** YCY 设备接收 IM 消息并执行相应动作
6. **实时通知** 后端通过 WebSocket 实时通知前端游戏事件和状态变化
7. **前端展示** 前端实时显示游戏状态、事件日志和 IM 连接状态

---

## 🚀 快速开始

### 前置要求

- Python 3.8 或更高版本
- Node.js 16 或更高版本
- Counter-Strike 2 游戏

### 开发环境运行

#### 步骤 1: 克隆项目

```bash
git clone https://github.com/tzwgoo/CS2-YCY-Link.git
cd CS2-YCY-Link
```

#### 步骤 2: 安装依赖

**IM 服务依赖**
```bash
cd im-service
npm install
```

**后端依赖**
```bash
cd backend
pip install -r requirements.txt
```

**前端依赖**
```bash
cd frontend
npm install
```

#### 步骤 3: 启动服务

**方式 1: 使用启动器（推荐）**
```bash
python launcher-portable.py
```

**方式 2: 手动启动各服务**

1. 启动 IM 服务：
```bash
cd im-service
node server.js
```

2. 启动后端服务：
```bash
cd backend
python main_server.py
```

3. 启动前端开发服务器：
```bash
cd frontend
npm run dev
```

#### 步骤 4: 配置 IM 连接

1. 在浏览器中打开 `http://localhost:8001`
2. 在控制面板点击 **"配置 UID/Token"** 按钮
3. 输入你的凭证：
   - **UID**: 输入不带 `game_` 前缀的 UID（例如：`5`）
   - **Token**: 从游戏链接中获取的 Token
4. 点击 **"确定"**，系统将自动连接腾讯云 IM

#### 步骤 5: 配置 CS2 GSI

在 CS2 游戏配置目录创建 GSI 配置文件：

**文件路径：**
```
Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\gamestate_integration_ycy.cfg
```

**文件内容：**
```cfg
"YCY IM Integration"
{
    "uri" "http://localhost:8001/api/cs2-event"
    "timeout" "5.0"
    "buffer" "0.1"
    "throttle" "0.1"
    "heartbeat" "30.0"
    "data"
    {
        "provider" "1"
        "map" "1"
        "round" "1"
        "player_id" "1"
        "player_state" "1"
        "player_weapons" "1"
        "player_match_stats" "1"
    }
}
```

#### 步骤 6: 开始游戏

启动 CS2 游戏，系统将自动开始监听游戏事件并发送指令！

---

## 📦 打包部署

### 打包成可执行文件

项目支持打包成独立的可执行文件，无需安装 Python 和 Node.js 环境。

#### 步骤 1: 构建前端

```bash
cd frontend
npm run build
```

构建产物将生成在 `frontend/dist` 目录。

#### 步骤 2: 复制前端文件到后端

```bash
# Windows
xcopy /E /I frontend\dist backend\frontend

# Linux/Mac
cp -r frontend/dist backend/frontend
```

#### 步骤 3: 打包后端

```bash
cd backend
pyinstaller build.spec
```

打包后的文件在 `backend/dist/backend.exe`。

#### 步骤 4: 打包 IM 服务

**方式 1: 使用 pkg（推荐）**

```bash
cd im-service
npm install -g pkg
pkg server.js --targets node18-win-x64 --output im-service.exe
```

**方式 2: 使用便携版 Node.js**

1. 下载 Node.js 便携版：https://nodejs.org/dist/v18.19.0/node-v18.19.0-win-x64.zip
2. 解压后将 `node.exe` 复制到 `im-service` 目录

#### 步骤 5: 组织发布文件

创建发布目录结构：

```
release/
├── backend.exe           # 后端可执行文件
├── launcher-portable.py  # Python 启动器
├── im-service/
│   ├── server.js
│   ├── node.exe         # 便携版 Node.js
│   ├── package.json
│   └── node_modules/
└── frontend/            # 前端静态文件（已包含在 backend.exe 中）
    ├── index.html
    └── assets/
```

#### 步骤 6: 使用打包后的程序

双击运行 `launcher-portable.py` 或 `launcher.exe`，程序会自动：
1. 检查必要文件
2. 启动 IM 服务（端口 3001）
3. 启动后端服务（端口 8001）
4. 打开浏览器访问控制面板

### 自动化打包脚本

项目提供了自动化打包脚本 `build.bat`：

```bash
# Windows
build.bat

# 脚本会自动完成：
# 1. 构建前端
# 2. 复制前端文件
# 3. 打包后端
# 4. 组织发布文件
```

---

## ✨ 功能特性

### 游戏事件支持

| 事件类型 | 触发条件 | 说明 |
|---------|---------|------|
| 🩸 玩家受伤 | 血量减少 | 玩家受到任何伤害时触发 |
| 💀 玩家死亡 | 血量归零 | 玩家死亡时触发 |
| 💥 闪光弹致盲 | 闪光值 > 0 | 被闪光弹致盲时触发 |
| 💨 烟雾弹影响 | 烟雾值 > 0 | 进入烟雾区域时触发 |
| 🔥 燃烧伤害 | 燃烧值 > 0 | 被火焰燃烧时触发 |
| 🏁 回合结束 | 回合阶段变化 | 回合结束时触发 |

### 核心功能

- ✅ **可视化配置界面** - 无需编码，在 Web 界面配置所有设置
- ✅ **实时游戏监控** - 实时显示玩家血量、状态等信息
- ✅ **IM 连接管理** - 可视化的连接状态和配置管理
- ✅ **指令日志记录** - 完整的指令发送历史和状态追踪
- ✅ **自定义事件** - 支持创建自定义游戏事件和指令
- ✅ **事件启用/禁用** - 灵活控制哪些事件需要触发
- ✅ **WebSocket 实时通信** - 毫秒级的事件响应速度

---

## 🛠️ 技术栈

### IM 服务技术
- **Node.js 18+** - JavaScript 运行时
- **Express.js** - Web 应用框架
- **@tencentcloud/chat** - 腾讯云 IM SDK
- **WebSocket (ws)** - WebSocket 库

### 后端技术
- **Python 3.8+** - 主要编程语言
- **FastAPI** - 高性能 Web 框架
- **WebSocket** - 实时双向通信
- **aiohttp** - 异步 HTTP 客户端
- **PyInstaller** - Python 打包工具

### 前端技术
- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **Ant Design Vue** - 企业级 UI 组件库
- **Axios** - HTTP 客户端
- **Tencent Cloud Chat SDK** - 腾讯云 IM SDK

---

## 🎮 页面功能

### 1. 事件配置页面
- 查看和管理所有游戏事件
- 启用/禁用特定事件
- 编辑事件触发条件
- 配置事件对应的指令
- 创建自定义事件

### 2. 游戏监控页面
- 实时显示游戏状态
- 监控玩家血量和状态
- 查看事件触发历史
- 实时数据可视化

### 3. IM 连接页面
- 配置 UID 和 Token
- 测试 IM 连接状态
- 查看连接详细信息
- 实时指令发送日志
- WebSocket 连接状态

---

## ❓ 常见问题

<details>
<summary><b>Q: IM 连接失败怎么办？</b></summary>

**A:** 请检查以下几点：
1. UID 和 Token 是否正确
2. 网络连接是否正常
3. Token 是否已过期
4. 浏览器控制台是否有错误信息

如果问题持续，请查看浏览器开发者工具的 Console 和 Network 标签页。
</details>

<details>
<summary><b>Q: 游戏事件没有触发怎么办？</b></summary>

**A:** 请按以下步骤排查：
1. 确认 CS2 GSI 配置文件已正确创建
2. 检查后端服务是否正常运行（`http://localhost:8001`）
3. 确认前端 WebSocket 已连接（查看 IM 连接页面）
4. 检查事件配置是否已启用
5. 查看后端控制台是否有错误日志
</details>

<details>
<summary><b>Q: 指令没有发送到设备怎么办？</b></summary>

**A:** 请确认：
1. IM 连接状态为"已连接"
2. 事件配置中的指令内容正确
3. 查看 IM 连接页面的指令日志
4. 确认 YCY 设备端在线并能接收消息
</details>

<details>
<summary><b>Q: 如何自定义事件？</b></summary>

**A:** 在事件配置页面：
1. 点击"新建事件"按钮
2. 填写事件 ID、名称和描述
3. 选择触发条件类型
4. 添加动作（发送指令）
5. 输入指令内容
6. 保存配置
</details>

<details>
<summary><b>Q: 打包后的程序无法启动怎么办？</b></summary>

**A:** 请检查：
1. 确保所有必要文件都在发布目录中
2. 检查是否有杀毒软件拦截
3. 查看是否有端口占用（3001、8001）
4. 查看启动器的错误提示信息
5. 尝试以管理员权限运行
</details>

<details>
<summary><b>Q: 前端访问不到后端 API 怎么办？</b></summary>

**A:** 这个问题已经修复：
1. 确保后端运行在端口 8001
2. 浏览器访问 `http://localhost:8001`
3. 检查后端控制台是否有错误
4. 确认防火墙没有阻止端口 8001
</details>

---

## 📝 指令格式说明

所有发送到 YCY IM 的指令遵循以下格式：

```json
{
  "code": "game_cmd",
  "id": "指令内容",
  "token": "你的Token"
}
```

**字段说明：**
- `code`: 固定为 `"game_cmd"`，标识这是游戏指令
- `id`: 指令内容，在事件配置中设置（如 `player_hurt`）
- `token`: 自动附加，用于身份验证

---

## 🔧 开发指南

### 前端开发

```bash
cd frontend
npm run dev
```

访问 `http://localhost:3000` 查看开发服务器（开发模式下使用代理访问后端）

### 前端构建

```bash
cd frontend
npm run build
```

构建产物将生成在 `frontend/dist` 目录

### 后端开发

```bash
cd backend
python main_server.py
```

API 文档访问 `http://localhost:8001/docs`

### IM 服务开发

```bash
cd im-service
node server.js
```

服务运行在 `http://localhost:3001`

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [CS2监听配置指南](./CS2监听配置指南.md) | CS2 GSI 配置详细说明 |
| [IM集成说明](./IM集成说明.md) | YCY IM 集成技术文档 |
| [IM 接入说明](./docs/IM_basic.md) | 腾讯云 IM 接入详细文档 |
| [IM 服务文档](./im-service/README.md) | Node.js IM 服务技术文档 |

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 报告问题

如果你发现了 bug 或有功能建议，请：
1. 在 [Issues](https://github.com/yourusername/CS2-YCY-Link/issues) 页面创建新 issue
2. 详细描述问题或建议
3. 如果是 bug，请提供复现步骤

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 🙏 致谢

- [腾讯云 IM](https://cloud.tencent.com/product/im) - 提供即时通讯服务
- [FastAPI](https://fastapi.tiangolo.com/) - 优秀的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Ant Design Vue](https://antdv.com/) - 企业级 UI 组件库

---

<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐️**

Made with ❤️ by CS2-YCY-Link Team

</div>
