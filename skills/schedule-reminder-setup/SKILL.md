---
name: "schedule-reminder-setup"
description: "현장 일정·마감 알림 등록: 기억 기록 + 텔레그램 아침 리마인더(delivery.to 필수)"
---

# 현장 일정 리마인더 등록

## 언제 쓰나
유이사님이 날짜가 붙은 일정 목록을 그대로 전달하거나("평택현장일정 (…9/28)(…10/1)"), 특정 마감일에 "알림 걸어줘"라고 할 때.

## 절차
1. 일정을 표로 정리해 `MEMORY.md`의 해당 섹션(보통 `## 업무`)에 한 줄 추가하고, `memory/YYYY-MM-DD.md`에 단계·날짜·비고 표를 남긴다. 완료 기준: 두 파일 모두에서 날짜와 단계를 확인할 수 있다.
2. 단계마다 `automations` add로 일회성 알림을 만든다. 공통 필드:
   - `schedule`: `{kind:"at", at:"<UTC ISO>"}`. KST 09:00 = 같은 날짜의 `T00:00:00Z`.
   - `sessionTarget:"isolated"`, `wakeMode:"now"`, `deleteAfterRun:true`.
   - `payload`: `{kind:"agentTurn", message:"…"}`. 메시지에 오늘 날짜·단계명, 전체 일정 나열, "짧게 한두 줄로 알려주세요"를 넣는다.
   - `delivery`: `{mode:"announce", channel:"telegram", to:"telegram:<chatId>"}`.
3. `to` 값은 추측하지 말고, 배달에 성공 중인 기존 작업에서 읽어 그대로 쓴다: `automations get` → "손자병법 명구 매일 전송" → 그 `delivery.to` 복사. 완료 기준: 새 작업의 `delivery.to`가 그 성공 작업과 동일하다.
4. 마감일이 있는 단계는 하루 전(D-1) 점검 알림도 함께 만든다.
5. 만든 작업의 `id`와 `nextRunAtMs`를 확인해 사용자에게 단계 표 + 알림 목록으로 보고한다.

## 함정
- `delivery.channel:"telegram"`만 넣고 `to`를 빠뜨리면 실행 시 `Delivering to Telegram requires target <chatId>`로 **발송 실패**한다. 기존 작업을 점검하다 이 상태를 발견하면 `delivery.to`를 채워 고친다.
- 만든 알림을 `run`(force)으로 테스트하면 어긋난 날짜 문구(예: "오늘(M/D)")가 실제로 전송된다. 검증은 force 실행이 아니라 `delivery.to` 비교와 `nextRunAtMs` 확인으로 한다.
- `automations` 툴 수정이 소유자 정책으로 막히면 CLI(`openclaw automations edit`)를 쓴다.
- 등록해 둔 미래 일회성 알림이 실행 전에 목록에서 사라진 사례가 있다.

## 일정 확인 요청

"○○일정 확인해줘" 요청을 받으면 등록 이력과 현재 목록을 대조한다.

1. `MEMORY.md` 해당 항목에서 단계·날짜와 등록된 job id를 찾는다.
2. `automations` list(`includeDisabled:true`)로 현재 작업 목록을 받아 job id를 맞춰본다.
3. 이력에는 있는데 목록에 없으면 그 자리에서 다시 `automations` add로 등록하고, `MEMORY.md`의 job id를 새 값으로 바꾼다. 완료 기준: 단계·상태 표 + 대조 결과 + 재등록 job id를 보고한다.

유이사님 현장 약어 **임사 = 임시사용승인**. 이 약어로 물으면 `MEMORY.md` `## 업무`의 임시사용승인 항목을 바로 확인한다.
