# OpenClaw Gateway watchdog (v2 - SYSTEM 작업 우선)
# 5분마다 실행: 포트 18789가 LISTENING이 아니면 SYSTEM 예약 작업으로 재기동, 실패 시 .vbs 폴백
$log = 'C:\Users\orisi\.openclaw\backup\gateway-watchdog.log'
try {
    $listening = Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue
    if (-not $listening) {
        schtasks /Run /TN "OpenClaw Gateway" 2>$null | Out-Null
        Start-Sleep -Seconds 4
        if (-not (Get-NetTCPConnection -LocalPort 18789 -State Listen -ErrorAction SilentlyContinue)) {
            Start-Process wscript.exe -ArgumentList '"C:\Users\orisi\.openclaw\gateway.vbs"' -WindowStyle Hidden
        }
        Add-Content $log ("{0} - gateway down -> restart issued (SYSTEM task, fallback vbs)" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
    }
} catch {
    try { Add-Content $log ("{0} - watchdog error: {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $_.Exception.Message) } catch {}
}
