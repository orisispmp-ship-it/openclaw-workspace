// 현장일기 GitHub 자동 백업 (스크립트 방식, 모델 호출 없음)
// v1: push 실패를 "✅ 완료"로 보고하던 조용한 실패 버그 수정
// v2: 이 환경의 exec은 Windows PowerShell 5.1 → `&&` 사용 불가
// v3: push 출력 캡처가 불안정 → 원격 SHA 비교 시도
// v4: exec이 성공 시 출력을 비워 반환 → push 후 `origin/main..main` 이 비었는지로 성공 판정
const dir = "C:/Users/orisi/.openclaw/workspace/현장일기";
const d = new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10); // KST 날짜
const out = (r) => String((r && (r.aggregated || r.output || r.result || r.text)) || "");
const step = async (cmd) => out(await exec({ command: cmd }));
const drift = async () => (await step('git -C "' + dir + '" log --oneline origin/main..main')).trim();

await step('git -C "' + dir + '" add -A');
const ch = (await step('git -C "' + dir + '" status --porcelain')).trim();
let committed = false;
if (ch) {
  await step('git -C "' + dir + '" commit -m "현장일기 백업 (' + d + ')"');
  committed = true;
}
let pending = await drift();
if (!pending) return { notify: "📦 현장일기 백업: 변경 없음 (" + d + ")" };
let pushErr = "";
try { pushErr = String((await step('git -C "' + dir + '" push origin main 2>&1')) || "").trim(); } catch (e) { pushErr = String((e && (e.message || e)) || "").trim(); }
pending = await drift();
if (pending) {
  return { notify: "❌ 현장일기 백업 push 실패 (" + d + ")\n미푸시 커밋:\n" + pending.split("\n").slice(0, 6).join("\n") + (pushErr ? "\n" + pushErr.split("\n").slice(-6).join("\n") : "") };
}
return { notify: "✅ 현장일기 백업 완료 (" + d + ")\n" + (committed ? String(ch.split("\n").length) + "개 파일 변경" : "이전 미푸시 커밋 푸시") };
