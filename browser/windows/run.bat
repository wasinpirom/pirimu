@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo ยังไม่ได้ติดตั้ง กรุณาดับเบิลคลิก install.bat ก่อน
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "pirimu.py"
