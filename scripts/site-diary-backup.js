// 현장일기 GitHub 자동 백업 (스크립트 방식, 모델 호출 없음)
// v1 2026-09-11: push 실패를 "✅ 완료"로 보고하던 조용한 실패 버그 수정
// v2 2026-09-11: 이 환경의 exec은 Windows PowerShell 5.1 → `&&` 사용 불가
// v3 2026-09-11: push 출력 캡처도 불안정 → push 전/후 GitHub 원격 SHA 비교로 성공/실패 판정
const dir = "C:/Users/orisi/.openclaw/workspace/현장일기";
const d = new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10); // KST 날짜
const out = (r) => String((r && (r.aggregated || r.output || r.result)) || "");
const step = async (cmd) => out(await exec({ command: cmd }));
const remoteSha = async () => (await step('git -C "' + dir + '" ls-remote origin refs/heads/main')).trim().split(/\s+/)[0];

await step('git -C "' + dir + '" add -A');
const ch = (await step('git -C "' + dir + '" status --porcelain')).trim();
let committed = false;
if (ch) {
  await step('git -C "' + dir + '" commit -m "현장일기 백업 (' + d + ')"');
  committed = true;
}
const localSha = (await step('git -C "' + dir + '" rev-parse main')).trim();
const before = await remoteSha();
if (before && before === localSha) return { notify: "📦 현장일기 백업: 변경 없음 (" + d + ")" };
const pushOut = String((await step('git -C "' + dir + '" push origin main 2>&1')) || "").trim();
const after = await remoteSha();
if (after !== localSha) {
  const detail = (pushOut || "(push 출력 없음)").split("\n").slice(-8).join("\n");
  return { notify: "❌ 현장일기 백업 push 실패 (" + d + ")\n로컬 커밋은 보존됨(다음 실행에서 재시도)\n" + detail };
}
return { notify: "✅ 현장일기 백업 완료 (" + d + ")\n" + (committed ? String(ch.split("\n").length) + "개 파일 변경" : "이전 미푸시 커밋 푸시") + "\n원격 확인: " + after.slice(0, 7) };
