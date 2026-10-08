# OpenClaw Gateway watchdog (v3)
# Runs every 5 minutes. If port 18789 is NOT listening:
#   - normal case: re-issue start (SYSTEM task, then .vbs fallback)
#   - zombie case (down 3 consecutive checks ~15min with gateway process alive): force-end then restart
# Safe by design: a slow-but-healthy startup (observed ~6.6min) is NOT killed, because
# force-cleanup only happens after 3 consecutive down detections.
$log  = 'C:\Users\orisi\.openclaw\backup\gateway-watchdog.log'
$state = 'C:\Users\orisi\.openclaw\backup\gateway-watchdog-state.txt'
$port = 18789

function W($m) { Add-Content $log ("{0} - {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) }
function IsListening { [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) }
function GatewayProcs {
    @(Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'openclaw' -and $_.CommandLine -match 'gateway' })
}

try {
    if (IsListening) {
        # healthy -> reset the down counter
        if (Test-Path $state) { Set-Content -Path $state -Value "0" -Encoding ascii }
        exit 0
    }

    # --- read / update consecutive-down counter ---
    $count = 0
    if (Test-Path $state) {
        $raw = (Get-Content $state -Raw -ErrorAction SilentlyContinue)
        if ($raw -match '^\s*(\d+)\s*$') { $count = [int]$Matches[1] }
    }
    $count = $count + 1
    Set-Content -Path $state -Value "$count" -Encoding ascii

    $procs = GatewayProcs
    $pids = ($procs | ForEach-Object { $_.ProcessId }) -join ','
    W ("gateway down (check #$count) - listening=false, gateway processes=$($procs.Count) pids=$pids")

    # --- zombie handling: only after 3 consecutive down checks ---
    if ($count -ge 3 -and $procs.Count -gt 0) {
        W "zombie detected -> force end task and kill remaining gateway node processes"
        & schtasks /End /TN "OpenClaw Gateway" 2>$null | Out-Null
        Start-Sleep -Seconds 3
        foreach ($p in (GatewayProcs)) {
            try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop; W ("killed pid " + $p.ProcessId) } catch { W ("kill failed pid " + $p.ProcessId) }
        }
        Start-Sleep -Seconds 3
    }

    # --- restart: SYSTEM task first, .vbs fallback ---
    & schtasks /Run /TN "OpenClaw Gateway" 2>$null | Out-Null
    Start-Sleep -Seconds 6
    if (-not (IsListening)) {
        Start-Process wscript.exe -ArgumentList '"C:\Users\orisi\.openclaw\gateway.vbs"' -WindowStyle Hidden
        Start-Sleep -Seconds 5
    }

    if (IsListening) { W "restart issued -> listening OK" }
    else { W "restart issued -> still not listening (SYSTEM task + vbs fallback)" }
} catch {
    try { W ("watchdog error: " + $_.Exception.Message) } catch {}
}
