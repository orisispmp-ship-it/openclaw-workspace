---
name: "us-stock-market-recap"
description: "US stock market recap / 미국 증시 요약 (Dow, S&P, Nasdaq close & intraday): session-timing check, fetch order, verified sources."
---

# US Stock Market Recap (미국 증시 요약)

트리거: "미국 증시/주식 시장 요약", "US stock market recap", 다우/S&P 500/나스닥 마감가·장중 현황 문의.

## Steps

1. **세션 상태부터 판별** — 숫자를 확정치로 소개하기 전에. 미국 정규장 마감 = 16:00 ET. ET는 서머타임(3월 중순~11월 초) UTC−4, 그 외 UTC−5. 현재 UTC가 미국 평일 16:00 ET 이전이면 **그 세션은 아직 진행 중**이므로 S&P/다우/나스닥 수치는 "장중"으로 라벨링하고, 직전 완료 마감치를 확정 데이터로 제시한다. 진행 중 세션의 리캡 기사는 16:00 ET 이후에야 나온다. (한국시간 기준 여름엔 오전 5시, 겨울엔 오전 6시 마감 — 새벽 4~5시 문의가 장중일 수 있음.)
2. **https://tradingeconomics.com/united-states/stock-market 페치** — 현재 세션 요약문(지수 % 변동, 상승/하락 동인, 주요 종목 움직임)과 매크로 표(CPI·기준금리·실업률)가 바로 읽힌다. 본문에서 세션 날짜를 확인(예: "on September 9, 2026")하고, 수치는 실시간/CFD 기준임을 감안한다.
3. **https://dowjonestoday.net/ 페치** — 가장 최근 완료된 다우 마감가: 지수, 변동(포인트+%), Dow 30 상승/하락 리더, 52주 최고점 대비 거리. 미국 장 마감 후 매일 갱신된다.
4. **오늘자 헤드라인·단일 종목 동향** (특히 장중) 은 Google News RSS로: `https://news.google.com/rss/search?q=<URL-인코딩 쿼리 + when:1d>&hl=en-US&gl=US&ceid=US:en`. `<item>`의 `<title>`·`<pubDate>`를 파싱한다. **item의 `<link>`는 절대 페치하지 말 것** — Google News 기사 리다이렉트는 JS 필요해서 빈 페이지만 돌아온다.
5. **사용자 언어로 답 작성** (보통 한국어): 세션 상태 라벨 → 지수 레벨/변동 → 주요 동인(유가·지정학·금리·실적) → 눈에 띄는 종목. 세션이 아직 진행 중이면 마감 후 확정치를 다시 정리해주겠다고 제안한다.

## Pitfalls (실패 검증됨 — 먼저 시도하지 말 것)

- **web_search 연속 호출**은 DuckDuckGo 봇 챌린지를 유발한다(2회째 실패 확인). 헤드라인은 Google News RSS로.
- **AP News(apnews.com)** 403 Cloudflare, **CNBC 일일 라이브블로그 URL**은 추측 시 404, **Yahoo Finance 시세 페이지**는 헤더 오버플로, **stockanalysis.com/markets**는 404. 이 소스들로 시작하지 않는다.
- web_fetch 결과가 잘리면 인라인 한도를 넘는 부분이 temp 로그 파일로 떨어지고(spill 경로가 결과에 표시됨), 그 파일을 PowerShell 정규식으로 파싱해 `<item>`들을 뽑아낼 수 있다.

주간·장기 맥락(1주/1개월/연초 대비 등)이 필요하면 dowjonestoday.net의 성과 표를 그대로 쓴다. 안전자산(금) 가격과 유가도 동향 문의 시 같은 페이지들에서 함께 확인된다.
