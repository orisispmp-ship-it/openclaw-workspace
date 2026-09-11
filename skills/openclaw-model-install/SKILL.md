---
name: "openclaw-model-install"
description: "모델 설치·추가 요청 시: 공식 API로 ID 실존 확인 후 config 백업·등록·검증 (model install, add model, 모델 추가)"
---

# OpenClaw 모델 설치·추가 (verify then register)

사용자가 OpenClaw에서 쓸 새 모델을 "설치/추가해 달라"고 하면(예: "deepseek v4.1 flash 설치해줘"), 추측 ID로 config를 먼저 고치지 않는다. 존재하지 않거나 아직 활성화되지 않은 모델을 등록하면 사용 시 400 오류가 나는 죽은 항목이 되므로, **실존 확인이 등록보다 먼저**다.

## 절차

1. 정확한 모델 ID와 활성 여부를 공식 경로로 확인한다.
   - 프로바이더 공식 문서·변경로그(예: DeepSeek는 api-docs.deepseek.com/updates)와 대조하고, 비공식 블로그/SEO 도메인은 근거로 쓰지 않는다.
   - 호스트에 주입된 키 env(예: `$env:DEEPSEEK_API_KEY`)로 공식 API에 직접 조회한다. 키 값은 절대 출력·로그에 남기지 않는다.
     - `GET {baseUrl}/models` → 응답 `data[].id` 목록에 있는지 확인.
     - 후보 ID로 최소 호출(`chat/completions`, `max_tokens=1`): 200이면 활성. 400이면 오류 메시지("supported API model names are ...")가 실제 지원 ID 목록을 알려주므로 그것을 기준으로 재확인.
   - 확인 실패(미활성/미존재) 시 등록하지 말고, 출시·활성화 시점(가격 적용 시각 등)을 사용자에게 보고한다. CLI 프로브(`openclaw agent --model ...`)는 세션 복구 상태에 따라 실패할 수 있어 API 직접 조회가 신뢰 경로다.

2. 등록 대상 위치를 연다: `~/.openclaw/openclaw.json` → `models.providers.<provider>.models` 배열. 같은 프로바이더의 기존 형제 모델 항목(`id`, `name`, `api`, `reasoning`, `input`, `cost`, `contextWindow`, `maxTokens`)을 복사해 템플릿으로 쓴다. `cost`(1M 토큰 USD: input/output/cacheRead/cacheWrite)는 프로바이더 공식 가격표 값으로 새 모델에 맞게 바꾼다.

3. 백업 후 등록한다: `openclaw.json`을 `openclaw.json.bak-<yyyyMMdd-HHmm>`으로 복사한 뒤, models 배열에 새 항목만 추가하는 대상 수정으로 넣는다(파일 전체 교체 금지). 설정 파일에는 평문 자격증명(프로바이더 키, `gateway.auth.token`)이 들어 있으므로 광범위 패턴으로 파일을 훑지 말고 필요한 줄 범위만 읽어 출력에 키가 섞이지 않게 한다.

4. 게이트웨이가 오버라이드를 거부하면 정책에 허용을 추가한다. `openclaw agent --model <provider>/<id>`가 "Model override ... is not allowed for agent ... by agents.defaults.modelPolicy.allow"로 실패하면 `agents.defaults.modelPolicy.allow` 배열에 `<provider>/<id>`를 추가한다(대상 수정).

5. 검증하고 보고한다.
   - 1단계의 최소 호출을 새 모델 ID로 다시 실행해 200 OK가 나오는지 확인.
   - 엔드투엔드: `openclaw agent -m "Reply with exactly: OK" --model <provider>/<id> --session-key agent:main:<고유키> --json` → `status: ok`이고 `meta.model`이 새 ID인지 확인. `--local`은 게이트웨이가 떠 있으면 "failed to acquire gateway state ownership"으로 실패하고, `--session-key`를 생략하면 기본 세션(`agent:main:main`)이 복구 상태에 따라 깨져 있으니 항상 고유 세션 키를 명시한다.
   - `openclaw models list`로 등록 노출 확인.
   - 사용자에게 결과(모델명·모델 ID·적용 가격 기준)를 짧게 보고한다. 기본 모델 변경 요청이 없었다면 기본값은 건드리지 않는다. 기존 ID가 alias로 남아 신모델을 서빙 중이면 그 사실도 알리고, 기본값 교체는 사용자 선택으로 남긴다.
