# 🎻 Church String Arranger (교회 현악 편곡기)

교회 현악 연주자를 위한 **AI 자동 편곡 앱 MVP**. PDF/이미지 악보(또는 MusicXML)를 업로드하면
바이올린 2중주 또는 현악 4중주로 자동 편곡하고, **가사를 유지한 채 PDF로 출력**합니다.

> PRD 기반 구현 — FastAPI(백엔드) + React(Vite, 프론트엔드)

---

## ✨ 기능 (MVP)

| 단계 | 기능 | 상태 |
|---|---|---|
| 1 | 업로드 (PDF / JPG / PNG / 사진 / 스캔 / MusicXML) | ✅ |
| 2 | 악보 OCR — **오선(staff) 자동 감지** + 수정 가능한 편집기 | ✅ (음표 단위 OMR은 엔진 연동 포인트) |
| 3 | 자동 편곡 — **바이올린 2중주 / 현악 4중주** (규칙 기반 화성 엔진) | ✅ |
| 4 | 가사 유지 + **PDF 출력** (A4/Letter, 페이지 번호) | ✅ |
| 5 | **MusicXML 저장** + MIDI 내보내기(재생용) | ✅ |
| 6 | 조 변경(Key), 템포 변경, 악기명 한글/영문, 가사 표시/숨기기 | ✅ |

**편곡 규칙 (PRD 반영)**
- 자연스러운 화성: 코드 톤 우선 3도/6도 진행
- 연주하기 쉬운 운지: 도약 최소화, 악기 음역(clamp) 준수
- 멜로디 유지: 바이올린 1 = 원곡 멜로디 (가사 포함)
- 예배용 편곡: 절제된 리듬, 첼로 베이스 + 비올라 필러

## 📁 구조

```
church-string-arranger/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI 서버 + API
│   │   ├── model.py       # 음악 데이터 모델 (Note/Chord/Score)
│   │   ├── harmony.py     # 규칙 기반 화성/편곡 엔진
│   │   ├── musicxml.py    # MusicXML 읽기/쓰기
│   │   ├── engraver.py    # PDF 악보 조판기 (matplotlib)
│   │   ├── ocr.py         # 악보 OCR 인터페이스 (오선 감지)
│   │   └── samples.py     # 내장 샘플 찬송가 3곡
│   ├── requirements.txt
│   └── run.py
├── frontend/              # React (Vite)
│   └── src/               # App.jsx, score.js(에디터), api.js, styles.css
└── README.md
```

## 🚀 실행 방법

### 백엔드
```bash
cd backend
pip install -r requirements.txt
python run.py          # http://127.0.0.1:8000
```

### 프론트엔드 (개발 모드)
```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (API 프록시 내장)
```
또는 프로덕션 빌드 후 백엔드가 직접 서빙:
```bash
cd frontend && npm run build   # dist/ 생성 → 백엔드가 자동 서빙
```

## 🔌 API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/health` | 상태 확인 |
| GET | `/api/samples` | 샘플 찬송가 목록 |
| GET | `/api/samples/{id}/musicxml` | 샘플 MusicXML 다운로드 |
| GET | `/api/instruments` | 악기/편곡 옵션/조(key) 목록 |
| POST | `/api/upload` | 파일 업로드 (PDF/이미지→오선 감지, MusicXML→파싱) |
| POST | `/api/arrange` | 편곡 실행 → PDF/MusicXML/MIDI 반환 |
| GET | `/api/output/{file}` | 생성 파일 다운로드 |

## 📝 악보 편집기 형식

```
제목: 주 은혜
조: G
박자: 4/4
템포: 84
코드: G | G D G | ...
멜로디: G4 G4 A4 G4 | B4 G4 G4 | ...
가사: 나 같은 죄인 살리신 | 주 은혜 놀라워 | ...
```
- `G4` 4분음표 · `G4:2` 2분 · `G4.` 점4분 · `G4:0.5` 8분 · `R` 쉼표 · `F#4`/`Bb4` 임시표
- 마디 구분은 `|`

## ⚠️ 현재 한계 & 향후 계획

- **음표 단위 OCR(OMR)**: 오선 감지까지 자동. 음표 인식은 연구급 문제라
  `backend/app/ocr.py`에 OMR 엔진(Audiveris 등) 연동 인터페이스를 마련해 두었고,
  MVP에서는 **편집기로 입력/수정**하는 흐름 제공 (PRD의 "OCR 결과 수정 기능" 충족).
- **향후**: 난이도 선택, 오케스트라 버전, 피아노+현악 편곡, 코드/인트로/간주/엔딩 자동 생성
- **저작권**: 업로드한 악보의 이용 권한 확인 필요. 출력물은 예배용으로만.

## 📜 라이선스 주의
샘플 곡은 퍼블릭 도메인 멜로디(Amazing Grace, Ode to Joy, Nettleton) 기반이며,
샘플 가사는 데모용 원문입니다. 실제 사용 시 해당 찬송가의 저작권(번역 포함)을 확인하세요.
