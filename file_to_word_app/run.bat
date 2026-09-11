@echo off
echo 필요한 패키지를 설치합니다...
pip install pdf2docx python-docx pytesseract Pillow PyMuPDF 2>nul
echo 설치 완료!
python "%~dp0file_to_word.py"
pause
