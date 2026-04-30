@echo off
setlocal enabledelayedexpansion

:: ======================================================================
:: 🔥 COSTPILOT AI - FIERY ARCTIC MIDNIGHT STARTUP SCRIPT 🔥
:: ======================================================================

title CostPilot AI - Dashboard Engine
cls

:: Define theme colors for the console (Windows 10+)
echo [91m======================================================================[0m
echo [91m      ⚡ COSTPILOT AI - FIERY ARCTIC MIDNIGHT EDITION ⚡[0m
echo [91m======================================================================[0m
echo.

:: 1. Environment Check
echo [96m[ℹ️][0m Checking environment...
if not exist .env (
    echo [91m[✖️][0m .env file not found! 
    if exist .env.example (
        echo [92m[✔][0m Creating .env from .env.example...
        copy .env.example .env > nul
        echo [93m[⚠️][0m PLEASE CONFIGURE YOUR AWS CREDENTIALS IN .env FIRST!
        notepad .env
    ) else (
        echo [91m[✖️][0m .env.example not found. Please create .env manually.
    )
    pause
    exit /b
)

:: 2. Initial Scan
echo.
echo [38;5;208m[🔍][0m Running Fiery Arctic Scan + AI Analysis...
python main.py --scan --ai

:: 3. Launch Dashboard
echo.
echo [38;5;208m[🖥️][0m Starting the Web Dashboard...
echo [96m[🌐][0m Your browser will open shortly at [97mhttp://127.0.0.1:5000[0m
echo [91m[🔥][0m Mode: Fiery Arctic Midnight Glassmorphism

:: Give the server a moment to spin up, then launch browser
timeout /t 3 /nobreak > nul
start "" "http://127.0.0.1:5000"

:: Run the dashboard with the specified port
python main.py --dashboard --port 5000

pause
