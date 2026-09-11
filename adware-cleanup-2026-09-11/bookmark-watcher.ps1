# Waits until Chrome is fully closed, then adds the Coupang bookmark to the Chrome
# bookmark file (idempotent). Bounded runtime.
$bk  = 'C:\Users\orisi\.openclaw\workspace\adware-cleanup-2026-09-11'
$log = Join-Path $bk 'bookmark-watcher.log'
$py  = Join-Path $bk 'ensure-coupang-bookmark.py'
$bm  = Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data\Default\Bookmarks'
$end = (Get-Date).AddHours(8)

function Log([string]$m) { ("{0} {1}" -f (Get-Date -Format 'MM-dd HH:mm:ss'), $m) | Tee-Object -FilePath $log -Append | Out-Null }

Log '=== watcher start (waiting for Chrome to close) ==='
$done = $false
while (-not $done -and (Get-Date) -lt $end) {
  if (-not (Get-Process chrome -ErrorAction SilentlyContinue)) {
    Log 'chrome is closed -> applying bookmark'
    $out = & python.exe $py 2>&1
    Log ("  script: " + (($out | Out-String).Trim() -replace "`r?`n", ' | '))
    Start-Sleep -Seconds 5
    $raw = Get-Content $bm -Raw -ErrorAction SilentlyContinue
    if ($raw -and $raw -match 'https://www\.coupang\.com/') {
      Log 'VERIFIED: coupang bookmark is in the file. watcher done.'
      $done = $true
      break
    }
    Log '  not verified yet, will retry'
  }
  Start-Sleep -Seconds 20
}
if (-not $done) { Log '=== watcher ended without applying (chrome stayed open or timeout) ===' }
