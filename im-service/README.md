# CS2 IM Service

Node.js IM 服务，负责连接腾讯云 IM 并发送游戏指令。

## 功能

- 自动连接腾讯云 IM
- 提供 HTTP API 接口供 Python 后端调用
- 自动重连机制
- 健康检查端点

## 安装

```bash
cd im-service
npm install
```

## 启动

```bash
npm start
```

开发模式（自动重启）：
```bash
npm run dev
```

## API 接口

### 健康检查

```
GET /health
```

响应：
```json
{
  "status": "ok",
  "imReady": true,
  "uid": "game_5",
  "userId": "5"
}
```

### 获取状态

```
GET /api/status
```

响应：
```json
{
  "isReady": true,
  "config": {
    "uid": "game_5",
    "userId": "5",
    "appId": "1400853470",
    "hasToken": true,
    "hasSign": true
  }
}
```

### 发送指令

```
POST /api/send-command
Content-Type: application/json

{
  "commandId": "player_hurt"
}
```

响应：
```json
{
  "success": true,
  "message": "指令发送成功",
  "data": { ... }
}
```

### 重新初始化

```
POST /api/reinit
```

响应：
```json
{
  "success": true,
  "message": "IM 重新初始化成功"
}
```

## 日志

服务会输出详细的日志信息：

```
[2024-12-15T10:30:00.000Z] [INFO] 正在初始化 IM 客户端...
[2024-12-15T10:30:01.000Z] [INFO] 已加载配置: UID=game_5, UserID=5
[2024-12-15T10:30:02.000Z] [INFO] ✓ 获取 IM 签名成功
[2024-12-15T10:30:03.000Z] [INFO] 正在登录 IM...
[2024-12-15T10:30:04.000Z] [INFO] ✓ IM SDK 就绪
[2024-12-15T10:30:04.000Z] [INFO] ✓ IM 客户端初始化成功
[2024-12-15T10:30:04.000Z] [INFO] ============================================================
[2024-12-15T10:30:04.000Z] [INFO] CS2 IM 服务已启动
[2024-12-15T10:30:04.000Z] [INFO] HTTP 服务: http://localhost:3001
[2024-12-15T10:30:04.000Z] [INFO] ============================================================
```

## 错误处理

- **IM 未就绪**: 返回 503 状态码
- **缺少参数**: 返回 400 状态码
- **发送失败**: 返回 500 状态码，包含错误信息

## 自动重连

当 IM 连接断开时，服务会自动尝试重连：

- 被踢下线：5秒后自动重连
- 网络异常：自动检测并重连

## 心跳机制

服务每 30 秒输出一次心跳日志，确认 IM 连接状态。

## 优雅退出

按 `Ctrl+C` 退出时，服务会：
1. 登出 IM
2. 销毁 IM 实例
3. 关闭 HTTP 服务器

## 故障排查

### IM 初始化失败

1. 检查 `state.json` 文件是否存在
2. 确认 UID 和 Token 是否正确
3. 检查网络连接

### 指令发送失败

1. 确认 IM 状态为 `isReady: true`
2. 检查目标用户 ID 是否正确
3. 查看服务日志获取详细错误信息

### 端口冲突

如果 3001 端口被占用，修改 `server.js` 中的 `PORT` 常量。

## 技术栈

- Node.js 18+
- Express.js
- @tencentcloud/chat
- WebSocket (ws)
