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

푸시 성공은 로컬 추적 ref로 검증한다: `git log --oneline origin/main..main`이 비어야 한다. 값이 남아 있으면 그 커밋은 GitHub에 없다. 자동 백업 스크립트도 push 결과를 스스로 확인하게 고친다(`push ... 2>&1 && echo __PUSH_OK__`를 실행하고 표식이 없으면 ❌로 보고). job payload가 스크립트를 인라인으로 들고 있으면 파일과 job을 함께 고친다.

워크스페이스 전체를 자동 커밋하는 스케줄을 걸기 전에 크기를 먼저 잰다: `Get-ChildItem -Recurse -File | Sort-Object Length -Descending | Select-Object -First 5`로 100MB 초과 파일을 찾고(GitHub는 파일당 100MB를 거부한다), `node_modules/`·업로드/출력 디렉터리 같은 재생성 가능 경로를 `.gitignore`에 넣는다. 그래도 걸지 여부는 사용자 확인을 받은 뒤 `automations`로 만들고 `runMode:"force"`로 한 번 실행해 알림 문구까지 검증한다.

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
