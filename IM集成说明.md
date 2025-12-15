# YCY IM 集成说明（基于腾讯云 IM）

## 概述

根据 `docs/IM_basic.md` 文档，YCY 系统使用**腾讯云即时通讯（IM）**作为消息中转通道。

### 架构演进

**v1.0.1 更新（2025-12-16）**：

架构从后端集中发送改为前端直接发送，提升安全性和响应速度：

```
旧架构（已废弃）：
[CS2 游戏] → [Python 后端] → [Node.js IM 服务] → [腾讯 IM] → [YCY 设备端]

新架构（当前）：
[CS2 游戏] → [Python 后端] → [WebSocket 通知] → [前端] → [腾讯 IM SDK] → [YCY 设备端]
```

**架构优势**：
- ✅ **更安全**：Token 仅在前端存储，不经过后端
- ✅ **更快速**：前端直接发送，减少一次 HTTP 调用
- ✅ **更可靠**：前端可以实时显示 IM 连接状态
- ✅ **更灵活**：前端可以缓存和重试发送失败的消息

### 通信架构

```
[CS2 游戏] → [本系统] → [腾讯 IM] → [YCY 设备端]
```

## 核心流程

### 1. 获取鉴权信息

调用 `/user/game_sign` 接口获取：

**请求：**
```json
POST https://suo.jiushu1234.com/api.php/user/game_sign
{
  "uid": "game_5",
  "token": "your_token"
}
```

**响应：**
```json
{
  "code": 1,
  "msg": "ok",
  "data": {
    "appid": "1400853470",
    "sign": "eJwtzEELgjAYxvHvsnPoXm0LhS4iIlGHSj0JMdqUl1pNXRJE372lHp-fH54PKfZnb1Q9iUngUbKaNkr1sNjgxK3Q6sIorGGpg7wJY1CSGDilFHjE2FzU22CvnDPGApdmtaj-tuHAwxCiaHnB1p3ncAJe5e296XRqB9wVqUy6Z1LJ2h*Frv2ueR2zPivL4nDdku8PSzkzfg__"
  }
}
```

### 2. 初始化腾讯 IM SDK

```javascript
// JavaScript 示例
let chat = $TC.create({
  SDKAppID: appid // 从上一步获取
});

// 登录 IM
chat.login({
  userID: 'game_5',  // 必须与 uid 一致
  userSig: sign      // 从上一步获取
});
```

### 3. 发送指令消息

```javascript
// 创建文本消息
let message = chat.createTextMessage({
  to: "5",  // 目标用户ID（不带 game_ 前缀）
  conversationType: $TC.TYPES.CONV_C2C,
  payload: {
    text: JSON.stringify({
      code: 'game_cmd',
      id: "player_hurt",
      token: 'your_token'
    })
  }
});

// 发送消息
chat.sendMessage(message);
```

## Python 实现说明

### 当前实现

由于 Python 环境限制，当前实现分为两个阶段：

#### 阶段 1：获取签名（已实现）

```python
async def request_game_sign(self) -> bool:
    """调用 /user/game_sign 获取 appid 和 sign"""
    url = f"{self.api_base}/user/game_sign"
    payload = {
        "uid": self.uid,      # 格式: game_5
        "token": self.token
    }

    async with self.session.post(url, json=payload) as response:
        result = await response.json()
        if result.get("code") == 1:
            self.appid = result["data"]["appid"]
            self.sign = result["data"]["sign"]
            return True
    return False
```

#### 阶段 2：发送消息（待实现）

目前只是记录日志，实际需要集成腾讯 IM SDK 或使用 REST API。

### UID 格式处理

**标准输入格式：** 用户输入不带 `game_` 前缀的 UID

系统会自动添加前缀：

```python
# 标准情况：用户输入 "5"
raw_uid = "5"
self.user_id = "5"           # 用于发送消息的 to 字段
self.uid = "game_5"          # 用于登录 IM

# 兼容情况：用户输入 "game_5"（系统会移除后重新添加）
raw_uid = "game_5"
self.user_id = "5"           # 移除 game_ 前缀
self.uid = "game_5"          # 重新添加前缀
```

**代码实现：**
```python
if raw_uid.startswith("game_"):
    # 移除前缀后重新添加（确保格式统一）
    self.user_id = raw_uid.replace("game_", "")
    self.uid = f"game_{self.user_id}"
else:
    # 标准情况：直接添加前缀
    self.user_id = raw_uid
    self.uid = f"game_{raw_uid}"
```

## 消息格式

### 标准格式

```json
{
  "code": "game_cmd",
  "id": "player_hurt",
  "token": "your_token"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | String | 固定为 `"game_cmd"` |
| `id` | String | 指令内容 |
| `token` | String | 用于消息验证 |

## 配置说明

### state.json

```json
{
  "uid": "5",           // 输入不带 game_ 前缀的 UID
  "token": "your_token"
}
```

**重要：** 用户输入的 UID 不带 `game_` 前缀，系统会自动添加。

**示例：**
- 用户输入：`5`
- 系统处理：`uid = "game_5"`, `user_id = "5"`

### 前端配置

在"IM 连接"页面配置：
- **UID**：输入不带前缀的数字或字符串（如 `5`），系统会自动添加 `game_` 前缀
- **Token**：从游戏链接中获取

**配置示例：**
```
UID: 5
Token: OWs4sZtTP056b9b7fa21752b173e8c1139c1baac5d4
```

系统会自动处理为：
```
登录 IM: userID = "game_5"
发送消息: to = "5"
```

## 完整集成方案

### 方案 A：使用腾讯 IM REST API（推荐）

使用腾讯云 IM 的 REST API 发送单聊消息。

**优点：**
- 不需要安装 SDK
- 纯 HTTP 调用
- 易于集成

**实现：**
```python
async def send_im_message(self, to_user: str, message: dict):
    """使用腾讯 IM REST API 发送消息"""
    # 参考文档：https://cloud.tencent.com/document/product/269/2282

    url = f"https://console.tim.qq.com/v4/openim/sendmsg"
    params = {
        "sdkappid": self.appid,
        "identifier": self.uid,
        "usersig": self.sign,
        "random": random.randint(0, 4294967295),
        "contenttype": "json"
    }

    payload = {
        "SyncOtherMachine": 1,
        "To_Account": to_user,
        "MsgLifeTime": 60,
        "MsgRandom": random.randint(0, 4294967295),
        "MsgTimeStamp": int(time.time()),
        "MsgBody": [{
            "MsgType": "TIMTextElem",
            "MsgContent": {
                "Text": json.dumps(message)
            }
        }]
    }

    async with self.session.post(url, params=params, json=payload) as response:
        result = await response.json()
        return result.get("ActionStatus") == "OK"
```

### 方案 B：使用 Node.js 桥接

创建一个 Node.js 服务，使用腾讯 IM SDK 发送消息。

**优点：**
- 使用官方 SDK
- 功能完整
- 稳定可靠

**架构：**
```
Python 后端 → HTTP → Node.js 服务 → 腾讯 IM SDK → YCY 设备
```

### 方案 C：使用 WebSocket（demo 方案）

参考 `demo/ycy_im_demo.ts`，使用 WebSocket 连接腾讯 IM。

**优点：**
- 实时双向通信
- 可以接收消息

**缺点：**
- Python 实现复杂
- 需要维护连接

## 当前状态

### 已实现（v1.0.1）

✅ **前端直接连接 IM** - Token 仅在前端存储，不经过后端
✅ **加载 UID 和 Token** - 从前端配置读取
✅ **调用 `/user/game_sign` 获取签名** - 前端直接调用
✅ **UID 格式自动处理** - 系统自动添加/移除 `game_` 前缀
✅ **消息格式构造** - 前端构造标准消息格式
✅ **命令队列处理** - 前端缓存未发送的消息
✅ **实时状态显示** - 前端显示 IM 连接状态和日志

### 实现位置

**前端 IM 客户端**：`frontend/src/utils/imClient.js`

**核心功能**：
- `connect(uid, token)` - 连接腾讯云 IM
- `sendCommand(commandId)` - 发送游戏指令
- `getStatus()` - 获取连接状态
- 自动重连和消息队列管理

**使用示例**：
```javascript
import imClient from '@/utils/imClient'

// 连接 IM
const result = await imClient.connect('5', 'your_token')

// 发送指令
const result = await imClient.sendCommand('player_hurt')

// 获取状态
const status = imClient.getStatus()
```

### 已废弃（旧架构）

❌ **Node.js IM 服务桥接** - 已不再需要，前端直接发送
❌ **后端 HTTP 调用 IM 服务** - 已移除，减少中间环节

### 架构对比

**旧架构（复杂）**：
```
游戏事件 → Python 后端 → HTTP 调用 → Node.js 服务 → 腾讯 IM → 设备
```

**新架构（简洁）**：
```
游戏事件 → Python 后端 → WebSocket → 前端 → 腾讯 IM SDK → 设备
```

**优势**：
- 减少一次 HTTP 调用，延迟降低
- Token 不经过后端，安全性提升
- 前端可以实时显示发送状态
- 消息队列管理更灵活

## 测试步骤

### 1. 配置凭证

在前端页面配置：
- UID: `5` (或 `game_5`)
- Token: 从游戏链接获取

### 2. 启动系统

```bash
cd backend
python main_server.py
```

### 3. 查看日志

后端会输出：
```
正在初始化 YCY IM 客户端...
已加载 state.json: UID=game_5, UserID=5
正在请求 IM 签名: https://suo.jiushu1234.com/api.php/user/game_sign
✓ 获取 IM 签名成功
✓ YCY IM 客户端初始化成功 (UID: game_5)
  AppID: 1400853470
  UserID: 5
```

### 4. 触发游戏事件

启动 CS2 游戏，触发事件后查看日志：
```
处理游戏指令: player_hurt
准备发送指令: {"code":"game_cmd","id":"player_hurt","token":"xxx"}
✓ 指令已准备发送
```

## 注意事项

### 1. UID 格式

- **登录使用**：`userID = game_5`
- **消息发送**：`to = "5"`（不带 game_ 前缀）

### 2. Token 有效性

Token 从游戏链接中获取，过期或伪造将导致签名获取失败。

### 3. Code 固定值

所有控制消息必须使用 `code: "game_cmd"`，否则设备不响应。

### 4. 消息格式

消息内容必须是 JSON 字符串，放在 `payload.text` 字段中。

## 下一步工作

### 优先级 1：实现消息发送

选择方案 A（REST API）或方案 B（Node.js 桥接）实现实际的消息发送功能。

### 优先级 2：错误处理

- 签名过期自动刷新
- 消息发送失败重试
- 连接断开自动重连

### 优先级 3：消息接收

如果需要接收设备端的反馈，需要实现消息接收功能。

## 参考资料

- [腾讯云 IM 文档](https://cloud.tencent.com/document/product/269)
- [REST API 文档](https://cloud.tencent.com/document/product/269/1519)
- [单聊消息 API](https://cloud.tencent.com/document/product/269/2282)
- `docs/IM_basic.md` - YCY IM 接入说明
- `demo/ycy_im_demo.ts` - TypeScript 示例代码

---

**版本：** v2.3.0
**更新日期：** 2024-12-15
**作者：** Claude Code
