import asyncio
import json
import sys
import os
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import aiohttp
from pathlib import Path


def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和 PyInstaller 打包环境"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        base_path = Path(sys.executable).parent
    else:
        # 开发环境 - backend/app.py 的父目录的父目录是项目根目录
        base_path = Path(__file__).parent.parent
    return base_path / relative_path


app = FastAPI(title="CS2 Event Trigger System")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
event_configs: Dict[str, dict] = {}
current_game_state = {
    "health": 100,
    "is_alive": True,
    "flashed": 0,
    "smoked": 0,
    "burning": 0,
    "round_phase": "unknown",
    "map_phase": "unknown"
}


class EventConfig(BaseModel):
    event_name: str
    enabled: bool
    trigger_condition: dict
    actions: List[dict]
    description: Optional[str] = ""


class CommandConfig(BaseModel):
    command_type: str  # pulse, strength_set, strength_increase, strength_decrease
    channel: str  # A, B, or Both
    data: dict


@app.on_event("startup")
async def startup_event():
    # 加载配置
    load_event_configs()


def load_event_configs():
    """从文件加载事件配置"""
    global event_configs
    try:
        config_path = get_resource_path("event_configs.json")
        with open(config_path, "r", encoding="utf-8") as f:
            event_configs = json.load(f)
    except FileNotFoundError:
        # 初始化默认配置
        event_configs = {
            "player_hurt": {
                "event_name": "玩家受伤",
                "enabled": True,
                "trigger_condition": {
                    "type": "health_decrease",
                    "min_damage": 1
                },
                "actions": [
                    {
                        "type": "send_command",
                        "command": "player_hurt",
                        "params": {
                            "damage_amount": "calculated"
                        }
                    }
                ],
                "description": "玩家血量减少时发送指令"
            },
            "player_death": {
                "event_name": "玩家死亡",
                "enabled": True,
                "trigger_condition": {
                    "type": "health_zero"
                },
                "actions": [
                    {
                        "type": "send_command",
                        "command": "player_death",
                        "params": {}
                    }
                ],
                "description": "玩家死亡时发送指令"
            },
            "player_flashed": {
                "event_name": "闪光弹致盲",
                "enabled": True,
                "trigger_condition": {
                    "type": "flashed",
                    "min_value": 1
                },
                "actions": [
                    {
                        "type": "send_command",
                        "command": "player_flashed",
                        "params": {}
                    }
                ],
                "description": "被闪光弹致盲时发送指令"
            },
            "player_smoked": {
                "event_name": "烟雾弹影响",
                "enabled": True,
                "trigger_condition": {
                    "type": "smoked",
                    "min_value": 1
                },
                "actions": [
                    {
                        "type": "send_command",
                        "command": "player_smoked",
                        "params": {}
                    }
                ],
                "description": "在烟雾中时发送指令"
            },
            "player_burning": {
                "event_name": "燃烧伤害",
                "enabled": True,
                "trigger_condition": {
                    "type": "burning",
                    "min_value": 1
                },
                "actions": [
                    {
                        "type": "send_command",
                        "command": "player_burning",
                        "params": {}
                    }
                ],
                "description": "被火焰燃烧时发送指令"
            },
            "round_end": {
                "event_name": "回合结束",
                "enabled": True,
                "trigger_condition": {
                    "type": "round_phase",
                    "value": "over"
                },
                "actions": [
                    {
                        "type": "send_command",
                        "command": "round_end",
                        "params": {}
                    }
                ],
                "description": "回合结束时发送指令"
            }
        }
        save_event_configs()


def save_event_configs():
    """保存事件配置到文件"""
    config_path = get_resource_path("event_configs.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(event_configs, f, ensure_ascii=False, indent=2)


@app.get("/api/events")
async def get_events():
    """获取所有事件配置"""
    return {"events": event_configs}


@app.get("/api/events/{event_id}")
async def get_event(event_id: str):
    """获取单个事件配置"""
    if event_id in event_configs:
        return event_configs[event_id]
    return {"error": "Event not found"}, 404


@app.post("/api/events/{event_id}")
async def update_event(event_id: str, config: dict):
    """更新事件配置"""
    event_configs[event_id] = config
    save_event_configs()
    return {"success": True, "event": config}


@app.delete("/api/events/{event_id}")
async def delete_event(event_id: str):
    """删除事件配置"""
    if event_id in event_configs:
        del event_configs[event_id]
        save_event_configs()
        return {"success": True}
    return {"error": "Event not found"}, 404


@app.post("/api/events")
async def create_event(config: dict):
    """创建新事件配置"""
    event_id = config.get("event_id", f"custom_{len(event_configs)}")
    event_configs[event_id] = config
    save_event_configs()
    return {"success": True, "event_id": event_id, "event": config}


@app.get("/api/game-state")
async def get_game_state():
    """获取当前游戏状态"""
    return current_game_state




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


async def check_and_trigger_events(old_state: dict, new_state: dict):
    """检查并触发符合条件的事件"""
    for event_id, config in event_configs.items():
        if not config.get("enabled", False):
            continue

        trigger = config.get("trigger_condition", {})
        trigger_type = trigger.get("type")

        # 检查触发条件
        should_trigger = False

        if trigger_type == "health_decrease":
            if new_state["health"] < old_state["health"]:
                min_damage = trigger.get("min_damage", 1)
                if old_state["health"] - new_state["health"] >= min_damage:
                    should_trigger = True

        elif trigger_type == "health_zero":
            if new_state["health"] == 0 and old_state["health"] > 0:
                should_trigger = True

        elif trigger_type == "flashed":
            if new_state["flashed"] > 0 and old_state["flashed"] == 0:
                should_trigger = True

        elif trigger_type == "smoked":
            if new_state["smoked"] > 0 and old_state["smoked"] == 0:
                should_trigger = True

        elif trigger_type == "burning":
            if new_state["burning"] > 0:
                should_trigger = True

        elif trigger_type == "round_phase":
            target_phase = trigger.get("value")
            if new_state["round_phase"] == target_phase and old_state["round_phase"] != target_phase:
                should_trigger = True

        # 触发事件动作 - 通知前端
        if should_trigger:
            await execute_event_actions(config.get("actions", []), old_state, new_state)
            # 通知前端发生了事件
            await notify_frontend_event(event_id, {
                "old_state": old_state,
                "new_state": new_state
            })


async def execute_event_actions(actions: List[dict], old_state: dict, new_state: dict):
    """执行事件动作 - 调用 Node.js IM 服务发送指令"""
    for action in actions:
        action_type = action.get("type")

        if action_type == "send_command":
            # 获取指令内容
            command_id = action.get("command", "")

            # 调用 Node.js IM 服务发送指令
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        'http://localhost:3001/api/send-command',
                        json={'commandId': command_id},
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        result = await response.json()
                        if result.get('success'):
                            print(f"✓ 指令发送成功: {command_id}")
                        else:
                            print(f"✗ 指令发送失败: {command_id} - {result.get('message')}")
            except Exception as e:
                print(f"✗ 调用 IM 服务失败: {e}")


async def notify_frontend_event(event_id: str, event_data: dict = None):
    """通知前端发生了游戏事件"""
    if not game_event_connections:
        return

    message_data = {
        "type": "game_event",
        "event_id": event_id,
        "data": event_data or {},
        "timestamp": datetime.now().isoformat()
    }

    # 向所有连接的前端发送事件通知
    disconnected = []
    for ws in game_event_connections:
        try:
            await ws.send_json(message_data)
            print(f"✓ 已通知前端事件: {event_id}")
        except Exception as e:
            print(f"发送事件通知失败: {e}")
            disconnected.append(ws)

    # 清理断开的连接
    for ws in disconnected:
        if ws in game_event_connections:
            game_event_connections.remove(ws)


@app.websocket("/ws/game-state")
async def websocket_game_state(websocket: WebSocket):
    """WebSocket连接，实时推送游戏状态"""
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "type": "game_state",
                "data": current_game_state,
                "timestamp": datetime.now().isoformat()
            })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print("WebSocket disconnected")


# 游戏事件 WebSocket 连接管理
game_event_connections: List[WebSocket] = []


@app.websocket("/ws/game-events")
async def websocket_game_events(websocket: WebSocket):
    """WebSocket连接，实时推送游戏事件到前端"""
    await websocket.accept()
    game_event_connections.append(websocket)
    print(f"前端已连接 WebSocket，当前连接数: {len(game_event_connections)}")

    try:
        while True:
            # 保持连接，接收前端的心跳消息
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        game_event_connections.remove(websocket)
        print(f"前端断开 WebSocket，当前连接数: {len(game_event_connections)}")


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# 前端静态文件服务
frontend_path = get_resource_path("frontend")

# 挂载 assets 目录
if (frontend_path / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")


@app.get("/")
async def serve_index():
    """返回前端首页"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "Frontend not found"}


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """处理 SPA 路由，返回静态文件或 index.html"""
    # 排除 API 路径（让 API 路由返回 404）
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")

    # 尝试返回静态文件
    file_path = frontend_path / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # 否则返回 index.html（用于 Vue Router 的客户端路由）
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
