schtasks /End /TN "OpenClaw Gateway" 2>$null
Start-Sleep -Seconds 4
schtasks /Run /TN "OpenClaw Gateway"
Add-Content "C:\Users\orisi\.openclaw\backup\gateway-revert.log" ("{0} - End/Run issued (orisi 전환 헬퍼)" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
