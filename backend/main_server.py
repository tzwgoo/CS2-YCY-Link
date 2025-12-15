import socket

import uvicorn

from app import app as fastapi_app


def get_ip_address():
    """获取本机IP地址"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except:
        ip_address = "127.0.0.1"
    finally:
        s.close()
    return ip_address


def main():
    """主函数"""
    print("=" * 60)
    print("CS2-YCY-Link 控制面板启动中...")
    print("=" * 60)
    print()
    print("架构说明:")
    print("- 后端: 监听 CS2 游戏事件，通过 WebSocket 通知前端")
    print("- 前端: 接收游戏事件通知，直接连接腾讯云 IM 发送指令")
    print()
    print("=" * 60)

    ip = get_ip_address()
    print(f"FastAPI 服务器启动: http://{ip}:8001")
    print(f"API 文档: http://{ip}:8001/docs")
    print()
    print("请在前端页面配置 UID 和 Token 以连接 IM")
    print("=" * 60)

    # 启动 FastAPI
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已退出")
