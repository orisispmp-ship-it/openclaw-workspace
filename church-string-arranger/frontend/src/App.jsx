import React, { useEffect, useRef, useState } from 'react'
import { api } from './api.js'
import { scoreToText, textToScore, DEFAULT_TEXT } from './score.js'

const STEPS = ['1. 악보 준비', '2. 악보 확인/수정', '3. 편곡 설정', '4. 결과']

export default function App() {
  const [step, setStep] = useState(0)
  const [samples, setSamples] = useState([])
  const [instruments, setInstruments] = useState(null)
  const [scoreJson, setScoreJson] = useState(null)   // 편곡할 악보
  const [editorText, setEditorText] = useState(DEFAULT_TEXT)
  const [editorDirty, setEditorDirty] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')
  const [uploadOcr, setUploadOcr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [result, setResult] = useState(null)
  const [pdfBlobUrl, setPdfBlobUrl] = useState('')
  const fileRef = useRef(null)

  // 설정
  const [arrangement, setArrangement] = useState('duo')
  const [transposeTo, setTransposeTo] = useState('')
  const [tempo, setTempo] = useState('')
  const [lyricsOn, setLyricsOn] = useState(true)
  const [pageSize, setPageSize] = useState('A4')
  const [lang, setLang] = useState('kr')
  const [pageNumbers, setPageNumbers] = useState(true)

  useEffect(() => {
    api.samples().then((s) => setSamples(s.samples)).catch(() => setServerDown(true))
    api.instruments().then((i) => setInstruments(i)).catch(() => setServerDown(true))
    api.health().then(() => setServerDown(false)).catch(() => setServerDown(true))
  }, [])

  const [serverDown, setServerDown] = useState(false)

  async function loadSample(id) {
    setBusy(true); setErr(''); setUploadMsg(''); setUploadOcr(null)
    try {
      const res = await fetch(api.sampleMusicxml(id))
      const blob = await res.blob()
      const file = new File([blob], `${id}.musicxml`, { type: 'application/xml' })
      const up = await api.upload(file)
      setScoreJson(up.score)
      setEditorText(scoreToText(up.score))
      setEditorDirty(false)
      setUploadMsg(`샘플 "${up.score.title}" 불러옴 — ${up.score.measures.length}마디`)
      setStep(1)
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  async function onUpload(file) {
    setBusy(true); setErr(''); setUploadMsg(''); setUploadOcr(null)
    try {
      const up = await api.upload(file)
      if (up.type === 'musicxml') {
        setScoreJson(up.score)
        setEditorText(scoreToText(up.score))
        setEditorDirty(false)
        setUploadMsg(`악보 파싱 완료 — ${up.score.title} (${up.score.measures.length}마디, ${up.score.key}조)`)
        setStep(1)
      } else {
        setUploadOcr(up.ocr)
        setUploadMsg(up.message)
        setStep(1)
      }
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  function applyEditor() {
    setErr('')
    try {
      const sc = textToScore(editorText)
      if (!sc.measures.length) { setErr('멜로디가 비어 있습니다'); return }
      setScoreJson(sc)
      setEditorDirty(false)
      setUploadMsg(`편집 내용 반영 — ${sc.measures.length}마디`)
      setStep(2)   // 다음 단계(편곡 설정)로 이동
    } catch (e) { setErr('악보 파싱 실패: ' + e.message) }
  }

  async function runArrange() {
    setBusy(true); setErr('')
    let sc = scoreJson
    if (editorDirty) {
      try { sc = textToScore(editorText) } catch (e) { setErr('악보 파싱 실패: ' + e.message); setBusy(false); return }
    }
    if (!sc || !sc.measures.length) { setErr('악보가 없습니다 — 1단계에서 악보를 먼저 불러오세요'); setBusy(false); return }
    try {
      const req = {
        score: sc,
        arrangement,
        transpose_to: transposeTo || null,
        tempo: tempo ? parseInt(tempo, 10) : null,
        lyrics_on: lyricsOn,
        page_size: pageSize,
        lang,
        page_numbers: pageNumbers,
      }
      const r = await api.arrange(req)
      setResult(r)
      setStep(3)                       // 결과 화면으로 즉시 이동
      // PDF 미리보기는 별도 로드 (실패해도 화면은 유지)
      loadPreview(r.pdf)
    } catch (e) { setErr('편곡 실패: ' + e.message) } finally { setBusy(false) }
  }

  async function loadPreview(pdfPath) {
    try {
      const blob = await (await fetch(pdfPath)).blob()
      if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl)
      setPdfBlobUrl(URL.createObjectURL(blob))
    } catch (e) {
      setErr('PDF 미리보기를 불러오지 못했습니다 — 다운로드 버튼은 사용 가능합니다.')
    }
  }

  function reset() {
    setScoreJson(null); setResult(null); setPdfBlobUrl(''); setUploadMsg(''); setUploadOcr(null)
    setEditorText(DEFAULT_TEXT); setEditorDirty(false); setStep(0)
  }

  return (
    <div className="wrap">
      <header>
        <h1>🎻 Church String Arranger</h1>
        <p>교회 현악 연주자를 위한 AI 자동 편곡 — 바이올린 2중주 · 현악 4중주</p>
      </header>

      {serverDown && (
        <div className="banner err">🔌 백엔드 서버에 연결할 수 없습니다 — <code>cd backend && python run.py</code> 로 서버를 시작해 주세요.</div>
      )}

      <nav className="steps">
        {STEPS.map((s, i) => (
          <div key={s} className={'step ' + (i === step ? 'active' : '') + (i < step ? 'done' : '')}
               onClick={() => i < step && setStep(i)}>
            {s}
          </div>
        ))}
      </nav>

      {err && <div className="banner err">⚠️ {err}</div>}
      {uploadMsg && <div className="banner ok">✅ {uploadMsg}</div>}

      {step === 0 && (
        <section className="card">
          <div className="drop" onClick={() => fileRef.current.click()}
               onDragOver={(e) => e.preventDefault()}
               onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) onUpload(f) }}>
            <div className="drop-icon">📄</div>
            <div><b>PDF / 이미지 / MusicXML 업로드</b></div>
            <div className="hint">PDF · JPG · PNG · 사진 촬영 · 스캔 이미지 · MusicXML(.musicxml/.mxl)</div>
          </div>
          <input ref={fileRef} type="file" hidden
                 accept=".pdf,.png,.jpg,.jpeg,.bmp,.musicxml,.mxl,.xml"
                 onChange={(e) => { if (e.target.files[0]) onUpload(e.target.files[0]); e.target.value = '' }} />
          <div className="or">— 또는 샘플 찬송가로 시작 —</div>
          <div className="samples">
            {samples.map((s) => (
              <button key={s.id} className="sample-btn" disabled={busy} onClick={() => loadSample(s.id)}>
                <span className="sample-title">{s.title}</span>
                <span className="sample-meta">{s.key} · {s.time}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {step === 1 && (
        <section className="card">
          {uploadOcr && (
            <div className="ocr-info">
              <b>🔍 이미지 분석 결과:</b> 오선 {uploadOcr.detected_staves}개 감지
              <div className="hint">{uploadOcr.message}</div>
            </div>
          )}
          <div className="editor-head">
            <b>악보 편집기</b>
            <span className="hint">오선 위 음표 · 코드 · 가사를 텍스트로 입력/수정 (마디는 | 로 구분)</span>
          </div>
          <textarea className="editor" rows={12} value={editorText}
                    onChange={(e) => { setEditorText(e.target.value); setEditorDirty(true) }} />
          <div className="hint">
            음표: <code>G4</code> 4분 · <code>G4:2</code> 2분 · <code>G4.</code> 점4분 · <code>G4:0.5</code> 8분 ·
            <code>R</code> 쉼표 · <code>F#4</code> 올림표 · <code>Bb4</code> 내림표
          </div>
          <div className="btn-row">
            <button className="primary" onClick={applyEditor}>반영하고 편곡하기 →</button>
            <button onClick={reset}>← 처음으로</button>
          </div>
        </section>
      )}

      {step === 2 && (
        <section className="card">
          <h3>편곡 설정</h3>
          <div className="grid">
            <label>편곡 형태
              <select value={arrangement} onChange={(e) => setArrangement(e.target.value)}>
                <option value="duo">바이올린 2중주</option>
                <option value="quartet">현악 4중주</option>
              </select>
            </label>
            <label>조 변경 {instruments && <span className="hint">(원곡: {scoreJson?.key || '?'})</span>}
              <select value={transposeTo} onChange={(e) => setTransposeTo(e.target.value)}>
                <option value="">변경 안 함</option>
                {(instruments?.keys || []).filter((k) => k !== scoreJson?.key).map((k) => <option key={k} value={k}>{k}</option>)}
              </select>
            </label>
            <label>템포 (♩)
              <input type="number" min={40} max={200} placeholder={scoreJson?.tempo || '90'}
                     value={tempo} onChange={(e) => setTempo(e.target.value)} />
            </label>
            <label>용지
              <select value={pageSize} onChange={(e) => setPageSize(e.target.value)}>
                <option value="A4">A4</option>
                <option value="Letter">Letter</option>
              </select>
            </label>
            <label>악기명
              <select value={lang} onChange={(e) => setLang(e.target.value)}>
                <option value="kr">한글</option>
                <option value="en">영문</option>
              </select>
            </label>
            <label className="check">
              <input type="checkbox" checked={lyricsOn} onChange={(e) => setLyricsOn(e.target.checked)} /> 가사 표시
            </label>
            <label className="check">
              <input type="checkbox" checked={pageNumbers} onChange={(e) => setPageNumbers(e.target.checked)} /> 페이지 번호
            </label>
          </div>
          <div className="btn-row">
            <button className="primary" disabled={busy} onClick={runArrange}>
              {busy ? '편곡 중...' : '🎵 편곡 실행'}
            </button>
            <button onClick={() => setStep(1)}>← 악보 수정</button>
          </div>
        </section>
      )}

      {step === 3 && result && (
        <section className="card">
          <div className="result-head">
            <h3>{result.title}</h3>
            <span className="badge">{result.arrangement_label}</span>
            <span className="badge">{result.key}조</span>
            <span className="badge">♩ = {result.tempo}</span>
            <span className="badge">{result.measures}마디</span>
          </div>
          <div className="preview">
            {pdfBlobUrl ? <iframe src={pdfBlobUrl} title="미리보기" /> : <div className="hint">PDF 생성 중...</div>}
          </div>
          <div className="btn-row">
            <a className="primary" href={result.pdf} download>⬇ PDF 다운로드</a>
            <a href={result.musicxml} download>MusicXML</a>
            <a href={result.midi} download>MIDI</a>
            <button onClick={() => { setStep(2); setResult(null); setPdfBlobUrl('') }}>설정 변경</button>
            <button onClick={reset}>새 악보</button>
          </div>
          <div className="hint">⚠️ 저작권: 업로드한 악보의 이용 권한을 확인하세요. 출력물은 예배용으로만 사용하세요.</div>
        </section>
      )}

      <footer>
        Church String Arranger MVP · FastAPI + React · 악보 OCR(OMR) 엔진 연동 준비됨
      </footer>
    </div>
  )
}
