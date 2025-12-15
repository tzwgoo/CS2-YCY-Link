"""
CS2-YCY-Link 启动器（便携版）
支持 Node.js 原生运行方式
"""

import subprocess
import time
import sys
import os
import webbrowser
from pathlib import Path
import socket
import urllib.request
import json
import atexit
import signal

# Windows 特定的导入
if sys.platform == 'win32':
    import ctypes
    import ctypes.wintypes

def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def wait_for_backend_ready(max_wait=30):
    """等待后端服务完全启动"""
    print("等待后端服务就绪...")
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = urllib.request.urlopen('http://localhost:8001/api/health', timeout=1)
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get('status') == 'ok':
                    print("✓ 后端服务已就绪")
                    return True
        except:
            pass
        time.sleep(0.5)
    return False

# 全局进程引用
im_process = None
backend_process = None

def set_process_group():
    """在Windows上设置进程组，确保子进程随父进程退出"""
    if sys.platform == 'win32':
        try:
            # 获取当前进程句柄
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetCurrentProcess()
            # 创建新的进程组
            kernel32.SetConsoleCtrlHandler(None, False)
        except:
            pass

def cleanup_processes():
    """清理所有子进程"""
    global im_process, backend_process

    print("\n正在清理子进程...")

    if im_process is not None:
        try:
            print(f"  终止 IM 服务 (PID: {im_process.pid})")
            im_process.terminate()
            try:
                im_process.wait(timeout=3)
                print("  ✓ IM 服务已正常终止")
            except subprocess.TimeoutExpired:
                print("  ⚠ IM 服务未响应，强制终止...")
                im_process.kill()
                im_process.wait(timeout=2)
                print("  ✓ IM 服务已强制终止")
        except Exception as e:
            print(f"  ⚠ 终止 IM 服务时出错: {e}")
        finally:
            im_process = None

    if backend_process is not None:
        try:
            print(f"  终止后端服务 (PID: {backend_process.pid})")
            backend_process.terminate()
            try:
                backend_process.wait(timeout=3)
                print("  ✓ 后端服务已正常终止")
            except subprocess.TimeoutExpired:
                print("  ⚠ 后端服务未响应，强制终止...")
                backend_process.kill()
                backend_process.wait(timeout=2)
                print("  ✓ 后端服务已强制终止")
        except Exception as e:
            print(f"  ⚠ 终止后端服务时出错: {e}")
        finally:
            backend_process = None

    print("✓ 所有子进程已清理")

def signal_handler(signum, frame):
    """处理信号"""
    print("\n\n正在停止服务...")
    cleanup_processes()
    print("✓ 所有服务已停止")
    sys.exit(0)

def main():
    global im_process, backend_process

    # 设置进程组（Windows）
    set_process_group()

    # 注册清理函数
    atexit.register(cleanup_processes)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("CS2-YCY-Link 启动器")
    print("=" * 60)
    print()

    # 获取当前目录
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent

    # 检查必要文件
    backend_exe = base_dir / "backend.exe"
    im_service_dir = base_dir / "im-service"
    node_exe = im_service_dir / "node.exe"
    server_js = im_service_dir / "server.js"

    print("检查文件...")

    if not backend_exe.exists():
        print("❌ 错误: 找不到 backend.exe")
        print(f"   路径: {backend_exe}")
        input("\n按回车键退出...")
        sys.exit(1)

    # 检查 Node.js
    node_available = False
    if node_exe.exists():
        print("✓ 找到便携版 Node.js")
        node_cmd = str(node_exe)
        node_available = True
    else:
        # 尝试使用系统 Node.js
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ 找到系统 Node.js: {result.stdout.strip()}")
                node_cmd = "node"
                node_available = True
        except:
            pass

    if not node_available:
        print("❌ 错误: 找不到 Node.js")
        print()
        print("请选择以下方式之一:")
        print("1. 下载 Node.js 便携版:")
        print("   https://nodejs.org/dist/v18.19.0/node-v18.19.0-win-x64.zip")
        print("   解压后将 node.exe 复制到 im-service 目录")
        print()
        print("2. 安装 Node.js:")
        print("   https://nodejs.org/")
        print()
        input("按回车键退出...")
        sys.exit(1)

    if not server_js.exists():
        print("❌ 错误: 找不到 server.js")
        print(f"   路径: {server_js}")
        input("\n按回车键退出...")
        sys.exit(1)

    print("✓ 文件检查完成")
    print()

    # 启动 IM 服务
    print("[1/2] 启动 IM 服务...")
    try:
        # Windows: 使用 CREATE_NO_WINDOW 隐藏窗口，并创建新进程组
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        im_process = subprocess.Popen(
            [node_cmd, str(server_js)],
            cwd=str(im_service_dir),
            creationflags=creation_flags,
            startupinfo=startupinfo
        )
        print("✓ IM 服务已启动 (PID: {})".format(im_process.pid))
        time.sleep(3)
    except Exception as e:
        print(f"❌ 启动 IM 服务失败: {e}")
        input("\n按回车键退出...")
        sys.exit(1)

    # 启动后端服务
    print("[2/2] 启动后端服务...")
    try:
        # Windows: 使用 CREATE_NO_WINDOW 隐藏窗口，并创建新进程组
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        backend_process = subprocess.Popen(
            [str(backend_exe)],
            cwd=str(base_dir),
            creationflags=creation_flags,
            startupinfo=startupinfo
        )
        print("✓ 后端服务已启动 (PID: {})".format(backend_process.pid))

        # 等待后端服务完全就绪
        if not wait_for_backend_ready():
            print("❌ 后端服务启动超时")
            print("正在停止所有服务...")
            cleanup_processes()
            input("\n按回车键退出...")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 启动后端服务失败: {e}")
        print("正在停止 IM 服务...")
        cleanup_processes()
        input("\n按回车键退出...")
        sys.exit(1)

    print()
    print("=" * 60)
    print("✓ 所有服务已启动！")
    print("=" * 60)
    print()
    print("服务地址:")
    print("- IM 服务:  http://localhost:3001")
    print("- 控制面板: http://localhost:8001")
    print()
    print("重要提示:")
    print("- 首次使用请在控制面板配置 UID 和 Token")
    print("- 点击左侧的配置 'UID/Token'按钮")
    print()
    print("正在打开浏览器...")
    print()

    # 打开浏览器
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:8001")
        print("✓ 浏览器已打开")
    except Exception as e:
        print(f"⚠️  无法自动打开浏览器: {e}")
        print("   请手动访问: http://localhost:8001")

    print()
    print("=" * 60)
    print("提示:")
    print("- 按 Ctrl+C 停止所有服务")
    print("- 关闭此窗口也会停止所有服务")
    print("- 注意: 浏览器窗口需要手动关闭")
    print("=" * 60)
    print()

    try:
        # 等待进程
        while True:
            if im_process and im_process.poll() is not None:
                print("\n⚠️  IM 服务已停止")
                break
            if backend_process and backend_process.poll() is not None:
                print("\n⚠️  后端服务已停止")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n检测到 Ctrl+C...")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        # 确保清理进程
        cleanup_processes()

    print()
    input("按回车键退出...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        sys.exit(1)
