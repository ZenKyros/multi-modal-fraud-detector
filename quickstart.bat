@echo off
REM Quick Start Script for Multi-Modal Fraud Detector (Windows)

echo ===================================
echo Multi-Modal Fraud Detector
echo Quick Start Setup (Windows)
echo ===================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo OK: %PYTHON_VERSION%
echo.

REM Check Node
echo [2/5] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 18+
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo OK: %NODE_VERSION%
echo.

REM Backend setup
echo [3/5] Setting up backend...
cd backend

REM Create virtual environment
python -m venv venv

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
pip install -q -r ..\requirements.txt

echo OK: Backend dependencies installed
cd ..
echo.

REM Frontend setup
echo [4/5] Setting up frontend...
cd frontend
call npm install -q
echo OK: Frontend dependencies installed
cd ..
echo.

REM Configuration
echo [5/5] Configuration Check
echo Please ensure you have:
echo   - GROQ_API_KEY set in backend\.env
echo   - GEMINI_API_KEY set in backend\.env
echo.

echo OK: Setup complete!
echo.
echo Next steps:
echo   1. Update backend\.env with your API keys
echo   2. Start backend: cd backend ^& python -m uvicorn main:app --reload
echo   3. Start frontend: cd frontend ^& npm run dev
echo   4. Open http://localhost:5173 in your browser
echo.
pause
