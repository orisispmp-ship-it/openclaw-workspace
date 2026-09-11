// API 클라이언트
const BASE = ''

async function j(method, path, body, isForm, timeoutMs = 60000) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeoutMs)
  const opts = { method, headers: {}, signal: ctrl.signal }
  try {
    if (body && !isForm) {
      opts.headers['Content-Type'] = 'application/json'
      opts.body = JSON.stringify(body)
    } else if (body && isForm) {
      opts.body = body
    }
    const res = await fetch(BASE + path, opts)
    if (!res.ok) {
      let msg = `서버 오류 (${res.status})`
      try {
        const jd = await res.json()
        if (jd.detail) msg = typeof jd.detail === 'string' ? jd.detail : JSON.stringify(jd.detail)
      } catch (e) { /* noop */ }
      throw new Error(msg)
    }
    return res.json()
  } catch (e) {
    if (e.name === 'AbortError') throw new Error('요청 시간 초과 — 서버가 응답하지 않습니다. 서버가 실행 중인지 확인하세요.')
    throw new Error(e.message === 'Failed to fetch' ? '서버에 연결할 수 없습니다. 백엔드 서버(127.0.0.1:8000)가 실행 중인지 확인하세요.' : e.message)
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  health: () => j('GET', '/api/health', null, false, 8000),
  samples: () => j('GET', '/api/samples', null, false, 8000),
  instruments: () => j('GET', '/api/instruments', null, false, 8000),
  sampleMusicxml: (id) => `${BASE}/api/samples/${id}/musicxml`,
  upload: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return j('POST', '/api/upload', fd, true, 30000)
  },
  arrange: (req) => j('POST', '/api/arrange', req, false, 90000),
}
