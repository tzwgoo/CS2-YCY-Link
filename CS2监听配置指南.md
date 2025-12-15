# CS2 游戏状态监听配置指南

## 📖 什么是 Game State Integration (GSI)

CS2 的 Game State Integration 是 Valve 提供的官方功能，允许游戏实时向外部应用发送游戏状态数据。

### 工作原理

```
┌─────────────┐                    ┌─────────────┐
│   CS2 游戏   │  ──── HTTP POST ──>│  你的后端    │
│             │   JSON 数据         │  (FastAPI)  │
└─────────────┘                    └─────────────┘
```

1. CS2 游戏读取 cfg 配置文件
2. 游戏运行时，定期向配置的 URL 发送 HTTP POST 请求
3. 请求体包含当前游戏状态的 JSON 数据
4. 你的后端接收并处理这些数据

---

## 📁 配置文件位置

### Windows 系统

```
Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\
```

**完整路径示例**:
```
C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\
```

### 如何找到这个目录

#### 方法 1: 通过 Steam 客户端

1. 打开 Steam
2. 右键点击 Counter-Strike 2
3. 选择 "管理" → "浏览本地文件"
4. 进入 `game\csgo\cfg\` 目录

#### 方法 2: 手动查找

1. 打开文件资源管理器
2. 导航到你的 Steam 安装目录
3. 进入 `steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\`

---

## 📝 配置文件内容

### 文件名

```
gamestate_integration_ycy.cfg
```

**重要**:
- 文件名必须以 `gamestate_integration_` 开头
- 后面可以是任意名称（如 `ycy`）
- 扩展名必须是 `.cfg`

### 文件内容

创建文件并填入以下内容：

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

### 配置参数说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `uri` | 后端接收数据的 URL | `http://localhost:8001/api/cs2-event` |
| `timeout` | 请求超时时间（秒） | `5.0` |
| `buffer` | 数据缓冲时间（秒） | `0.1` |
| `throttle` | 数据发送间隔（秒） | `0.1` |
| `heartbeat` | 心跳间隔（秒） | `30.0` |

### 数据类型说明

| 数据类型 | 说明 | 是否必需 |
|---------|------|---------|
| `provider` | 游戏提供者信息 | 是 |
| `map` | 地图信息 | 是 |
| `round` | 回合信息 | 是 |
| `player_id` | 玩家 ID | 是 |
| `player_state` | 玩家状态（血量、护甲等） | **是（核心）** |
| `player_weapons` | 玩家武器信息 | 可选 |
| `player_match_stats` | 玩家比赛统计 | 可选 |

---

## 🔧 后端接收实现

### 后端 API 端点

在 `backend/app.py` 中已经实现：

```python
@app.post("/api/cs2-event")
async def handle_cs2_event(data: dict):
    """处理CS2游戏状态更新"""
    global current_game_state

    try:
        if "player" not in data or "map" not in data:
            return {"status": "error", "message": "Invalid data format"}

        # 检查是否是本地玩家
        if data["provider"]["steamid"] != data["player"]["steamid"]:
            return {"status": "ignored", "message": "Not local player"}

        # 更新游戏状态
        player_state = data["player"]["state"]
        new_health = player_state["health"]
        new_flashed = player_state.get("flashed", 0)
        new_smoked = player_state.get("smoked", 0)
        new_burning = player_state.get("burning", 0)

        # 检查并触发事件
        await check_and_trigger_events(
            old_state=current_game_state,
            new_state={
                "health": new_health,
                "is_alive": new_health > 0,
                "flashed": new_flashed,
                "smoked": new_smoked,
                "burning": new_burning,
                "round_phase": data.get("round", {}).get("phase", "unknown"),
                "map_phase": data.get("map", {}).get("phase", "unknown")
            }
        )

        # 更新当前状态
        current_game_state.update({
            "health": new_health,
            "is_alive": new_health > 0,
            "flashed": new_flashed,
            "smoked": new_smoked,
            "burning": new_burning,
            "round_phase": data.get("round", {}).get("phase", "unknown"),
            "map_phase": data.get("map", {}).get("phase", "unknown")
        })

        return {"status": "success", "message": "Event processed"}

    except Exception as e:
        print(f"Error processing CS2 event: {e}")
        return {"status": "error", "message": str(e)}
```

### 接收的数据格式

CS2 发送的 JSON 数据示例：

```json
{
  "provider": {
    "name": "Counter-Strike: Global Offensive",
    "appid": 730,
    "version": 13960,
    "steamid": "76561198012345678",
    "timestamp": 1702648800
  },
  "map": {
    "mode": "competitive",
    "name": "de_dust2",
    "phase": "live",
    "round": 5,
    "team_ct": {
      "score": 2
    },
    "team_t": {
      "score": 3
    }
  },
  "round": {
    "phase": "live",
    "bomb": "planted"
  },
  "player": {
    "steamid": "76561198012345678",
    "name": "Player",
    "team": "CT",
    "state": {
      "health": 85,
      "armor": 100,
      "helmet": true,
      "flashed": 0,
      "smoked": 0,
      "burning": 0,
      "money": 4500,
      "round_kills": 1,
      "round_killhs": 0
    },
    "weapons": {
      "weapon_0": {
        "name": "weapon_ak47",
        "paintkit": "default",
        "type": "Rifle",
        "state": "active",
        "ammo_clip": 30,
        "ammo_clip_max": 30,
        "ammo_reserve": 90
      }
    }
  }
}
```

---

## 🧪 测试配置

### 1. 创建配置文件

1. 找到 CS2 cfg 目录
2. 创建 `gamestate_integration_ycy.cfg`
3. 复制上面的配置内容
4. 保存文件

### 2. 启动后端服务

```bash
cd backend
python main_server.py
```

确认后端在 `http://localhost:8001` 运行。

### 3. 启动 CS2 游戏

1. 启动 Counter-Strike 2
2. 进入任意游戏模式（竞技、休闲、死亡竞赛等）
3. 观察后端控制台

### 4. 验证连接

**后端应该显示**:
```
收到 CS2 事件数据
玩家血量: 100
玩家状态: 存活
```

**前端控制面板应该显示**:
- 游戏状态实时更新
- 血量条变化
- 状态效果显示

---

## 🔍 故障排查

### 问题 1: 后端没有收到数据

**检查项**:
1. ✅ cfg 文件是否在正确的目录
2. ✅ cfg 文件名是否以 `gamestate_integration_` 开头
3. ✅ URI 是否正确（`http://localhost:8001/api/cs2-event`）
4. ✅ 后端服务是否正在运行
5. ✅ 防火墙是否阻止了连接
6. ✅ CS2 游戏是否已重启（配置文件在游戏启动时读取）

### 问题 2: 收到数据但事件不触发

**检查项**:
1. ✅ 事件配置是否已启用
2. ✅ 触发条件是否正确
3. ✅ 查看后端控制台的日志输出
4. ✅ 检查 IM 服务是否正常运行

### 问题 3: 数据发送频率太高

**解决方法**:
- 增加 `throttle` 值（如 `0.5` 或 `1.0`）
- 增加 `buffer` 值

### 问题 4: 只想监听特定数据

**解决方法**:
在 cfg 文件中只启用需要的数据类型：

```cfg
"data"
{
    "provider" "1"
    "player_state" "1"
}
```

---

## 📊 数据更新频率

| 场景 | 更新频率 |
|------|---------|
| 玩家受伤 | 立即 |
| 血量变化 | 立即 |
| 状态效果 | 立即 |
| 回合阶段 | 阶段切换时 |
| 心跳 | 每 30 秒 |

---

## 🎯 高级配置

### 远程服务器配置

如果后端不在本机：

```cfg
"uri" "http://192.168.1.100:8001/api/cs2-event"
```

### 多个监听器

可以创建多个配置文件：

```
gamestate_integration_ycy.cfg
gamestate_integration_stats.cfg
gamestate_integration_overlay.cfg
```

每个文件可以配置不同的 URI 和数据类型。

### 安全配置

如果使用公网 IP，建议：

1. 使用 HTTPS
2. 添加身份验证
3. 限制 IP 访问

---

## 📚 参考资料

- [Valve GSI 官方文档](https://developer.valvesoftware.com/wiki/Counter-Strike:_Global_Offensive_Game_State_Integration)

---

## ✅ 配置检查清单

配置完成后，检查以下项目：

- [ ] cfg 文件已创建在正确的目录
- [ ] cfg 文件名以 `gamestate_integration_` 开头
- [ ] URI 指向正确的后端地址
- [ ] 后端服务正在运行
- [ ] CS2 游戏已重启
- [ ] 后端控制台显示收到数据
- [ ] 前端控制面板显示游戏状态
- [ ] 事件触发正常工作

---

**配置完成后，开始享受游戏与设备的实时联动吧！** 🎮
