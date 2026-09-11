# Adware cleanup - X1_Carbon_G12 / orisi - 2026-09-11
# Targets: Smart Windows Favorite(winfavorites), HTTPS Connect SecureConnection,
#          MiteNews(powernhit), Temperature Indicator(weaping), WindowsOptimizer,
#          Anchortools(SoftBridge/Flint), SmartBridge(Enliple)
$ErrorActionPreference = 'Continue'
$bk  = 'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11'
$log = Join-Path $bk 'cleanup.log'
function Log([string]$m) { $m | Tee-Object -FilePath $log -Append | Out-Null }

Log "=== cleanup start $(Get-Date -Format s) ==="

# 0) evidence snapshot
try { & reg.exe export 'HKCU\Software\favoriteurls' (Join-Path $bk 'favoriteurls.reg.txt') /y | Out-Null } catch {}
try {
  $snap = @()
  foreach ($k in 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run') {
    $p = Get-ItemProperty $k -ErrorAction SilentlyContinue
    if ($p) { $p.PSObject.Properties | Where-Object { $_.Name -notlike 'PS*' } | ForEach-Object { $snap += "$k :: $($_.Name) = $($_.Value)" } }
  }
  $snap | Set-Content -Encoding UTF8 (Join-Path $bk 'run-keys-before.txt')
  Log '[snap] run keys saved'
} catch {}

# 1) scheduled tasks: disable then delete
$tasks = @('Smart Windows Favorite','Schedule for Favorite Update Check','secureconnections','SecureConnectionCheck')
foreach ($n in $tasks) {
  & schtasks.exe /Change /TN $n /DISABLE 2>&1 | Out-Null
  $r = & schtasks.exe /Delete /TN $n /F 2>&1
  Log "[task] $n -> $r"
}

# 2) stop adware processes
$proc = @('favoriteurl','favoritesch','secureconnection','secureconnectionservice','powernhit_manager','WindowsOptimizer','Flint','Beige','TemperatureIndicator','weapUpdater','SmartBridge','SmartBridgeLauncher')
foreach ($p in $proc) {
  Get-Process -Name $p -ErrorAction SilentlyContinue | ForEach-Object {
    Log "[proc] stop $($_.ProcessName) ($($_.Id))"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
  }
}

# 3) adware service
if (Get-Service -Name 'SecureConnection' -ErrorAction SilentlyContinue) {
  Stop-Service -Name 'SecureConnection' -Force -ErrorAction SilentlyContinue
  & sc.exe delete SecureConnection | Out-Null
  Log '[svc] SecureConnection stopped and deleted'
}

# 4) vendor uninstallers (silent, no -Wait to avoid hangs)
$uninst = @(
  @{ f = 'C:\Users\orisi\AppData\Roaming\winfavorites\Uninstall.exe';            a = '/S' },
  @{ f = 'C:\ProgramData\secureconnection\Uninstall.exe';                        a = '/S' },
  @{ f = 'C:\Users\orisi\AppData\Local\powernhit\unins000.exe';                  a = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' },
  @{ f = 'C:\Users\orisi\AppData\Local\TemperatureIndicator\unins000.exe';       a = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' }
)
foreach ($u in $uninst) {
  if (Test-Path $u.f) {
    Log "[uninst] $($u.f) $($u.a)"
    try { Start-Process -FilePath $u.f -ArgumentList $u.a -ErrorAction Stop } catch { Log "[uninst] FAILED $($u.f) : $($_.Exception.Message)" }
  } else { Log "[uninst] missing $($u.f)" }
}
$wo = 'C:\Users\orisi\AppData\Local\WindowsOptimizer\Update.exe'
if (Test-Path $wo) {
  Log '[uninst] WindowsOptimizer'
  try { Start-Process -FilePath $wo -ArgumentList '--uninstall','-s' -ErrorAction Stop } catch { Log "[uninst] FAILED WindowsOptimizer : $($_.Exception.Message)" }
}
Log '[wait] letting uninstallers run 45s'
Start-Sleep -Seconds 45

# re-kill anything the uninstallers started
foreach ($p in $proc) { Get-Process -Name $p -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue }

# 5) leftover folders
$folders = @(
  'C:\Users\orisi\AppData\Roaming\winfavorites',
  'C:\Users\orisi\AppData\Local\TemperatureIndicator',
  'C:\Users\orisi\AppData\Local\WindowsOptimizer',
  'C:\Users\orisi\AppData\Local\powernhit',
  'C:\ProgramData\secureconnection',
  'C:\Program Files (x86)\VP\AD'
)
foreach ($d in $folders) {
  if (Test-Path $d) {
    Remove-Item -LiteralPath $d -Recurse -Force -ErrorAction SilentlyContinue
    Log "[dir] $d removed = $(-not (Test-Path $d))"
  } else { Log "[dir] $d already gone" }
}

# Anchortools/Flint files (keep unrelated dainBroad subfolder)
$fl = @('Flint.exe','Flint.20250630.bak','Beige.exe','Beige.log','config.ini','Flint.log','libeay32.dll','mls.lst','ssleay32.dll')
foreach ($f in $fl) {
  $p = Join-Path 'C:\SoftBridge' $f
  if (Test-Path $p) { Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue; Log "[file] $f removed = $(-not (Test-Path $p))" }
}

# 6) autostart entries
$runKeys = @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run','HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run')
$runNames = @('powernhit_manager','Anchortools Launcher','weaping','weapingU','WindowsOptimizer','SmartBridgeLauncher')
foreach ($k in $runKeys) {
  if (-not (Test-Path $k)) { continue }
  foreach ($n in $runNames) {
    if (Get-ItemProperty -Path $k -Name $n -ErrorAction SilentlyContinue) {
      Remove-ItemProperty -Path $k -Name $n -Force -ErrorAction SilentlyContinue
      Log "[run] $k -> $n removed = $(-not [bool](Get-ItemProperty -Path $k -Name $n -ErrorAction SilentlyContinue))"
    }
  }
}

# 7) registry leftovers
$regs = @(
  'HKCU:\Software\favoriteurls',
  'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\favoriteurls',
  'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsOptimizer',
  'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\secureconnection',
  'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{B8137491-AEE9-4D36-BDB2-708F8F6EBD79}_is1',
  'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{CA1EE949-5251-4DF3-9E12-8D886F2F7F2E}_is1'
)
foreach ($k in $regs) {
  if (Test-Path $k) {
    Remove-Item -LiteralPath $k -Recurse -Force -ErrorAction SilentlyContinue
    Log "[reg] $k removed = $(-not (Test-Path $k))"
  }
}

# 8) verify
Log '=== verify: tasks (should all be blank) ==='
foreach ($n in $tasks) { Log ("  {0} : {1}" -f $n, (Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue).State) }
Log '=== verify: paths (should all be False) ==='
foreach ($d in $folders) { Log ("  {0} exists={1}" -f $d, (Test-Path $d)) }
Log '=== verify: leftover procs ==='
foreach ($p in $proc) { $x = Get-Process -Name $p -ErrorAction SilentlyContinue; if ($x) { Log "  STILL RUNNING: $p" } }
Log '=== verify: leftover run keys ==='
foreach ($k in $runKeys) { foreach ($n in $runNames) { if (Get-ItemProperty -Path $k -Name $n -ErrorAction SilentlyContinue) { Log "  STILL PRESENT: $k -> $n" } } }
Log '=== verify: leftover uninstall entries ==='
$up = @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*')
Get-ItemProperty $up -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match 'Smart Windows Favorite|SecureConnection|Temperature Indicator|WindowsOptimizer|MiteNews' } | ForEach-Object { Log "  STILL PRESENT: $($_.DisplayName)" }
Log "=== cleanup end $(Get-Date -Format s) ==="
Get-Content $log
