# Adware cleanup pass 2 - 2026-09-11
$ErrorActionPreference = 'Continue'
$bk  = 'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11'
$log = Join-Path $bk 'pass2.log'
function Log([string]$m) { $m | Tee-Object -FilePath $log -Append | Out-Null }

Log "=== pass2 start $(Get-Date -Format s) ==="

# 1) kill leftover zombie process from the removed adware service
Get-Process -Name 'secureconnectionservice' -ErrorAction SilentlyContinue | ForEach-Object {
  Log "[proc] stop $($_.ProcessName) ($($_.Id))"
  Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Get-Process -Name 'favoriteurl','favoritesch','secureconnection','powernhit_manager','WindowsOptimizer','Flint','Beige','TemperatureIndicator','weapUpdater','SmartBridge','SmartBridgeLauncher' -ErrorAction SilentlyContinue | ForEach-Object {
  Log "[proc] stop $($_.ProcessName) ($($_.Id))"
  Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

# 2) persistence sweep: services with unusual binaries
Log '=== services with non-standard paths ==='
Get-CimInstance Win32_Service | Where-Object { $_.PathName -match 'AppData|ProgramData|\\Temp\\|SoftBridge|winfavorites|secureconnection|powernhit' } | ForEach-Object {
  Log ("  {0} | {1} | {2} | {3}" -f $_.Name, $_.State, $_.StartMode, $_.PathName)
}

# 3) scheduled tasks outside the Microsoft folder
Log '=== root scheduled tasks ==='
Get-ScheduledTask | Where-Object { $_.TaskPath -eq '\' } | ForEach-Object {
  Log ("  {0} | {1} | {2} {3}" -f $_.TaskName, $_.State, $_.Actions.Execute, $_.Actions.Arguments)
}

# 4) autostart entries
Log '=== run keys ==='
foreach ($k in 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce','HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run') {
  $p = Get-ItemProperty $k -ErrorAction SilentlyContinue
  if ($p) { $p.PSObject.Properties | Where-Object { $_.Name -notlike 'PS*' } | ForEach-Object { Log ("  {0} :: {1} = {2}" -f $k, $_.Name, $_.Value) } }
}

# 5) final verification of the removal
Log '=== verify removed ==='
foreach ($n in 'Smart Windows Favorite','Schedule for Favorite Update Check','secureconnections','SecureConnectionCheck') {
  $t = Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue
  Log ("  task {0} => {1}" -f $n, $(if ($t) { $t.State } else { 'GONE' }))
}
foreach ($d in 'C:\Users\orisi\AppData\Roaming\winfavorites','C:\Users\orisi\AppData\Local\TemperatureIndicator','C:\Users\orisi\AppData\Local\WindowsOptimizer','C:\Users\orisi\AppData\Local\powernhit','C:\ProgramData\secureconnection','C:\Program Files (x86)\VP\AD') {
  Log ("  path {0} exists={1}" -f $d, (Test-Path $d))
}
$svc = Get-Service -Name 'SecureConnection' -ErrorAction SilentlyContinue
Log ("  service SecureConnection => {0}" -f $(if ($svc) { $svc.Status } else { 'GONE' }))
foreach ($p in 'favoriteurl','favoritesch','secureconnection','secureconnectionservice','powernhit_manager','WindowsOptimizer','Flint','Beige','TemperatureIndicator','weapUpdater','SmartBridge','SmartBridgeLauncher') {
  if (Get-Process -Name $p -ErrorAction SilentlyContinue) { Log "  STILL RUNNING: $p" }
}
$up = @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')
Get-ItemProperty $up -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match 'Smart Windows Favorite|SecureConnection|Temperature Indicator|WindowsOptimizer|MiteNews' } | ForEach-Object { Log "  STILL INSTALLED: $($_.DisplayName)" }

Log "=== pass2 end $(Get-Date -Format s) ==="
