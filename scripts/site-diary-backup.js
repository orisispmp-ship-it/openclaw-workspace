// 현장일기 GitHub 자동 백업 (스크립트 방식, 모델 호출 없음)
// v1 2026-09-11: push 실패를 "✅ 완료"로 보고하던 조용한 실패 버그 수정
// v2 2026-09-11: 이 환경의 exec은 Windows PowerShell 5.1 → `&&` 사용 불가.
//   push 성공 여부는 $LASTEXITCODE 로 확인하고, 미푸시 커밋이 남아 있으면 재푸시를 시도한다.
const dir = "C:/Users/orisi/.openclaw/workspace/현장일기";
const d = new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10); // KST 날짜
const out = (r) => String((r && (r.aggregated || r.output)) || "");
const step = async (cmd) => out(await exec({ command: cmd }));

await step('git -C "' + dir + '" add -A');
const ch = (await step('git -C "' + dir + '" status --porcelain')).trim();
let committed = false;
if (ch) {
  await step('git -C "' + dir + '" commit -m "현장일기 백업 (' + d + ')"');
  committed = true;
}
const ahead = (await step('git -C "' + dir + '" log --oneline origin/main..main')).trim();
if (!ahead) return { notify: "📦 현장일기 백업: 변경 없음 (" + d + ")" };
const push = await step('git -C "' + dir + '" push origin main 2>&1; "PUSH_EXIT=$LASTEXITCODE"');
if (!push.includes("PUSH_EXIT=0")) {
  const tail = push.trim().split("\n").slice(-6).join("\n");
  return { notify: "❌ 현장일기 백업 push 실패 (" + d + ")\n로컬 커밋은 보존됨(다음 실행에서 재시도)\n" + tail };
}
return { notify: "✅ 현장일기 백업 완료 (" + d + ")\n" + (committed ? ch.split("\n").length + "개 파일 변경" : "이전 미푸시 커밋 푸시") + "\n" + ahead.split("\n").slice(0, 10).join("\n") };
