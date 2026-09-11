# DeepSeek API 키 상태 체크 스크립트
# 출력: HTTP 상태 코드 (200 = 정상) 또는 NO_KEY / SCRIPT_ERROR
$ErrorActionPreference = 'Stop'
$configPath = Join-Path $env:USERPROFILE '.openclaw\openclaw.json'
try {
  $config = Get-Content $configPath -Raw | ConvertFrom-Json
  $key = $config.env.vars.DEEPSEEK_API_KEY
  if (-not $key) { Write-Output 'NO_KEY'; exit 2 }
  $code = & curl.exe -s -o NUL -w '%{http_code}' -H "Authorization: Bearer $key" 'https://api.deepseek.com/user/balance'
  Write-Output $code
} catch {
  Write-Output 'SCRIPT_ERROR'
  exit 3
}
