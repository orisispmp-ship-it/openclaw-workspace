param(
  [Parameter(Mandatory=$true)][string]$Xlsx,
  [string]$Out = ""
)
# .xlsx 셀 그리드를 텍스트 행으로 출력 (Excel 불필요).
# 사용: powershell -NoProfile -ExecutionPolicy Bypass -File read-xlsx-rows.ps1 <file.xlsx>
$ErrorActionPreference = 'Stop'
$src = (Resolve-Path $Xlsx).Path
$tmpId = [guid]::NewGuid().ToString('N')
$zip = Join-Path $env:TEMP ($tmpId + '.zip')
$dir = Join-Path $env:TEMP ('xlsx_' + $tmpId)
try {
  Copy-Item $src $zip -Force
  Expand-Archive $zip -DestinationPath $dir -Force
  $ssPath = Join-Path $dir 'xl/sharedStrings.xml'
  $sheetPath = Join-Path $dir 'xl/worksheets/sheet1.xml'
  if (-not (Test-Path $ssPath) -or -not (Test-Path $sheetPath)) { throw 'sharedStrings.xml or sheet1.xml missing' }

  [xml]$ss = Get-Content -Raw -Encoding UTF8 $ssPath
  $strings = @()
  foreach ($si in $ss.sst.si) {
    $txt = ''
    if ($si.t -is [string]) { $txt = $si.t }
    elseif ($si.t) { $txt = $si.t.'#text'; if (-not $txt) { $txt = ($si.t | ForEach-Object { $_.'#text' }) -join '' } }
    if ($si.r) {
      $runs = @()
      foreach ($r in $si.r) { if ($r.t -is [string]) { $runs += $r.t } elseif ($r.t) { $runs += $r.t.'#text' } }
      $txt = $runs -join ''
    }
    $strings += [string]$txt
  }

  [xml]$sheet = Get-Content -Raw -Encoding UTF8 $sheetPath
  function ColLetterToNum($col) { $n = 0; foreach ($ch in $col.ToCharArray()) { $n = $n * 26 + ([int][char]$ch - 64) }; return $n }
  $rows = @()
  foreach ($row in $sheet.worksheet.sheetData.row) {
    $cells = @{}; $maxCol = 0
    foreach ($c in $row.c) {
      $colIdx = ColLetterToNum (($c.r -replace '[0-9]', ''))
      if ($colIdx -gt $maxCol) { $maxCol = $colIdx }
      $val = ''
      if ($c.t -eq 's') { $val = $strings[[int]$c.v] }
      elseif ($c.t -eq 'inlineStr') { $val = $c.is.t }
      elseif ($c.v) { $val = [string]$c.v }
      $cells[$colIdx] = $val
    }
    $line = @()
    for ($i = 1; $i -le $maxCol; $i++) { if ($cells.ContainsKey($i)) { $line += $cells[$i] } else { $line += '' } }
    $rows += ($line -join ' | ')
  }
  if ($Out) { $rows | Out-File -FilePath $Out -Encoding UTF8; Write-Output "saved: $Out" }
  else { $rows }
}
finally {
  Remove-Item $zip -Force -ErrorAction SilentlyContinue
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
}