@echo off
echo.
echo ============================================
echo   MANANZE CRYPTO COMMAND CENTER
echo   The OS for a crypto researcher
echo ============================================
echo.
where python >nul 2>&1
if errorlevel 1 (
  echo Please tell MANANZE.
  echo Python was not found on PATH.
  exit /b 1
)
cd /d "%~dp0"
if not exist .venv (
  echo Creating .venv ...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
if exist .env.example if not exist .env copy .env.example .env >nul
echo Launching on http://localhost:8501 ...
streamlit run app.py --server.port 8501
