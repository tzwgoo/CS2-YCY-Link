@echo off
chcp 65001 >nul
echo ============================================================
echo 后端简单打包脚本（排除 GUI 库）
echo ============================================================
echo.

REM 清理旧文件
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo 开始打包...
echo.

REM 使用命令行参数直接排除不需要的库
python -m PyInstaller ^
    --onefile ^
    --console ^
    --name backend ^
    --add-data "event_configs.json;." ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.loops ^
    --hidden-import uvicorn.loops.auto ^
    --hidden-import uvicorn.protocols ^
    --hidden-import uvicorn.protocols.http ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.protocols.websockets ^
    --hidden-import uvicorn.protocols.websockets.auto ^
    --hidden-import uvicorn.lifespan ^
    --hidden-import uvicorn.lifespan.on ^
    --hidden-import aiohttp ^
    --hidden-import aiohttp.client ^
    --hidden-import aiohttp.connector ^
    --exclude-module PyQt5 ^
    --exclude-module PyQt6 ^
    --exclude-module PySide2 ^
    --exclude-module PySide6 ^
    --exclude-module tkinter ^
    --exclude-module _tkinter ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module scipy ^
    --exclude-module PIL ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    --exclude-module notebook ^
    main_server.py

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo 打包成功！
    echo ============================================================
    echo.
    echo 输出文件: dist\backend.exe
    echo.
) else (
    echo.
    echo ============================================================
    echo 打包失败！
    echo ============================================================
    echo.
)

pause
