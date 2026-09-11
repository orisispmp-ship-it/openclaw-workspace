# Final check - 2026-09-11
$ErrorActionPreference = 'Continue'

Write-Output '===== 1) adware scheduled tasks ====='
$tasks = @('ClipdownBootStrapper', 'ClipDownScheduler_{EF3FBBA1-8465-488A-AF71-1A9FF009B65C}',
           'Smart Windows Favorite', 'Schedule for Favorite Update Check', 'secureconnections', 'SecureConnectionCheck')
foreach ($n in $tasks) {
  $t = Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue
  Write-Output ("  {0,-45} => {1}" -f $n, $(if ($t) { $t.State } else { 'GONE (ok)' }))
}
Write-Output '  * any other task pointing at adware paths:'
$hit = $false
Get-ScheduledTask | ForEach-Object { $t = $_; $t.Actions | ForEach-Object { if ($_.Execute -match 'clipdown|cdsrvc|winfavorites|favoriteurl|secureconnection|powernhit|TemperatureIndicator|WindowsOptimizer|SoftBridge|SmartBridge') { Write-Output "    STILL: $($t.TaskName) -> $($_.Execute)"; $hit = $true } } }
if (-not $hit) { Write-Output '    none (ok)' }

Write-Output ''
Write-Output '===== 2) adware services ====='
$svc = Get-CimInstance Win32_Service | Where-Object { $_.PathName -match 'clipdown|cdsrvc|secureconnection|winfavorites|powernhit|WindowsOptimizer|TemperatureIndicator|SoftBridge|SmartBridge' }
if ($svc) { $svc | Select-Object Name, State, PathName | Format-List } else { Write-Output '  none (ok)' }

Write-Output ''
Write-Output '===== 3) adware processes ====='
$found = $false
foreach ($p in 'clipdown', 'cdsrvc', 'cdboot', 'favoriteurl', 'favoritesch', 'secureconnection', 'secureconnectionservice', 'powernhit_manager', 'WindowsOptimizer', 'Flint', 'Beige', 'TemperatureIndicator', 'weapUpdater', 'SmartBridge', 'SmartBridgeLauncher') {
  $x = Get-Process -Name $p -ErrorAction SilentlyContinue
  if ($x) { Write-Output "  RUNNING: $p"; $found = $true }
}
if (-not $found) { Write-Output '  none (ok)' }

Write-Output ''
Write-Output '===== 4) adware folders ====='
foreach ($d in 'C:\Program Files (x86)\clipdown', "$env:APPDATA\winfavorites", "$env:LOCALAPPDATA\powernhit", "$env:LOCALAPPDATA\TemperatureIndicator", "$env:LOCALAPPDATA\WindowsOptimizer", 'C:\ProgramData\secureconnection', 'C:\Program Files (x86)\VP\AD', 'C:\SoftBridge\Flint.exe') {
  Write-Output ("  {0,-52} exists={1}" -f $d, (Test-Path $d))
}

Write-Output ''
Write-Output '===== 5) startup entries (adware) ====='
$runKeys = @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run', 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run')
$bad = $false
foreach ($k in $runKeys) {
  $p = Get-ItemProperty $k -ErrorAction SilentlyContinue
  if ($p) { $p.PSObject.Properties | Where-Object { $_.Name -notlike 'PS*' } | ForEach-Object { if ($_.Name -match 'clipdown|favorite|secureconn|powernhit|weaping|Optimizer|SmartBridge|Anchor') { Write-Output "  STILL: $($_.Name)"; $bad = $true } } }
}
if (-not $bad) { Write-Output '  none (ok)' }

Write-Output ''
Write-Output '===== 6) chrome fake bookmarks ====='
$bm = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Bookmarks"
if (Test-Path $bm) {
  $raw = Get-Content $bm -Raw
  Write-Output ("  xn--o39an entries : {0}" -f ([regex]::Matches($raw, 'xn--o39an')).Count)
  Write-Output ("  shoppingbargain   : {0}" -f ([regex]::Matches($raw, 'shoppingbargain')).Count)
  Write-Output ("  total bookmarks   : {0}" -f ([regex]::Matches($raw, '"type": "url"')).Count)
} else { Write-Output '  Bookmarks file missing' }

Write-Output ''
Write-Output '===== 7) chrome status ====='
$c = Get-Process chrome -ErrorAction SilentlyContinue
Write-Output ("  chrome processes: {0} (running={1})" -f @($c).Count, [bool]$c)
