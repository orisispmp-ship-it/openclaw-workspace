# ClipDown adware removal - 2026-09-11
$ErrorActionPreference = 'Continue'
$bk  = 'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11'
$log = Join-Path $bk 'pass3-clipdown.log'
function Log([string]$m) { $m | Tee-Object -FilePath $log -Append | Out-Null }

$tasks = @('ClipdownBootStrapper', 'ClipDownScheduler_{EF3FBBA1-8465-488A-AF71-1A9FF009B65C}')
$procs = @('clipdown', 'cdsrvc', 'cdboot')
$dir   = 'C:\Program Files (x86)\clipdown'

Log "=== ClipDown removal start $(Get-Date -Format s) ==="

# 1) backup scheduled tasks
foreach ($n in $tasks) {
  try { Export-ScheduledTask -TaskName $n | Set-Content -Encoding UTF8 (Join-Path $bk "$n.xml"); Log "[backup] $n" }
  catch { Log "[backup] FAIL $n : $($_.Exception.Message)" }
}

# 2) disable + delete scheduled tasks
foreach ($n in $tasks) {
  & schtasks.exe /Change /TN $n /DISABLE 2>&1 | Out-Null
  $r = & schtasks.exe /Delete /TN $n /F 2>&1
  Log "[task] $n -> $r"
}

# 3) stop and delete the service
if (Get-Service -Name 'ClipdownService' -ErrorAction SilentlyContinue) {
  Stop-Service -Name 'ClipdownService' -Force -ErrorAction SilentlyContinue
  & sc.exe config ClipdownService start= disabled | Out-Null
  & sc.exe delete ClipdownService | Out-Null
  Log '[svc] ClipdownService stopped and deleted'
}

# 4) kill processes
foreach ($p in $procs) {
  Get-Process -Name $p -ErrorAction SilentlyContinue | ForEach-Object {
    Log "[proc] stop $($_.ProcessName) ($($_.Id))"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
  }
}

# 5) vendor uninstaller (silent)
$un = Join-Path $dir 'uninst.exe'
if (Test-Path $un) {
  Log "[uninst] $un /S"
  try { Start-Process -FilePath $un -ArgumentList '/S' -ErrorAction Stop } catch { Log "[uninst] FAILED $($_.Exception.Message)" }
  Start-Sleep -Seconds 30
} else { Log "[uninst] missing $un" }

foreach ($p in $procs) { Get-Process -Name $p -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue }

# 6) remove leftovers
if (Test-Path $dir) {
  Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue
  Log "[dir] $dir removed = $(-not (Test-Path $dir))"
}
$sm = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\clipdown'
if (Test-Path $sm) { Remove-Item -LiteralPath $sm -Recurse -Force -ErrorAction SilentlyContinue; Log "[shortcut] start menu clipdown removed" }

$regs = @(
  'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\CLIPDOWN',
  'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\CLIPDOWN'
)
foreach ($k in $regs) {
  if (Test-Path $k) { Remove-Item -LiteralPath $k -Recurse -Force -ErrorAction SilentlyContinue; Log "[reg] $k removed = $(-not (Test-Path $k))" }
}

# 7) verify
Log '=== verify ==='
foreach ($n in $tasks) { Log ("  task {0} => {1}" -f $n, $(if (Get-ScheduledTask -TaskName $n -ErrorAction SilentlyContinue) { 'STILL PRESENT' } else { 'GONE' })) }
Log ("  service ClipdownService => " + $(if (Get-Service -Name 'ClipdownService' -ErrorAction SilentlyContinue) { 'STILL PRESENT' } else { 'GONE' }))
Log ("  path {0} exists={1}" -f $dir, (Test-Path $dir))
foreach ($p in $procs) { if (Get-Process -Name $p -ErrorAction SilentlyContinue) { Log "  STILL RUNNING: $p" } }
Get-CimInstance Win32_Service | Where-Object { $_.PathName -match 'clipdown|cdsrvc' } | ForEach-Object { Log "  STILL SERVICE: $($_.Name) $($_.PathName)" }
Log "=== ClipDown removal end $(Get-Date -Format s) ==="
