# SYSTEM 상시 실행 모드 전환 스크립트 (관리자 권한으로 실행됨)
$ErrorActionPreference = 'Continue'
$log = 'C:\Users\orisi\.openclaw\backup\system-mode-setup.log'
"=== start $(Get-Date) ===" | Out-File $log -Encoding utf8

# 1) SYSTEM 게이트웨이 예약 작업 등록 (8/26 XML 재사용)
schtasks /create /f /tn "OpenClaw Gateway" /xml "C:\Users\orisi\.openclaw\gateway-service-task.xml" *>> $log
"TASK CREATE EXIT: $LASTEXITCODE" | Out-File $log -Append -Encoding utf8

# 2) GitHub 자격증명을 SYSTEM GCM에 등록
$tmp = Join-Path $env:TEMP ("gw-cred-" + [guid]::NewGuid().ToString("N") + ".txt")
"protocol=https`nhost=github.com`n`n" | git credential fill 2>$null | Out-File $tmp -Encoding ascii
$importPath = Join-Path $env:TEMP ("gw-import-" + [guid]::NewGuid().ToString("N") + ".ps1")
$import = @"
`$ErrorActionPreference = 'Continue'
`$log = 'C:\Users\orisi\.openclaw\backup\system-mode-setup.log'
try {
    Get-Content '$tmp' -Raw | git credential-manager store
    Add-Content `$log ("{0} - cred store ok" -f (Get-Date -Format 'HH:mm:ss'))
} catch {
    Add-Content `$log ("{0} - cred store FAIL: {1}" -f (Get-Date -Format 'HH:mm:ss'), `$_.Exception.Message)
}
try {
    `$out = git ls-remote https://github.com/orisispmp-ship-it/site-diary.git HEAD 2>&1
    Add-Content `$log ("{0} - ls-remote result: {1}" -f (Get-Date -Format 'HH:mm:ss'), (`$out | Select-Object -First 1))
} catch {
    Add-Content `$log ("{0} - ls-remote FAIL: {1}" -f (Get-Date -Format 'HH:mm:ss'), `$_.Exception.Message)
}
Remove-Item '$tmp' -Force -ErrorAction SilentlyContinue
"@
Set-Content $importPath $import -Encoding utf8

schtasks /create /f /tn "OpenClaw-Gateway-Cred-Setup" /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File $importPath" /sc once /st 23:59 /ru SYSTEM /rl HIGHEST *>> $log
schtasks /run /tn "OpenClaw-Gateway-Cred-Setup" *>> $log
Start-Sleep -Seconds 10
schtasks /delete /f /tn "OpenClaw-Gateway-Cred-Setup" *>> $log
Remove-Item $importPath -Force -ErrorAction SilentlyContinue

# 3) 현재(orisi) 게이트웨이 종료
$gw = Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like '*openclaw*' }
foreach ($p in $gw) {
    "killing PID $($p.ProcessId)" | Out-File $log -Append -Encoding utf8
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 4

# 4) 포트 해제 대기 (최대 30초)
for ($i = 0; $i -lt 15; $i++) {
    if (-not (Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue)) { break }
    Start-Sleep -Seconds 2
}
"PORT FREE: $(-not (Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue))" | Out-File $log -Append -Encoding utf8

# 5) SYSTEM 작업으로 게이트웨이 시작
schtasks /run /tn "OpenClaw Gateway" *>> $log
"TASK RUN EXIT: $LASTEXITCODE" | Out-File $log -Append -Encoding utf8

# 6) 포트 수신 대기 (최대 90초, 실패 시 1회 재시도)
$up = $false
for ($try = 0; $try -lt 2 -and -not $up; $try++) {
    for ($i = 0; $i -lt 15; $i++) {
        if (Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue) { $up = $true; break }
        Start-Sleep -Seconds 3
    }
    if (-not $up -and $try -eq 0) { schtasks /run /tn "OpenClaw Gateway" *>> $log }
}
"GATEWAY UP: $up" | Out-File $log -Append -Encoding utf8
$proc = Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like '*openclaw*' }
if ($proc) {
    try { $o = Invoke-CimMethod -InputObject $proc -MethodName GetOwner; "GW OWNER: $($o.Domain)\$($o.User)" | Out-File $log -Append -Encoding utf8 } catch {}
}
"=== end $(Get-Date) ===" | Out-File $log -Append -Encoding utf8
