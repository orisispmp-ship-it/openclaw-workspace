---
name: "github-backup-connect"
description: "GitHub 백업 연결 요청 시: 워크스페이스 git vs openclaw backup git 대상 판정, 자격증명 확인, 커밋·원격 푸시"
---

# GitHub 백업 연결

"GitHub 백업 연결", "워크스페이스 백업", "openclaw backup git" 요청을 받으면 먼저 무엇을 백업할지 판정하고, 그 다음 호스트 상태를 확인한 뒤 연결한다.

## 1. 백업 대상 판정

- 문서·메모리·스킬 등 워크스페이스 파일 → 2단계 워크스페이스 git 백업.
- 세션·설정·자격증명이 든 SQLite 상태 → 4단계 `openclaw backup git`.
- 에이전트 도구(`gh`, `github_publish`)용 신원만 필요 → Control UI **Agents → Tools → GitHub Identity → Connect GitHub**(device flow, `repo`/`workflow`/`read:org`/`gist` 승인).

GitHub Identity 연결은 git credential helper를 설치하지 않으므로 그것만으로 `git push` 인증이 되지 않는다. 사용자가 신원 연결만 요청했더라도 이 차이를 먼저 밝힌다.

## 2. 워크스페이스 git 백업

호스트 상태를 확인한다.

```powershell
cd ~/.openclaw/workspace
git status; git remote -v; git rev-list --count HEAD; git config --get-all credential.helper; gh --version
```

- 커밋 0개이거나 remote가 없으면 아직 백업되지 않는 상태라고 보고에 명시한다.
- `credential.helper=manager`(GCM)가 있어도 저장된 자격증명이 없으면 HTTPS 푸시는 실패한다. 서비스·예약작업 컨텍스트에서는 `git ls-remote`가 `Unable to persist credentials with the 'wincredman' credential store`로 종료되고 프롬프트도 불가하므로 HTTPS+GCM은 이 호스트에서 못 쓴다고 판정한다.
- 자격증명 유무는 `cmdkey /list`(빈 목록이면 없음), `$env:GH_TOKEN`·`$env:GITHUB_TOKEN`, OpenClaw `secrets list`로 확인한다. 셋 다 비어 있으면 푸시 인증 수단이 없다고 먼저 보고한 뒤 SSH 경로로 간다.

`.gitignore`가 없으면 만들고, 비밀 파일과 런타임 산출물을 제외한다: `.env`, `**/*.key`, `**/*.pem`, `**/secrets*`, `tmp/`, `state/`, `.openclaw/`, `node_modules/`.

핵심 파일만 초기 커밋한다(전체 `git add .` 금지).

```powershell
git add .gitignore AGENTS.md SOUL.md IDENTITY.md USER.md memory skills scripts
git commit -m "Add agent workspace"
```

커밋 전 스테이징 내용에서 키·토큰 패턴을 스캔하고, 검출되면 커밋하지 않고 사용자에게 알린다.

원격 URL을 받으면 그 저장소가 이미 다른 프로젝트 전용인지 먼저 확인한다(`git -C <해당폴더> remote -v`, `git -C <해당폴더> log --oneline origin/main`). 남의 내용이 올라가 있는 저장소에 워크스페이스를 밀면 파일이 섞이고 이력이 달라 push가 거부되며, 강제 푸시는 그 백업을 파괴한다 → 별도 private 저장소 URL을 요청한다.

인증 수단이 없으면 SSH 키로 간다.

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\id_ed25519_github" -N '""' -C "backup@<호스트>"
```

`~/.ssh/config`에 `Host github.com` / `IdentityFile ~/.ssh/id_ed25519_github` / `IdentitiesOnly yes`를 쓰고, 공개키(`.pub`)를 사용자에게 보여 https://github.com/settings/ssh/new 등록을 요청한다(계정 키 하나로 모든 저장소 커버, deploy key는 저장소별이며 `Allow write access` 필요). 등록 전 `ssh -T git@github.com`이 `Permission denied (publickey)`인 것은 정상이다.

```powershell
git branch -M main
git remote add origin git@github.com:<계정>/<저장소>.git
ssh -T git@github.com
git push -u origin main
```

푸시 성공은 로컬 추적 ref로 검증한다: `git log --oneline origin/main..main`이 비어야 한다. 값이 남아 있으면 그 커밋은 GitHub에 없다. 자동 백업 스크립트의 성공 판정도 이 상태 비교로만 한다. 이 환경의 exec은 Windows PowerShell 5.1이라 `&&`가 문법 오류이고, 성공한 명령의 출력을 빈 값으로 돌려주며, 기본 yield(10초)를 넘긴 push는 백그라운드로 돌리고 먼저 반환한다. 그래서 `push ... && echo __PUSH_OK__`나 push 출력 캡처는 성공한 푸시를 ❌로 오탐한다.

```javascript
const out = (r) => String((r && (r.aggregated || r.output || r.result || r.text)) || "");
const run = async (cmd, ms) => out(await exec({ command: cmd, yieldMs: ms || 120000 }));
const drift = async () => (await run('git -C "' + dir + '" log --oneline origin/main..main')).trim();
await run('git -C "' + dir + '" push origin main 2>&1');
for (let i = 0; i < 3 && (await drift()); i++) await run('Start-Sleep -Seconds 5', 30000);
// drift()가 비면 ✅, 남으면 ❌ + 미푸시 커밋 목록
```

job payload가 스크립트를 인라인으로 들고 있으면 파일과 job을 함께 고친다(`automations` get으로 payload를 확인).

전체 백업 푸시가 `GH013 Repository rule violations`와 `Push cannot contain secrets`로 거부되면 Push Protection이 코드에 박힌 키를 찾은 것이고, 그 키는 원격에 올라가지 않았다. unblock URL은 쓰지 않는다(비밀을 원격에 허용하게 된다). 코드를 고치는 방향으로 처리한다: 비밀을 `**/*.local` 같은 gitignore 대상 파일로 옮기고, 코드는 `process.env.<NAME> || readFileSync(new URL('./<파일>', import.meta.url), 'utf-8').trim()`으로 읽게 한 뒤 `git add -A` → `git commit --amend` → 재푸시한다. 고친 뒤 `git grep -l -I -E "sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}" origin/main`이 0건인지 확인하고, 평문으로 존재했던 키는 재발급을 권한다.

워크스페이스 전체를 자동 커밋하는 스케줄을 걸기 전에 비밀과 크기를 먼저 잰다: `git grep -l -I -E "sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}"`로 키를 찾고, `Get-ChildItem -Recurse -File | Sort-Object Length -Descending | Select-Object -First 5`로 100MB 초과 파일을 찾고(GitHub는 파일당 100MB를 거부한다), `node_modules/`·업로드/출력 디렉터리 같은 재생성 가능 경로를 `.gitignore`에 넣는다. 그래도 걸지 여부는 사용자 확인을 받은 뒤 `automations`로 만들고 `runMode:"force"`로 한 번 실행해 알림 문구까지 검증한다.

보고에는 커밋 해시, 스테이징 파일 수, 푸시 검증 결과를 포함한다. 이후 워크스페이스 변경은 같은 저장소에 커밋·푸시한다.

## 3. 상태 백업 스케줄

원격 저장소를 먼저 만든 뒤에만 스케줄을 건다. `--push`는 origin remote가 없으면 거부된다.

```powershell
openclaw backup git init --repository ~/Backups/openclaw-git --remote <원격URL>
openclaw backup enable --repository ~/Backups/openclaw-git --every 24h --push
```

자동 푸시 기본 덤프에는 자격증명이 포함되므로 원격은 private으로 유지하고, redact된 이력이면 `--exclude-secrets`를 함께 쓴다. 되돌릴 때는 `openclaw backup disable`.

## 참조

- 워크스페이스 git 백업·`.gitignore`: `docs/concepts/agent-workspace.md`
- 아카이브·스냅샷·Git 백업·복원: `docs/install/backups.md`, `docs/cli/backup.md`
- `tools.github` 신원 범위·PAT 폴백: `docs/gateway/config-tools.md`
