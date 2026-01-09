# Claude Template 프로젝트 계획

## 목표

새 프로젝트 시작 시 일관된 `.claude` 환경을 즉시 세팅할 수 있는 Git 템플릿 repo 생성

## 환경

- Windows PowerShell + WSL2 Ubuntu 양쪽에서 사용
- Git repo로 관리하여 동기화/버전관리/백업

---

## 폴더 구조

```
claude-template/
├── .claude/
│   ├── CLAUDE.md           # 핵심 규칙 (간결하게, @참조 활용)
│   ├── clean-code.md       # Clean Code 원칙
│   ├── tdd.md              # TDD 가이드라인
│   ├── settings.json       # 권한 설정
│   ├── settings.local.json # 로컬 전용 (gitignore 대상)
│   ├── commands/           # 커스텀 슬래시 명령어
│   │   └── .gitkeep
│   ├── hooks/              # pre-commit, post-task 등
│   │   ├── pre-commit      # Biome 체크
│   │   └── post-task       # 음성 알림
│   ├── skills/             # 기술 스택별 가이드
│   │   └── .gitkeep
│   └── plugins/            # MCP 플러그인 설정
│       └── .gitkeep
├── setup.sh                # WSL/Linux용 설치 스크립트
├── setup.ps1               # PowerShell용 설치 스크립트
├── .gitignore
└── README.md
```

---

## 작업 순서

### Phase 1: 기본 구조 생성

- [ ] 폴더 구조 생성
- [ ] .gitkeep 파일 추가

### Phase 2: 핵심 파일 작성

- [ ] CLAUDE.md (간결하게, 500토큰 이하)
- [ ] clean-code.md
- [ ] tdd.md
- [ ] settings.json

### Phase 3: Hooks 작성

- [ ] pre-commit (Biome lint/format 체크)
- [ ] post-task (음성 알림 - Windows/Mac/Linux 분기)

### Phase 4: 설치 스크립트

- [ ] setup.sh (WSL/Linux/Mac)
- [ ] setup.ps1 (PowerShell)
- [ ] 기존 .claude 백업 로직 포함

### Phase 5: 문서화

- [ ] README.md (설치/사용법)
- [ ] .gitignore (settings.local.json 등)

### Phase 6: Git 설정

- [ ] git init
- [ ] GitHub repo 생성 및 push

---

## 파일 내용 가이드

### CLAUDE.md (예시)

```markdown
# Project Guidelines

## Core Principles

- TDD: 테스트 먼저 작성
- Clean Code: @clean-code.md 참조
- Tidying: 리팩토링은 별도 커밋

## Tech Stack

[프로젝트별 수정]

## Commands

- /review: 코드 리뷰
- /refactor: 리팩토링 제안

## Rules

- 한국어로 응답
- 변경 전 설명
```

### settings.json (예시)

```json
{
  "permissions": {
    "allow": ["Read(*)", "Write(./*)", "Bash(npm:*, pnpm:*, git:*, biome:*)"],
    "deny": ["Write(~/*)", "Bash(rm -rf *)"]
  }
}
```

### pre-commit hook (예시)

```bash
#!/bin/bash
# Biome check before commit
npx biome check --staged || exit 1
```

### post-task hook (예시)

```bash
#!/bin/bash
# 음성 알림
if [[ "$OSTYPE" == "darwin"* ]]; then
    say "작업 완료"
elif command -v espeak &> /dev/null; then
    espeak "작업 완료"
elif command -v powershell.exe &> /dev/null; then
    powershell.exe -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('작업 완료')"
fi
```

---

## 사용법 (완성 후)

### 최초 설치

```bash
# WSL/Linux
git clone git@github.com:YOUR_ID/claude-template.git ~/.claude-template

# PowerShell
git clone git@github.com:YOUR_ID/claude-template.git $HOME\.claude-template
```

### 프로젝트에 적용

```bash
# WSL
~/.claude-template/setup.sh

# PowerShell
~\.claude-template\setup.ps1
```

### 템플릿 업데이트

```bash
cd ~/.claude-template && git pull
```

---

## 메모

- CLAUDE.md는 매번 로드되므로 간결하게 유지
- 상세 규칙은 별도 .md로 분리하여 @참조
- hooks, commands, settings.json은 토큰 영향 없음
- skills, commands는 필요할 때 추가
