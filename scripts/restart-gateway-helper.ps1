# Restart OpenClaw Gateway - one-shot helper (runs outside the gateway process)
# ASCII only (avoids encoding issues when launched by Task Scheduler)
$log = 'C:\Users\orisi\.openclaw\workspace\backup\gateway-restart.log'
$dir = Split-Path $log -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
function W($m){ (((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) + ' ' + $m) | Out-File -FilePath $log -Append -Encoding utf8 }

W '=== restart helper start ==='
W ('user: ' + (whoami))

$out = & schtasks /End /TN "OpenClaw Gateway" 2>&1 | Out-String
W ('END -> ' + ($out -replace '\s+', ' ').Trim())

Start-Sleep -Seconds 5

$out2 = & schtasks /Run /TN "OpenClaw Gateway" 2>&1 | Out-String
W ('RUN -> ' + ($out2 -replace '\s+', ' ').Trim())

Start-Sleep -Seconds 3
W '=== restart helper done ==='

# best-effort self cleanup of the one-shot task
& schtasks /Delete /TN "OpenClaw Gateway Restart Helper" /F 2>&1 | Out-Null
