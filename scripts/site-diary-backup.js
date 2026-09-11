// 현장일기 GitHub 자동 백업 (스크립트 방식, 모델 호출 없음)
// git add -A → 변경 있으면 commit + push → notify(텔레그램 announce)
// 2026-09-11 수정: push 실패를 "✅ 완료"로 보고하던 조용한 실패 버그 수정
//   - push 결과를 확인해 실패 시 ❌ + 오류 메시지 + 미푸시 커밋 안내
//   - 변경은 없지만 미푸시 커밋이 남아 있으면 ⚠️ 로 알림
const dir = "C:/Users/orisi/.openclaw/workspace/현장일기";
const d = new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10); // KST 날짜
const out = (r) => String((r && (r.aggregated || r.output)) || "");
const step = async (cmd) => out(await exec({ command: cmd }));

await step('git -C "' + dir + '" add -A');
const ch = (await step('git -C "' + dir + '" status --porcelain')).trim();
if (!ch) {
  const drift = (await step('git -C "' + dir + '" log --oneline origin/main..main')).trim();
  if (drift) return { notify: "⚠️ 현장일기 백업: 새 변경은 없지만 GitHub에 안 올라간 커밋이 있습니다 (" + d + ")\n" + drift };
  return { notify: "📦 현장일기 백업: 변경 없음 (" + d + ")" };
}
await step('git -C "' + dir + '" commit -m "현장일기 백업 (' + d + ')"');
const push = await step('git -C "' + dir + '" push origin main 2>&1 && echo __PUSH_OK__');
if (!push.includes("__PUSH_OK__")) {
  const tail = push.trim().split("\n").slice(-5).join("\n");
  return { notify: "❌ 현장일기 백업 push 실패 (" + d + ")\n커밋은 로컬에 만들어졌습니다(" + ch.split("\n").length + "개 파일).\n" + tail };
}
return { notify: "✅ 현장일기 백업 완료 (" + d + ")\n" + ch.split("\n").slice(0, 15).join("\n") };
