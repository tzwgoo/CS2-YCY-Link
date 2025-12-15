@echo off
chcp 65001 >nul
echo ============================================================
echo CS2-YCY-Link 便携版打包脚本
echo ============================================================
echo.
echo 此脚本将创建不依赖 pkg 的便携版
echo Node.js 将以原生方式运行
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python
    pause
    exit /b 1
)

echo 工具检查完成
echo.

REM 清理旧文件
echo 清理旧文件...
if exist release rmdir /s /q release
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
echo 清理完成
echo.

REM 1. 构建前端
echo [1/5] 构建前端...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo 前端构建失败
    cd ..
    pause
    exit /b 1
)
cd ..
echo 前端构建完成
echo.

REM 2. 打包 Python 后端
echo [2/5] 打包 Python 后端...
cd backend
python -m PyInstaller build.spec
if %errorlevel% neq 0 (
    echo 后端打包失败
    cd ..
    pause
    exit /b 1
)
cd ..
echo 后端打包完成
echo.

REM 3. 准备 IM 服务（不打包，原生运行）
echo [3/5] 准备 IM 服务...
mkdir release
mkdir release\im-service
mkdir release\frontend

REM 复制 IM 服务文件
copy im-service\server.js release\im-service\
copy im-service\package.json release\im-service\

REM 复制 node_modules
echo 复制 node_modules...
xcopy /E /I /Y im-service\node_modules release\im-service\node_modules

echo IM 服务准备完成
echo.

REM 4. 打包启动器
echo [4/5] 打包启动器...
python -m PyInstaller --onefile --console --name "CS2-YCY-Link" launcher-portable.py
if %errorlevel% neq 0 (
    echo 启动器打包失败
    pause
    exit /b 1
)
echo 启动器打包完成
echo.

REM 5. 组织文件
echo [5/5] 组织文件...

REM 复制可执行文件
copy dist\CS2-YCY-Link.exe release\
copy backend\dist\backend.exe release\

REM 复制前端文件
xcopy /E /I /Y frontend\dist release\frontend

REM 创建 README
(
echo CS2-YCY-Link 使用说明（便携版）
echo ====================================
echo.
echo 重要: 首次使用需要配置 Node.js
echo.
echo 方式 1: 使用便携版 Node.js（推荐）
echo   1. 下载 Node.js 便携版:
echo      https://nodejs.org/dist/v18.19.0/node-v18.19.0-win-x64.zip
echo   2. 解压后将 node.exe 复制到 im-service 目录
echo.
echo 方式 2: 安装 Node.js
echo   1. 访问 https://nodejs.org/
echo   2. 下载并安装 Node.js
echo.
echo 配置完成后:
echo   1. 将 state.json.example 重命名为 state.json
echo   2. 编辑 state.json，填入你的 UID 和 Token
echo   3. 双击 CS2-YCY-Link.exe 启动
echo.
echo 配置 CS2 GSI:
echo   - 将 gamestate_integration_ycy.cfg 复制到 CS2 cfg 目录
echo   - 路径: Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\
echo.
echo 停止程序:
echo   - 在启动器窗口按 Ctrl+C
echo   - 或直接关闭所有窗口
) > release\README.txt

REM 复制 GSI 配置文件
if exist gamestate_integration_ycy.cfg (
    copy gamestate_integration_ycy.cfg release\
)

echo 文件组织完成
echo.

echo ============================================================
echo 打包完成！
echo ============================================================
echo.
echo 发布文件位于: release\
echo.
echo 重要提示:
echo 1. 需要下载 Node.js 便携版
echo    https://nodejs.org/dist/v18.19.0/node-v18.19.0-win-x64.zip
echo.
echo 2. 解压后将 node.exe 复制到 release\im-service\ 目录
echo.
echo 3. 或者用户可以安装 Node.js 到系统
echo.
echo 包含文件:
dir /b release
echo.
pause
