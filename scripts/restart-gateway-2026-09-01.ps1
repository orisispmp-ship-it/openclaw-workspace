$log = 'C:\Users\orisi\.openclaw\backup\gateway-restart-2026-09-01.log'
"=== restart start $(Get-Date) ===" | Out-File $log -Encoding utf8

# 1. 기존 게이트웨이 종료 (orisi 소유이므로 가능)
$gw = Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -like '*openclaw*' }
foreach ($p in $gw) {
    "killing PID $($p.ProcessId): $($p.CommandLine.Substring(0, [Math]::Min(100, $p.CommandLine.Length)))" | Out-File $log -Append -Encoding utf8
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}

# 2. 포트 18789 해제 대기 (최대 30초)
$portFree = $false
for ($i = 0; $i -lt 15; $i++) {
    if (-not (Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue)) { $portFree = $true; break }
    Start-Sleep -Seconds 2
}
"port free: $portFree" | Out-File $log -Append -Encoding utf8

# 3. 새 버전으로 게이트웨이 시작 (기존과 동일한 메커니즘: .vbs -> gateway.cmd, orisi 컨텍스트 유지)
Start-Process wscript.exe -ArgumentList '"C:\Users\orisi\.openclaw\gateway.vbs"'
"start issued via gateway.vbs" | Out-File $log -Append -Encoding utf8

# 4. 포트 수신 대기 (최대 60초)
$up = $false
for ($i = 0; $i -lt 30; $i++) {
    if (Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue) { $up = $true; break }
    Start-Sleep -Seconds 2
}
"gateway listening: $up" | Out-File $log -Append -Encoding utf8

# 5. 잠금 해제된 스테이징 잔재 정리
Start-Sleep -Seconds 3
Remove-Item -Recurse -Force 'C:\Users\orisi\AppData\Roaming\npm\node_modules\.openclaw-89X79CDN' -ErrorAction SilentlyContinue
"staging dir removed: $(-not (Test-Path 'C:\Users\orisi\AppData\Roaming\npm\node_modules\.openclaw-89X79CDN'))" | Out-File $log -Append -Encoding utf8

"=== restart end $(Get-Date) ===" | Out-File $log -Append -Encoding utf8
