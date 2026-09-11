@echo off
rem Church String Arranger - 서버 시작 스크립트
cd /d "%~dp0backend"
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python이 PATH에 없습니다.
  pause
  exit /b 1
)
pip install -r requirements.txt -q 2>nul
echo.
echo ============================================
echo   Church String Arranger 서버 시작 중...
echo   접속 주소: http://127.0.0.1:8000
echo   (종료하려면 이 창에서 Ctrl+C)
echo ============================================
echo.
python run.py
pause
