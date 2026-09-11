// 악보 텍스트 에디터 ↔ Score JSON 변환
// 형식:
//   제목: 주 은혜
//   조: G
//   박자: 4/4
//   템포: 84
//   코드: G | G D G | ...
//   멜로디: G4 G4 A4 G4 | B4 G4 G4 | ...
//   가사: 나 같은 죄인 살리신 | 주 은혜 놀라워 | ...
//
// 음표 토큰: G4 (4분), G4:2 (2분), G4. (점4분), G4:0.5 (8분), R (4분쉼), R:2, F#4, Bb4

const STEPS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
const DEFAULT_BEATS = 4

export function parseNoteToken(tok) {
  if (!tok) return null
  let t = tok.trim()
  if (!t) return null
  let duration = 1.0
  let dots = 0
  // 지속 시간
  const dm = t.match(/:(0?\.?\d+)$/)
  if (dm) { duration = parseFloat(dm[1]); t = t.replace(/:\d+(\.\d+)?$/, '') }
  if (t.endsWith('.')) { dots = 1; duration = duration * 1.5; t = t.slice(0, -1) }
  if (t.toUpperCase() === 'R') return { is_rest: true, duration, dots }
  const m = t.match(/^([A-Ga-g])(#|b)?(\d)$/)
  if (!m) return null
  return {
    step: m[1].toUpperCase(),
    alter: m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0,
    octave: parseInt(m[3], 10),
    duration,
    dots,
    is_rest: false,
    lyric: '',
  }
}

export function noteToToken(n) {
  if (n.is_rest) return 'R' + (n.duration !== 1 ? ':' + n.duration : '')
  const acc = n.alter > 0 ? '#' : n.alter < 0 ? 'b' : ''
  let t = `${n.step}${acc}${n.octave}`
  const dur = n.duration
  if (Math.abs(dur - 1.5) < 0.01) t += '.'
  else if (Math.abs(dur - 1.0) > 0.01) t += ':' + dur
  return t
}

// Score JSON → 에디터 텍스트
export function scoreToText(score) {
  const lines = []
  lines.push(`제목: ${score.title}`)
  lines.push(`작곡: ${score.composer || ''}`)
  lines.push(`조: ${score.key}`)
  lines.push(`박자: ${score.time[0]}/${score.time[1]}`)
  lines.push(`템포: ${score.tempo}`)
  const chordLines = []
  const melLines = []
  const lyrLines = []
  for (const m of score.measures) {
    chordLines.push(m.chords[0] ? m.chords[0] : '-')
    melLines.push(m.notes.map(noteToToken).join(' '))
    lyrLines.push(m.notes.map((n) => n.lyric || '_').join(' '))
  }
  lines.push(`코드: ${chordLines.join(' | ')}`)
  lines.push(`멜로디: ${melLines.join(' | ')}`)
  lines.push(`가사: ${lyrLines.join(' | ')}`)
  return lines.join('\n')
}

// 에디터 텍스트 → Score JSON
export function textToScore(text) {
  const meta = { title: '제목 없음', composer: '', key: 'C', time: [4, 4], tempo: 90 }
  const sections = {}
  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim()
    const mm = line.match(/^([가-힣A-Za-z]+)\s*:\s*(.*)$/)
    if (!mm) continue
    const k = mm[1]
    const v = mm[2].trim()
    if (k === '제목') meta.title = v
    else if (k === '작곡') meta.composer = v
    else if (k === '조') meta.key = v
    else if (k === '박자') {
      const [a, b] = v.split('/')
      meta.time = [parseInt(a) || 4, parseInt(b) || 4]
    } else if (k === '템포') meta.tempo = parseInt(v) || 90
    else sections[k] = v
  }
  const measures = []
  const chords = (sections['코드'] || '').split('|').map((s) => s.trim())
  const mels = (sections['멜로디'] || '').split('|').map((s) => s.trim())
  const lyrs = (sections['가사'] || '').split('|').map((s) => s.trim())
  const count = Math.max(chords.length, mels.length)
  for (let i = 0; i < count; i++) {
    const notes = (mels[i] || '').split(/\s+/).filter(Boolean).map(parseNoteToken).filter(Boolean)
    const lyrToks = (lyrs[i] || '').split(/\s+/).filter(Boolean)
    notes.forEach((n, j) => {
      const l = lyrToks[j]
      if (l && l !== '_' && l !== '-') n.lyric = l
    })
    measures.push({
      chords: chords[i] && chords[i] !== '-' ? [chords[i]] : [],
      notes,
    })
  }
  return { ...meta, measures }
}

export const DEFAULT_TEXT = `제목: 주 은혜
작곡: 전통 찬송
조: G
박자: 4/4
템포: 84
코드: G | G D G | G C G D | G | G C G | D D G Em | C G D D | G C G | G D G
멜로디: G4 G4 A4 G4 | B4 G4 G4 | G4 G4 A4 G4 | C5 B4 G4 | D5 D5 B4 A4 | G4 A4 B4 | G4 A4 G4 E4 | D4 D4
가사: 나 같은 죄인 살리신 | 주 은혜 놀라워 | 잃었던 생명 찾았네 | 주 은혜 놀라워 | 나 같은 죄인 살리신 | 주 은혜 놀라워 | 잃었던 생명 찾았네 | 주 은혜 놀라워`
