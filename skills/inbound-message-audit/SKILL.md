---
name: "inbound-message-audit"
description: "메시지 유실·오프라인 입력 확인: OpenClaw sqlite로 도착/실행/미처리 판정과 재시작 시각 대조"
---

# 메시지 도착·유실 감사 (inbound audit)

## 언제 쓰나
"마지막으로 입력한 거 날아갔나?", "메시지 안 들어왔나?", "답장이 안 왔나?", "오프라인으로 보낸 게 도착했나?" 같은 질문.

## 판정 원칙
- 추측 금지. 독립 근거 2개 이상(입력 스캔 + 실행 로그 + 프로세스 기동 시각)이 일치할 때만 결론을 말한다.
- "도착 안 함" = 그 구간에 사용자 role 트랜스크립트 이벤트도 없고, 미처리 입력도 없음. 클라이언트가 서버로 넘기지 못한 것이다.
- 게이트웨이가 꺼져 있는 동안 들어온 입력은 서버에 흔적을 남기지 않으며 자동 복구되지 않는다. 사용자에게 그 내용을 다시 보내달라고 요청한다.
- 세션 가시성이 tree면 `sessions_list`/`sessions_search`에 다른 세션이 안 보인다. 감사는 DB 직접 조회로 한다.

## 절차
1. 구간을 확정한다: `session_status`로 현재 시각을 확인하고, 최근 6시간 또는 "마지막 정상 상호작용 이후"를 감사 구간으로 잡는다.
2. 감사 스크립트를 파일로 실행한다: `node <이 스킬 폴더>/scripts/audit-inbound.js 6` (인자는 시간 단위).
   - 이 호스트에 `sqlite3` CLI가 없으므로 node:sqlite를 쓰고, DB는 `readOnly: true`로 연다(게이트웨이 실행 중).
   - PowerShell에서 `node -e "..."`은 따옴표·한글 때문에 깨진다. 항상 `.js` 파일로 저장해 실행한다.
3. 출력 5개 섹션을 순서대로 해석한다.
   - [1] 사용자 입력 목록: 그 메시지가 있으면 도착. 없으면 [2]로 간다.
   - [2] 미처리 입력: `state`가 `queued`/`interrupted`면 "잃지 않았지만 자동 재생 안 됨" → 이어서 처리하거나 사용자에게 알린다. [1]·[2] 모두 비면 도착 안 함으로 판정.
   - [3] 실행 로그: `agent.run.started`가 있고 같은 `run_id`의 `finished`가 없으면 중단된 턴이다. 도구 결과는 불명으로 취급하고 그 턴을 마무리한다.
   - [4] 채널 수신 이벤트: `status=failed`나 `failed_reason`이 있으면 채널 단에서 실패한 것.
   - [5] 부팅 시각으로 실제 오프라인 구간을 잡고, `Get-Process node | Select Id,StartTime`(게이트웨이 실가동 시각)과 `~/.openclaw/logs/gateway-restart.log`(UTC 타임스탬프, KST = +9h)로 교차 확인한다.
4. 보고한다: 시간순 표(입력 · 재시작 · 답변) → 판정 한 줄 → 조치 한 줄(재입력 요청 또는 이어서 처리). 판정 문장에는 근거 테이블 이름을 붙여 검증 가능하게 한다.

## 저장소 (확인된 경로)
- 상태 DB `%USERPROFILE%\.openclaw\state\openclaw.sqlite`
  - `channel_ingress_events` — 채널별 수신 이벤트(`channel_id`, `lane_key`, `status`, `received_at`, `updated_at`, `failed_reason`). `payload_json`은 보통 null이므로 본문은 여기서 얻지 않는다.
  - `audit_events` — `kind='agent_run'`(action `agent.run.started`/`finished`, `session_key`, `run_id`), `kind='tool_action'`.
  - `delivery_queue_entries` — 발신 큐(`status`, `failed_at`, `enqueued_at`).
  - `gateway_boot_lifecycle` — `pid`, `started_at_ms` (부팅 시각).
- 에이전트 DB `%USERPROFILE%\.openclaw\agents\main\agent\openclaw-agent.sqlite`
  - `transcript_events` — `session_id` = `session_nodes.current_session_id`, `seq`, `event_json`(내부 `message.role`/`message.content`).
  - `session_pending_inputs` — `state`(queued/interrupted/cancelled), `accepted_at`, `message_json`.
  - `conversation_deliveries` — `send`/`turn` 상태(`status`: created|queued|sent|suppressed|rejected|unknown|replied).
  - 롤오버된 과거 창은 `session_nodes.current_session_id`에 없으므로, 그 구간은 `session_windows`에서 `session_key`로 창을 찾아 조회한다.
- 모든 타임스탬프는 epoch ms → `new Date(t).toLocaleString('ko-KR',{timeZone:'Asia/Seoul'})`.

## 검증
- 결론 전에 최소 두 근거를 대조한다. 예: "[1]에 입력 없음" + "[5] 그 시각 사이 부팅 2회" → 오프라인 구간 유실로 판정.
- 스크립트가 5개 섹션을 모두 출력하지 못하면(테이블/컬럼 누락) 그 사실을 사용자에게 말하고, 추정으로 답하지 않는다.
