// OpenClaw 수신 감사: 도착한 사용자 입력 / 미처리 입력 / 실행 로그 / 채널 수신 / 게이트웨이 부팅
// 사용법: node audit-inbound.js [hours=6]
// 읽기 전용으로만 연다. sqlite3 CLI 없는 호스트에서 node:sqlite 사용.
const { DatabaseSync } = require('node:sqlite');
const os = require('os');
const path = require('path');

const hours = Number(process.argv[2] || 6);
const root = path.join(process.env.USERPROFILE || os.homedir(), '.openclaw');
const state = new DatabaseSync(path.join(root, 'state', 'openclaw.sqlite'), { readOnly: true });
const agent = new DatabaseSync(path.join(root, 'agents', 'main', 'agent', 'openclaw-agent.sqlite'), { readOnly: true });
const kst = (t) => (t == null ? '(없음)' : new Date(Number(t)).toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }));
const flat = (s) => String(s == null ? '' : s).replace(/\s+/g, ' ');
const since = Date.now() - hours * 3600 * 1000;
const out = [];

out.push(`== 기준 ${kst(Date.now())} | 최근 ${hours}시간 (since ${kst(since)}) ==`);

const names = new Map(
  agent.prepare('select current_session_id, session_key from session_nodes').all()
    .map((r) => [r.current_session_id, r.session_key]),
);

out.push('\n[1] 도착한 사용자 입력 (최신순)');
let seen = 0;
for (const r of agent.prepare('select session_id, seq, created_at, event_json from transcript_events where created_at >= ? order by created_at desc limit 300').all(since)) {
  let ev;
  try { ev = JSON.parse(r.event_json); } catch { continue; }
  const m = ev.message || {};
  if (m.role !== 'user') continue;
  const text = typeof m.content === 'string'
    ? m.content
    : Array.isArray(m.content)
      ? m.content.map((c) => c.text || `[${c.type}]`).join(' ')
      : '';
  out.push(`${kst(r.created_at)} | ${names.get(r.session_id) || r.session_id} | seq=${r.seq} | ${flat(text).slice(0, 250)}`);
  seen++;
}
if (!seen) out.push('(없음) → 이 구간에 도착한 사용자 입력 없음');

out.push('\n[2] 미처리 입력 (session_pending_inputs, 최신 10)');
for (const r of agent.prepare('select seq, session_key, state, accepted_at, message_json from session_pending_inputs order by seq desc limit 10').all())
  out.push(`#${r.seq} ${kst(r.accepted_at)} | ${r.session_key} | ${r.state} | ${flat(r.message_json).slice(0, 160)}`);

out.push('\n[3] 에이전트 실행 (audit_events kind=agent_run)');
const runs = state.prepare("select occurred_at, action, status, session_key, run_id from audit_events where kind='agent_run' and occurred_at >= ? order by occurred_at asc").all(since);
for (const r of runs) out.push(`${kst(r.occurred_at)} | ${r.action} | ${r.status} | ${r.session_key}`);
const started = runs.filter((r) => r.action === 'agent.run.started').map((r) => r.run_id);
const finished = new Set(runs.filter((r) => r.action === 'agent.run.finished').map((r) => r.run_id));
const unfinished = [...new Set(started)].filter((id) => !finished.has(id));
if (!runs.length) out.push('(없음)');
out.push(`시작 ${new Set(started).size} / 완료 ${finished.size} / 미완료 run_id: ${unfinished.join(', ') || '없음'}`);

out.push('\n[4] 채널 수신 이벤트 (channel_ingress_events, 최신 10)');
for (const r of state.prepare('select channel_id, lane_key, status, received_at, updated_at, failed_reason from channel_ingress_events order by received_at desc limit 10').all())
  out.push(`${kst(r.received_at)} | ${r.channel_id} | ${r.lane_key} | ${r.status} | ${flat(r.failed_reason)}`);

out.push('\n[5] 게이트웨이 부팅 (gateway_boot_lifecycle, 최신 5)');
for (const r of state.prepare('select pid, started_at_ms from gateway_boot_lifecycle order by started_at_ms desc limit 5').all())
  out.push(`${kst(r.started_at_ms)} | pid=${r.pid}`);
out.push('실가동 시각 대조: Get-Process node | Select Id,StartTime / ~/.openclaw/logs/gateway-restart.log (UTC, KST=+9h)');

console.log(out.join('\n'));
