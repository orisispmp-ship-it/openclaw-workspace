// 현장일기 GitHub 자동 백업 (스크립트 방식, 모델 호출 없음)
// git add -A → 변경 있으면 commit + push → notify(텔레그램 announce)
const dir = "C:\\Users\\orisi\\.openclaw\\workspace\\현장일기";
const d = new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10); // KST 날짜
await exec({ command: 'git -C "' + dir + '" add -A' });
const st = await exec({ command: 'git -C "' + dir + '" status --porcelain' });
const ch = String((st && (st.aggregated || st.output)) || "").trim();
if (!ch) return { notify: "📦 현장일기 백업: 변경 없음 (" + d + ")" };
await exec({ command: 'git -C "' + dir + '" commit -m "현장일기 백업 (' + d + ')"' });
await exec({ command: 'git -C "' + dir + '" push origin main' });
return { notify: "✅ 현장일기 백업 완료 (" + d + ")\n" + ch.split("\n").slice(0, 15).join("\n") };
