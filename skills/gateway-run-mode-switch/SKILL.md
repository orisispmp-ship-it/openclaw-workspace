---
name: "gateway-run-mode-switch"
description: "OpenClaw gateway Windows run-mode switch: SYSTEM always-on ↔ orisi logon. Safe restart via one-shot helper task + auto-verify."
---

# Gateway Windows 실행모드 전환 (SYSTEM ↔ orisi)

Windows 호스트에서 OpenClaw 게이트웨이의 실행 주체를 **SYSTEM 상시 실행**과 **orisi 로그온 실행** 사이에서 바꾼다. 유이사님이 "로그인 안 해도 24시간 돌아가게 해줘"(→SYSTEM), "system 상시 실행 전환 취소해줘"(→orisi)처럼 모드를 요청할 때 쓴다.

## 핵심 원리 (왜 이렇게 하는지)

- 게이트웨이 = 포트 18789의 node 프로세스이며 **에이전트·exec의 호스트**. 게이트웨이를 죽이면 지금 돌고 있는 대화/exec도 같이 끊긴다.
- 따라서 **파괴적 재시작(기존 프로세스 종료)은 절대 현재 exec에서 직접 하지 말고**, +2~3분 뒤 실행되는 1회용 헬퍼 작업으로 분리한다. 그 사이 현재 턴은 끝내고 유이사님에게 "잠시 끊겼다 돌아온다"고 먼저 알린다.
- 재등록 단계(아래 2번)는 실행 중인 인스턴스를 죽이지 않으므로 현재 턴에서 바로 해도 안전하다.

## 절차

1. **현재 상태 파악** — 대상 작업 "OpenClaw Gateway"와 "OpenClaw Gateway 감시"의 Principal/LogonType/Triggers(`Get-ScheduledTask`), 실행 중 node 소유자(`Get-CimInstance Win32_Process -Filter "Name='node.exe'"` + `GetOwner`, CommandLine에 openclaw 포함 필터), 로그인 사용자(`Get-CimInstance Win32_ComputerSystem`의 UserName), 실행 파일 존재 확인: 시작폴더 `OpenClaw Gateway.vbs`, `C:\Users\orisi\.openclaw\gateway.cmd`·`gateway-service.cmd`(포트 중복 방지 + orisi 프로필 환경설정 포함 — 실행 Action은 이것을 유지).
2. **작업 재등록 (현재 턴에서 실행, 안전)**
   - **orisi(로그온)로**: `$xml = Export-ScheduledTask -TaskName "OpenClaw Gateway"` → `$xml.Replace('<UserId>S-1-5-18</UserId>', '<UserId>orisi</UserId><LogonType>InteractiveToken</LogonType>')` → `<BootTrigger\s*/>` 제거 → `<LogonTrigger/>`를 `<LogonTrigger><UserId>orisi</UserId></LogonTrigger>`로 → `Register-ScheduledTask -TaskName "OpenClaw Gateway" -Xml $xml -Force`.
   - **SYSTEM으로**: 부팅+로그온 트리거, Principal `S-1-5-18`(ServiceAccount, Highest), 실패 시 1분×3 재시도 — 9/1 작성본 `workspace/scripts/system-mode-setup.ps1` 참고해 같은 XML 패턴으로 등록.
   - **검증(완료 기준)**: `Get-ScheduledTask`로 Principal·LogonType·Triggers가 의도대로 바뀌었는지 출력 확인. 이 시점에 실행 중 인스턴스는 옛 방식 그대로 살아 있다.
3. **재시작 헬퍼 작성·예약 (파괴적 단계)**
   - `workspace/scripts/revert-helper.ps1`: `schtasks /End /TN "OpenClaw Gateway"` → `Start-Sleep 4` → `schtasks /Run /TN "OpenClaw Gateway"` → 결과 로그 append(`backup/gateway-revert.log`). `/End`는 실패로 간주되지 않아 RestartOnFailure가 안 걸리고, `/Run`이 새 방식(orisi Interactive, 로그인 세션 필요)으로 시작한다.
   - 1회 작업 등록: `New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(3)` + Principal SYSTEM(ServiceAccount, Highest) + `Register-ScheduledTask`.
4. **자동 검증 예약** — `automations`로 +5~7분 1회 agentTurn(`sessionTarget: current`): ① 작업 Principal이 orisi인지 ② 포트 18789 LISTENING 소유자가 orisi인지 ③ 헬퍼 로그 갱신 확인 → 정상이면 유이사님에게 완료 보고, 이상 있으면 상태 설명. (전환 직후 이 대화는 끊겼다 자동 복귀하므로, 그 사이의 통신은 이 예약된 검증 턴이 담당.)
5. **마무리** — 헬퍼 1회 작업 삭제, MEMORY.md "게이트웨이 실행 방식" 항목과 memory/일자 파일 갱신(모드 + 영향), 유이사님께 영향 고지: **로그온 모드에선 로그아웃/재부팅 후 로그인 전에 게이트웨이·크론(19:00 현장일기 백업, 07:00 손자병법 등)이 미동작**, 로그인하면 로그온 트리거 + 시작폴더 .vbs로 자동 시작. GitHub PAT는 orisi·SYSTEM GCM 양쪽에 있으므로 백업 인증은 모드와 무관.

## 주의

- 감시 작업 "OpenClaw Gateway 감시"(orisi, 5분)와 시작폴더 .vbs는 모드를 바꿔도 **그대로 둔다** — 로그온 자동 시작 + 사망 자동 복구의 안전망.
- **모호한 요청("백그라운드에서 돌아가게" 등)은 곧바로 전환하지 않는다** — 먼저 현재 상태가 이미 요청을 충족하는지 점검한다(포트 18789 LISTEN, node.exe Owner=orisi + WinTitle 없음 = 이미 창 없이 백그라운드 실행 중, 시작폴더 .vbs는 window style 0으로 숨김 실행). 이미 충족 중이거나 요청이 최근 지시와 상충하면(예: 당일 SYSTEM 취소 직후 상시 실행 요청) 유이사님께 확인받은 뒤에만 재시작한다. 확인 없이 헬퍼 재시작을 걸면 대화가 불필요하게 끊긴다.
- 실행 Action(`gateway-service.cmd`)은 바꾸지 않는다. `.cmd` 내부의 포트 중복 체크가 이중 기동을 막아준다.
- orisi Interactive 작업 재기동은 orisi가 로그인된 상태에서만 가능. 헬퍼 실행 시점에 로그인 안 되어 있으면 실패하므로, 헬퍼는 로그인 세션을 확인한 뒤 예약한다.
