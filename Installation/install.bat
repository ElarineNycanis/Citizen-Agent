@echo off
chcp 65001 >nul
title CitizenAgent 安装向导

echo.
echo ================================================
echo       CitizenAgent 一键安装向导
echo ================================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 建议以管理员身份运行此脚本
    echo     右键 install.bat → 以管理员身份运行
    echo.
)

:: 检查 Python
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [-] 未检测到 Python！
    echo.
    echo 请先安装 Python：
    echo   1. 打开 https://www.python.org/downloads/
    echo   2. 下载最新版 Python（点黄色按钮）
    echo   3. 安装时务必勾选 "Add Python to PATH"
    echo   4. 安装完成后重新运行本脚本
    echo.
    pause
    exit /b 1
)
python --version
echo [+] Python 环境正常
echo.

:: 检查 pip
echo [2/4] 检查 pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [-] pip 不可用，正在修复...
    python -m ensurepip --upgrade
)
echo [+] pip 正常
echo.

:: 安装依赖
echo [3/4] 安装依赖包...
python -m pip install requests --quiet
if %errorlevel% neq 0 (
    echo [-] requests 安装失败，请检查网络连接
    pause
    exit /b 1
)
echo [+] requests 已安装

:: 可选：prompt_toolkit
echo [*] 安装可选依赖 prompt_toolkit（更好看的输入框）...
python -m pip install prompt_toolkit --quiet 2>nul
if %errorlevel% equ 0 (
    echo [+] prompt_toolkit 已安装
) else (
    echo [!] prompt_toolkit 安装失败（不影响使用，输入框会降级为简易模式）
)
echo.

:: 配置文件
echo [4/4] 配置文件...
set "CONFIG_PATH=%USERPROFILE%\CitizenAgentConfig.json"

if exist "%CONFIG_PATH%" (
    echo [*] 配置文件已存在: %CONFIG_PATH%
    echo [*] 跳过配置创建
) else (
    if exist "config.example.json" (
        copy "config.example.json" "%CONFIG_PATH%" >nul
        echo [+] 已创建配置文件: %CONFIG_PATH%
    ) else (
        echo [-] 未找到 config.example.json，将创建最小配置...
        (
            echo {
            echo   "models": {
            echo     "main": {
            echo       "base_url": "https://api.deepseek.com",
            echo       "model": "deepseek-chat",
            echo       "api_key": "在此填入你的 API Key"
            echo     }
            echo   },
            echo   "ai_name": "林清墨",
            echo   "parallel_enabled": true
            echo }
        ) > "%CONFIG_PATH%"
        echo [+] 已创建最小配置文件
    )
)

echo.
echo ================================================
echo       安装完成！
echo ================================================
echo.
echo 配置文件位置: %CONFIG_PATH%
echo.
echo 【重要】接下来需要填入 API Key：
echo.
echo   如果你已经有 API Key：
echo     1. 运行: notepad %CONFIG_PATH%
echo     2. 把 "api_key" 后面替换成你的 Key
echo.
echo   如果还没有 API Key：
echo     打开 安装指导\API_KEY_SETUP.md 查看获取教程
echo.
echo 配置完成后，双击 CitizenAgent.bat 即可启动！
echo.
pause
