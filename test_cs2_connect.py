"""
CS2 GSI 连接测试脚本
用于测试 CS2 游戏是否正确发送数据到后端
"""

from fastapi import FastAPI, Request
import uvicorn
import json
from datetime import datetime

app = FastAPI()

# 记录收到的数据
received_count = 0
last_data = None

@app.post("/api/cs2-event")
async def test_cs2_event(request: Request):
    """测试接收 CS2 数据"""
    global received_count, last_data

    try:
        data = await request.json()
        received_count += 1
        last_data = data

        # 打印关键信息
        print("\n" + "=" * 60)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 收到第 {received_count} 条数据")
        print("=" * 60)

        # 提供者信息
        if "provider" in data:
            provider = data["provider"]
            print(f"游戏: {provider.get('name', 'Unknown')}")
            print(f"Steam ID: {provider.get('steamid', 'Unknown')}")

        # 地图信息
        if "map" in data:
            map_data = data["map"]
            print(f"地图: {map_data.get('name', 'Unknown')}")
            print(f"模式: {map_data.get('mode', 'Unknown')}")
            print(f"阶段: {map_data.get('phase', 'Unknown')}")

        # 回合信息
        if "round" in data:
            round_data = data["round"]
            print(f"回合阶段: {round_data.get('phase', 'Unknown')}")

        # 玩家信息
        if "player" in data:
            player = data["player"]
            print(f"玩家: {player.get('name', 'Unknown')}")
            print(f"队伍: {player.get('team', 'Unknown')}")

            # 玩家状态
            if "state" in player:
                state = player["state"]
                print(f"\n玩家状态:")
                print(f"  血量: {state.get('health', 0)}")
                print(f"  护甲: {state.get('armor', 0)}")
                print(f"  金钱: {state.get('money', 0)}")
                print(f"  闪光: {state.get('flashed', 0)}")
                print(f"  烟雾: {state.get('smoked', 0)}")
                print(f"  燃烧: {state.get('burning', 0)}")

        print("=" * 60)

        return {"status": "success", "count": received_count}

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    """显示测试状态"""
    return {
        "status": "running",
        "received_count": received_count,
        "message": "CS2 GSI 测试服务器正在运行",
        "endpoint": "/api/cs2-event"
    }

@app.get("/status")
async def status():
    """获取详细状态"""
    return {
        "received_count": received_count,
        "last_data": last_data,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("=" * 60)
    print("CS2 GSI 连接测试服务器")
    print("=" * 60)
    print()
    print("服务器地址: http://localhost:8000")
    print("测试端点: http://localhost:8000/api/cs2-event")
    print("状态查询: http://localhost:8000/status")
    print()
    print("=" * 60)
    print()
    print("等待 CS2 发送数据...")
    print("请确保:")
    print("1. gamestate_integration_ycy.cfg 已放置在 CS2 cfg 目录")
    print("2. CS2 游戏已启动")
    print("3. 已进入游戏（任意模式）")
    print()
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        print(f"总共收到 {received_count} 条数据")
