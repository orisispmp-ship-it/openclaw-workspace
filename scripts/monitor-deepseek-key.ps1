# DeepSeek API 키 오류 모니터링 스크립트
# - 정상(200): NO_REPLY 출력 (크론이 조용히 넘김)
# - 에러: 경고 메시지 출력 (텔레그램 announce로 전송됨)
$ErrorActionPreference = 'Stop'
$configPath = Join-Path $env:USERPROFILE '.openclaw\openclaw.json'
try {
  $config = Get-Content $configPath -Raw | ConvertFrom-Json
  $key = $config.env.vars.DEEPSEEK_API_KEY
  if (-not $key) { Write-Output '⚠️ DeepSeek API 키가 설정 파일에 없습니다 (DEEPSEEK_API_KEY 누락). 확인 필요.'; exit 0 }
  $code = & curl.exe -s -o NUL -w '%{http_code}' -H "Authorization: Bearer $key" 'https://api.deepseek.com/user/balance'
  if ($code -eq '200') {
    Write-Output 'NO_REPLY'
  } else {
    $msg = switch ($code) {
      '401' { 'DeepSeek API 키가 유효하지 않거나 만료되었습니다 (HTTP 401). DeepSeek 콘솔에서 키를 확인하세요.' }
      '402' { 'DeepSeek API 잔액이 부족합니다 (HTTP 402). 충전이 필요합니다.' }
      '403' { 'DeepSeek API 접근이 거부되었습니다 (HTTP 403). 키 권한을 확인하세요.' }
      'NO_KEY' { 'DeepSeek API 키가 설정 파일에 없습니다. 확인 필요.' }
      'SCRIPT_ERROR' { 'DeepSeek 키 체크 스크립트 자체가 실패했습니다.' }
      default { "DeepSeek API 응답이 비정상입니다 (HTTP $code). 키/네트워크 상태를 확인하세요." }
    }
    Write-Output "⚠️ $msg"
  }
} catch {
  Write-Output '⚠️ DeepSeek 키 모니터링 스크립트 오류. 로그 확인 필요.'
}
exit 0
