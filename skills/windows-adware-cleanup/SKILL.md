---
name: "windows-adware-cleanup"
description: "윈도우 광고창·저절로 뜨는 브라우저 창 제거: 예약작업 진단→백업→UAC 관리자 정리→검증"
---

# 윈도우 애드웨어 제거 (저절로 뜨는 브라우저·광고 팝업)

## 언제 쓴다
"크롬창이 저절로 뜬다", "쿠팡/쇼핑몰 창이 자꾸 뜬다", 원치 않는 프로그램이 자동 실행된다는 신고.

## 1. 진단 (읽기 전용, 관리자 불필요)
아래를 한 번에 조회하고 결과를 표로 정리한다.
- 예약작업: `Get-ScheduledTask | Where-Object { $_.Actions.Arguments -match 'http|chrome|msedge' -or $_.Actions.Execute -match 'AppData|ProgramData|Temp' } | Select-Object TaskName,TaskPath,State,@{n='Exec';e={$_.Actions.Execute}},@{n='Args';e={$_.Actions.Arguments}} | Format-List`
- 자동시작: HKCU/HKLM/WOW6432Node `...\CurrentVersion\Run` + 시작프로그램 폴더 2곳(`%APPDATA%`, `%ProgramData%`)
- 설치 목록: Uninstall 키 3곳(HKLM, WOW6432Node, HKCU)에서 DisplayName/Publisher/UninstallString
- 서비스: `Get-CimInstance Win32_Service | Where-Object { $_.PathName -match 'AppData|ProgramData|Temp' }`
- 게시자: `(Get-AuthenticodeSignature $f).SignerCertificate.Subject` + `(Get-Item $f).VersionInfo`
- 애드웨어 자체 설정: `HKCU\Software\<이름>` (예: `favoriteurls`의 `fv=600` = 600초 주기 → 반복 팝업의 직접 증거)
- 브라우저 쪽: Chrome 정책 키 `HKLM|HKCU\SOFTWARE\Policies\Google\Chrome`, 바로가기 Arguments, 확장 목록

알려진 국내 애드웨어 계열(원인 후보): `favoriteurls`/winfavorites(MediaClick, 쇼핑몰 URL 주기 오픈), secureconnection(MONSTERJ, 재설치 배포), MiteNews(powernhit), Temperature Indicator, WindowsOptimizer, Anchortools/Flint(SoftBridge), SmartBridge(Enliple).

완료 기준: 반복 실행 주체(예약작업·서비스), 실행 파일 경로, 설치일, 게시자를 특정.

## 2. 백업 (변경 전 필수)
워크스페이스에 `adware-cleanup-<YYYY-MM-DD>\` 생성 → `Export-ScheduledTask` XML, Run 키 스냅샷, `reg export`, CloudStore 백업을 저장한다.

## 3. 관리자 작업은 UAC 경유로
- `exec elevated:true`는 webchat 등 provider 게이트에서 거부된다(runtime=direct). 재시도로 시간 쓰지 말고 바로 다음으로 간다.
- 게이트웨이가 로그인 사용자(session 1)로 돌면 `Start-Process -FilePath powershell.exe -ArgumentList '-ExecutionPolicy','Bypass','-NoProfile','-File',<스크립트> -Verb RunAs`로 바탕화면에 UAC 창을 띄우고, 사용자에게 "UAC 창에서 예를 눌러달라"고 안내한다.
- UAC는 약 2분 뒤 자동 취소된다(`사용자가 작업을 취소했습니다`). 그 안에 클릭받아야 하며, 안 되면 재부팅으로 미루거나 다시 요청한다.
- 스크립트가 결과를 로그 파일에 쓰게 하고, 실행 후 그 로그를 읽어 검증한다(exec 출력에 의존하지 않는다).
- 먼저 `whoami`와 `(Get-Process -Id $PID).SessionId`로 SYSTEM 여부·세션을 확인한다. SYSTEM이면 HKCU가 달라져 스크립트가 헛돈다.

## 4. 정리 순서 (한 스크립트에서)
1. 예약작업: `schtasks /Change /TN "<name>" /DISABLE` 후 `/Delete /F`
2. 프로세스 중지
3. 서비스 중지 + `sc.exe delete "<name>"`
4. 제거 실행: Inno는 `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`, NSIS는 `/S`, Electron은 `--uninstall -s`. `-Wait`는 쓰지 않는다(hang·브라우저 실행 위험) → 실행 후 `Start-Sleep 45`, 이후 남은 프로세스를 재종료
5. 폴더 삭제 → Run 키 삭제 → Uninstall·CloudStore 레지스트리 삭제 → 서비스·바이너리를 지운 뒤에도 남는 애드웨어 설정 키(`HKCU\Software\<이름>`, `HKLM\SOFTWARE\WOW6432Node\<이름>`, 예: `check_secureconnection`)와 애드웨어가 심은 Chrome 정책 값(`HKLM\SOFTWARE\Policies\Google\Chrome`의 `InsecurePrivateNetworkRequestsAllowed` 등) 삭제

같은 폴더를 공유하는 무관한 하위 프로그램은 보존한다. 삭제 대상 목록을 먼저 확인하고 범위를 사용자에게 한 번 확인받는다.

## 5. 검증
삭제한 예약작업·폴더·레지스트리·프로세스를 다시 조회해 없음을 확인하고 로그에 남긴다. SYSTEM 소유 프로세스가 남고 바이너리가 이미 삭제됐다면 "재부팅 시 소멸"로 보고한다.

점검 스크립트는 한 번에 묶어 돌린다: 삭제 대상 예약작업 + 애드웨어 경로를 가리키는 다른 예약작업, 서비스, 프로세스, 폴더, 시작프로그램, 크롬 `Bookmarks`의 의심 URL 개수, Chrome 실행 여부.

`-File`로 실행하는 헬퍼 .ps1 본문에 한글을 쓰면 Windows PowerShell 5.1이 UTF-8을 ANSI로 읽어 파서 오류(`문자열에 ' 종결자가 없습니다`)로 죽는다. 스크립트 안 레이블·로그 메시지는 ASCII로 쓰고 한글 보고는 채팅에서 한다.

## 보존 대상 (한국 금융·인증)
UbiViewer, CrossEX, AnySign4PC, Veraport, MagicLine4NX, IPinside, SignKorea, TouchEn, VPWallet/eISP, 알약 계열 — 제거 목록에 넣지 않는다.

## 6. 미제거 애드웨어 찾기 — 크롬 방문 기록 포렌식
예약작업·폴더·레지스트리를 다 지운 뒤에도 광고창이 뜨면 남은 애드웨어가 있다. 크롬 기록이 그걸 드러내는 유일한 증거다(실제로 ClipDown은 이 단계에서만 발견됐다). 정리 직후에도 반드시 한 번 돌린다.

1. `%LOCALAPPDATA%\Google\Chrome\User Data\Default\History`를 임시 폴더로 **복사**한 뒤 sqlite3로 연다(실행 중 Chrome이 원본을 잠근다).
2. `visits.url`은 `urls.id`를 가리키는 정수 FK다. 반드시 조인한다: `select v.visit_time, u.url from visits v join urls u on u.id = v.url where v.visit_time > ? order by v.visit_time`. 조인 없이 `url`을 그대로 쓰면 정수가 나와 `'int' object has no attribute 'lower'`로 죽는다.
3. Chrome time = 1601-01-01 UTC 기준 마이크로초. 시각 변환은 `datetime(1601,1,1)+timedelta(microseconds=ct)+timedelta(hours=9)`(KST), 필터 값은 **정수로 만들어** 넘긴다(파이썬 datetime을 그대로 넘기면 SQLite가 문자열로 비교해 0건이 된다).
4. 의심 도메인으로 필터: `searchalgorithm.co.kr`, `api.mjbiz.co.kr`, `api.hode.co.kr`, `rabinoa.com`, `chatgot.co.kr`, `searchconsole.co.kr`, `smartbridge.co.kr`, `helpstart.co.kr`, `xn--o39an5bf2p1yd8rjol5a.com`(쇼핑바로가기.com). 광고 탭은 `.../ad/tab_open.php?...&domain=즐겨찾기` → `api.*.co.kr` → 쇼핑몰 링크 → 실제 쇼핑몰 순서로 찍힌다.
5. 같은 시각대가 반복되면(예: 매일 04:4x·18:0x) 주기 실행 증거다. 정리 시각 **이후** 항목이 하나라도 있으면 미제거 확정이며, 그 기록의 `title`·`shortcut` 파라미터가 범인 프로그램의 광고 이름을 알려준다.
6. 범인이 ClipDown 계열(JS Future)이면 함께 지운다: `C:\Program Files (x86)\clipdown`, 서비스 `ClipdownService`(cdsrvc.exe), 예약작업 `ClipdownBootStrapper`·`ClipDownScheduler_{...}`. `ad_shortcutbookmark.xml`의 쿠팡/11번가/G마켓/옥션/알리/아고다/테무 가짜 바로가기는 base64 후 키 `clip` 반복 XOR로 난독화돼 있다.
7. **크롬 북마크도 별도 지속 경로다.** 이름이 "쿠팡!" 같은 가짜 쇼핑 바로가기가 `Bookmarks` JSON에 심겨 있으면 백업 후 `roots`를 재귀 순회해 의심 URL 노드(`xn--o39an`, `쇼핑바로가기`, `searchalgorithm` 등)만 삭제한다. **Chrome 실행 중에 파일을 고치면 메모리 상태로 덮여 되살아나므로, Chrome을 완전히 종료한 상태에서 수정하고 재시작을 안내한다.**
   - `checksum` 필드는 로드 시 **검사되지 않는다**. Chromium `bookmark_codec.cc`의 `DecodeHelper`는 `version`과 `roots`·`bookmark_bar`·`other`·`synced` 존재만 확인하고, checksum은 `Encode`에서만 계산한다. 이 필드 때문에 파일 편집을 포기하지 않는다.
   - 그래도 맞추려면: MD5(hex 소문자)에 **노드 순서대로** `id`(문자열) → `name`(UTF-16LE 바이트) → URL 노드면 `url`+`url`(UTF-8), 폴더 노드면 `folder`를 넣고, 폴더의 자식은 그 폴더 뒤에 이어 넣는다. 루트는 `bookmark_bar` → `other` → `synced` 순. 크롬이 쓴 기존 파일로 재계산해 값이 일치하는지 먼저 검증한다.
   - 같은 방법으로 정상 북마크를 추가할 수 있다. 노드는 `id`(트리 최대값+1, 문자열), `guid`(uuid4), `name`, `type:"url"`, `url`, `date_added`/`date_last_used`(1601-01-01 UTC 기준 마이크로초 문자열, 미사용이면 `"0"`).
   - 크롬은 프로필 시작 시에만 `Bookmarks`를 읽으므로, 수정 뒤에는 크롬을 완전히 종료(트레이 포함)했다가 다시 열어야 화면에 반영된다.
8. 정리 직후 며칠간 재점검을 예약해 두면 재발을 조기에 잡는다.
