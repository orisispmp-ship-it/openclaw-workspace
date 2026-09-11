@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  =^> PDF Compressor 실행 중...
echo  =^> http://127.0.0.1:5000
echo  =^> 브라우저가 열리지 않으면 위 주소로 직접 접속하세요.
echo  =^> 종료: Ctrl+C
echo.
start http://127.0.0.1:5000
python app.py
pause
