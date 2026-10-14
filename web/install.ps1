# PiriMU one-line installer for Windows
# ใช้งาน: เปิด PowerShell แล้ววาง   irm https://pirimu.com/install.ps1 | iex
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
$Base = 'https://pirimu.com'
$Dir  = Join-Path $env:LOCALAPPDATA 'PiriMU'

Write-Host ''
Write-Host '  PiriMU - เว็บบราวเซอร์สำหรับสายมู โดย ดร.วศิน ภิรมย์' -ForegroundColor Magenta
Write-Host '  กำลังติดตั้ง... (ครั้งแรกใช้เวลา 3-10 นาที)' -ForegroundColor Magenta
Write-Host ''

function Find-Python {
    $cands = @('py', 'python', (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
               (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'))
    foreach ($c in $cands) {
        try {
            $ok = & $c -c "import sys; print(sys.version_info >= (3, 9))" 2>$null
            if ($ok -eq 'True') { return $c }
        } catch {}
    }
    return $null
}

$py = Find-Python
if (-not $py) {
    Write-Host '[0/4] ไม่พบ Python กำลังติดตั้ง Python 3.12 ให้อัตโนมัติ...' -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements | Out-Host
        $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
        $py = Find-Python
    }
    if (-not $py) {
        Write-Host 'ติดตั้ง Python อัตโนมัติไม่สำเร็จ' -ForegroundColor Red
        Write-Host 'กรุณาติดตั้งจาก https://www.python.org/downloads/ (ติ๊ก Add python.exe to PATH) แล้ววางคำสั่งเดิมอีกครั้ง'
        Start-Process 'https://www.python.org/downloads/'
        return
    }
}

Write-Host '[1/4] กำลังดาวน์โหลด PiriMU...'
$zip = Join-Path $env:TEMP 'PiriMU-Windows.zip'
$tmp = Join-Path $env:TEMP 'PiriMU-extract'
Invoke-WebRequest "$Base/dl/windows-zip?src=cli" -OutFile $zip -UseBasicParsing
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Expand-Archive $zip -DestinationPath $tmp -Force
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
Copy-Item (Join-Path $tmp 'PiriMU-Windows\*') $Dir -Recurse -Force

Write-Host '[2/4] กำลังเตรียมพื้นที่ติดตั้ง...'
$venvPy = Join-Path $Dir '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPy)) { & $py -m venv (Join-Path $Dir '.venv') }

Write-Host '[3/4] กำลังดาวน์โหลดเครื่องยนต์เบราว์เซอร์ (ประมาณ 200 MB)...'
& $venvPy -m pip install --upgrade pip --disable-pip-version-check -q
& $venvPy -m pip install -r (Join-Path $Dir 'requirements.txt') --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { Write-Host 'ติดตั้งไม่สำเร็จ ลองวางคำสั่งเดิมอีกครั้ง หรือแจ้งปัญหาที่ ดร.วศิน ภิรมย์ Line OA: @wasin' -ForegroundColor Red; return }

Write-Host '[4/4] กำลังสร้างไอคอน PiriMU บน Desktop และ Start Menu...'
$w = New-Object -ComObject WScript.Shell
foreach ($folder in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {
    $s = $w.CreateShortcut((Join-Path $folder 'PiriMU.lnk'))
    $s.TargetPath = Join-Path $Dir '.venv\Scripts\pythonw.exe'
    $s.Arguments = 'pirimu.py'
    $s.WorkingDirectory = $Dir
    $s.IconLocation = Join-Path $Dir 'icon.ico'
    $s.Description = 'PiriMU web browser'
    $s.Save()
}

Write-Host ''
Write-Host '  ติดตั้งเสร็จแล้ว! เปิด PiriMU ได้จากไอคอนบน Desktop หรือ Start Menu' -ForegroundColor Green
Write-Host ''
Start-Process (Join-Path $Dir '.venv\Scripts\pythonw.exe') -ArgumentList 'pirimu.py' -WorkingDirectory $Dir
