@echo off
REM MyTaskly MCP Server - Quick Installation Script
REM This script sets up the MCP server in one command

echo ============================================================
echo  MyTaskly MCP Server - Quick Installation
echo ============================================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
if exist venv (
    echo    - Virtual environment already exists, skipping
) else (
    python -m venv venv
    echo    - Virtual environment created
)

echo.
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/5] Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet fastmcp httpx pyjwt python-dotenv pydantic pydantic-settings

echo.
echo [4/5] Checking configuration...
if exist .env (
    echo    - Configuration file .env already exists
    echo    - WARNING: Please ensure JWT_SECRET_KEY matches your FastAPI server!
) else (
    echo    - Creating .env from template...
    copy .env.example .env >nul
    echo    - IMPORTANT: Edit .env and set JWT_SECRET_KEY!
)

echo.
echo [5/5] Running health check...
python -c "from src.config import settings; print(f'   - Server name: {settings.mcp_server_name}')"
python -c "from src.config import settings; print(f'   - FastAPI URL: {settings.fastapi_base_url}')"

echo.
echo ============================================================
echo  Installation Complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Edit .env and set JWT_SECRET_KEY to match FastAPI server
echo   2. Run: python -m src.server
echo   3. Test: python -m tests.manual_test
echo.
echo Documentation:
echo   - Quick start: QUICKSTART.md
echo   - Full docs: README.md
echo   - Integration: INTEGRATION_GUIDE.md
echo.
pause
