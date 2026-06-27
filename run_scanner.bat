@echo off
REM Simple batch script to run the scanner with Telegram integration
REM Usage: double-click this file or run from command prompt

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if credentials are set
if "%TELEGRAM_BOT_TOKEN%"=="" (
    echo.
    echo ⚠️  Telegram credentials not configured!
    echo.
    echo To set up Telegram integration:
    echo 1. Create a bot: Message @BotFather on Telegram and use /newbot
    echo 2. Get your chat ID: Message @userinfobot
    echo.
    echo Then set environment variables in Windows:
    echo   setx TELEGRAM_BOT_TOKEN "your_bot_token"
    echo   setx TELEGRAM_CHAT_ID "your_chat_id"
    echo.
    echo Or set them temporarily (this command prompt only):
    echo   set TELEGRAM_BOT_TOKEN=your_bot_token
    echo   set TELEGRAM_CHAT_ID=your_chat_id
    echo.
    echo Running scanner without Telegram...
    echo.
    pause
)

REM Run the scanner
python run_scanner_with_telegram.py
pause
