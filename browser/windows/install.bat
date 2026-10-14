@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title PiriMU - ติดตั้ง
echo.
echo   =============================================
echo     PiriMU  เว็บบราวเซอร์สำหรับสายมู
echo     โดย ดร.วศิน ภิรมย์  -  pirimu.com
echo   =============================================
echo.

set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if not defined PY goto nopython

echo [1/3] กำลังสร้างพื้นที่ติดตั้ง...
%PY% -m venv .venv
if errorlevel 1 goto fail

echo [2/3] กำลังดาวน์โหลดเครื่องยนต์เบราว์เซอร์ (ประมาณ 150-250 MB รอสักครู่นะครับ)...
".venv\Scripts\python.exe" -m pip install --upgrade pip --disable-pip-version-check -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 goto fail

echo [3/3] กำลังสร้างไอคอน PiriMU บนหน้าจอ (Desktop)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=[Environment]::GetFolderPath('Desktop'); $w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut((Join-Path $d 'PiriMU.lnk')); $s.TargetPath=(Join-Path (Get-Location) '.venv\Scripts\pythonw.exe'); $s.Arguments='pirimu.py'; $s.WorkingDirectory=(Get-Location).Path; $s.IconLocation=(Join-Path (Get-Location) 'icon.ico'); $s.Description='PiriMU web browser'; $s.Save()"

echo.
echo   ติดตั้งเสร็จแล้ว! ดับเบิลคลิกไอคอน PiriMU บน Desktop เพื่อเปิดใช้งาน
echo   (หรือดับเบิลคลิก run.bat ในโฟลเดอร์นี้)
echo.
echo   ห้ามลบหรือย้ายโฟลเดอร์นี้ เพราะโปรแกรมอยู่ในโฟลเดอร์นี้
echo.
start "" ".venv\Scripts\pythonw.exe" "pirimu.py"
pause
exit /b 0

:nopython
echo   ยังไม่พบ Python ในเครื่องครับ
echo   1) ติดตั้ง Python 3.12 จาก https://www.python.org/downloads/
echo   2) ตอนติดตั้ง ติ๊กช่อง "Add python.exe to PATH" ด้วย
echo   3) แล้วดับเบิลคลิก install.bat อีกครั้ง
echo.
start "" "https://www.python.org/downloads/"
pause
exit /b 1

:fail
echo.
echo   ติดตั้งไม่สำเร็จ ลองตรวจสอบอินเทอร์เน็ต แล้วดับเบิลคลิก install.bat อีกครั้ง
echo   ถ้ายังไม่ได้ แจ้งปัญหาได้ที่ ดร.วศิน ภิรมย์ Line OA: @wasin
pause
exit /b 1
