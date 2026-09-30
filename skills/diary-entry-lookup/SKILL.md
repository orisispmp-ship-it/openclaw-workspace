---
name: "diary-entry-lookup"
description: "일기 보여줘·나의 일기·현장일기·회사일기 기록/조회: 파일 위치, 미기록 날짜 판정, 원본 근거 확인"
---

# 일기 조회·기록

"일기 보여줘", "9/21~9/23 일기", "나의 일기 :", "현장일기 :", "회사일기" 요청에 쓴다.

## 파일 위치 (고정)

- "나의 일기 :" → `~/.openclaw/workspace/현장일기/나의일기/YYYY-MM-DD.md`
- "현장일기 :" · "회사일기 :" → `~/.openclaw/workspace/현장일기/YYYY-MM-DD.md`
- 커밋·푸시는 `github-backup-connect` 3단계(현장일기 저장소) 그대로, 메시지는 `현장일기 백업 (YYYY-MM-DD)`.

완료 기준: 저장한 파일에서 유이사님이 말한 문장을 그대로 확인.

## 기록할 때

- 유이사님이 준 고유명사(업체·사람·제품)는 교정하거나 추측하지 않고 그대로 쓴다. 이상해 보여도 그대로 넣고, 정말 막힐 때만 한 번 짧게 묻는다. (2026-09-30 "11번가"를 음성 오인식으로 추정했다가 정정받음)
- 날짜를 말하면 그 날짜 파일에 넣는다. 오늘 파일에 밀어 넣지 않는다.
- 정정 요청이 오면 파일을 고치고 같은 메시지 형식으로 다시 커밋·푸시한다.

## 날짜 범위 조회

1. 실제 파일부터 확정한다: `Get-ChildItem ~/.openclaw/workspace/현장일기 -Recurse -File` 과 `git -C ~/.openclaw/workspace/현장일기 log --date=short --name-status`로 존재하는 날짜 목록을 얻는다.
2. 없는 날짜는 "그 날짜 기록 없음"이라고 먼저 말한다. 파일을 만들어 채우거나 내용을 추측하지 않는다.
3. 그 날짜에 유이사님이 실제로 무엇을 보냈는지 확인이 필요하면 읽기 전용으로 조회한다: `~/.openclaw/agents/main/agent/openclaw-agent.sqlite`(URI `file:...?mode=ro`)의 `session_transcript_fts`에서 `role='user'` + timestamp(ms epoch) 구간, 그리고 `workspace/memory/.dreams/session-corpus/YYYY-MM-DD.txt`.
   - `python -c`에 따옴표를 중첩하면 문법 오류가 난다 → `workspace/tmp/*.py` 파일로 쓴다.
   - 한국어 결과는 콘솔에서 깨진다 → UTF-8 파일로 쓰고 `read`로 읽는다.
4. `memory/dreaming/{light,deep,rem}/`와 `session-corpus`는 AI 요약이므로 일기 원본이 아니다. 원본 판정은 1번의 파일·git 이력으로만 한다.

완료 기준: 존재하는 날짜 목록과, 없으면 없다는 명시와, 필요하면 그 날짜의 실제 사용자 메시지 근거까지 제시.

## 답변

- 미기록 날짜는 단정하되 근거(파일 목록·git 이력) 한 줄을 붙인다.
- 유이사님이 내용을 불러주면 그 날짜 파일로 만들어 백업한다.
