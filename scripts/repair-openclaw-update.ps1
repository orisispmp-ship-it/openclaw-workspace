$ErrorActionPreference = 'Continue'
$log = 'C:\Users\orisi\.openclaw\backup\update-repair-2026-09-01.log'
$pkg = 'C:\Users\orisi\AppData\Roaming\npm\node_modules\openclaw'
"=== repair start $(Get-Date) ===" | Out-File $log -Encoding utf8

# 1. 게이트웨이 중지 (SYSTEM 태스크)
schtasks /End /TN "OpenClaw Gateway" *>> $log
Start-Sleep -Seconds 4
$task = schtasks /Query /TN "OpenClaw Gateway" /FO CSV 2>$null | ConvertFrom-Csv
"TASK STATE AFTER END: $($task.Status)" | Out-File $log -Append -Encoding utf8

# 2. 포트 18789 해제 대기 (최대 40초)
$portFree = $false
for ($i = 0; $i -lt 20; $i++) {
    $conn = Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue
    if (-not $conn) { $portFree = $true; break }
    Start-Sleep -Seconds 2
}
"PORT 18789 FREE: $portFree" | Out-File $log -Append -Encoding utf8
if (-not $portFree) {
    "ABORT: port still in use" | Out-File $log -Append -Encoding utf8
    exit 1
}

# 3. 구버전 패키지 삭제 (잠금 해제된 상태)
Remove-Item -Recurse -Force $pkg -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
"PKG REMOVED: $(-not (Test-Path $pkg))" | Out-File $log -Append -Encoding utf8
if (Test-Path $pkg) {
    "ABORT: package dir still exists" | Out-File $log -Append -Encoding utf8
    exit 1
}

# 4. 신버전 재설치
npm install -g openclaw@latest *>> $log
"NPM INSTALL EXIT: $LASTEXITCODE" | Out-File $log -Append -Encoding utf8

# 5. 버전 확인
openclaw --version *>> $log
"VERSION EXIT: $LASTEXITCODE" | Out-File $log -Append -Encoding utf8

# 6. 게이트웨이 재시작
schtasks /Run /TN "OpenClaw Gateway" *>> $log
"TASK RUN ISSUED: $LASTEXITCODE" | Out-File $log -Append -Encoding utf8
Start-Sleep -Seconds 8
$task2 = schtasks /Query /TN "OpenClaw Gateway" /FO CSV 2>$null | ConvertFrom-Csv
"TASK STATE AFTER RUN: $($task2.Status)" | Out-File $log -Append -Encoding utf8

"=== repair end $(Get-Date) ===" | Out-File $log -Append -Encoding utf8
