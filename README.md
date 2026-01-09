# Claude Template

새 프로젝트 시작 시 일관된 `.claude` 환경을 즉시 세팅할 수 있는 템플릿 저장소입니다.

## 특징

- 🎯 **TDD & Clean Code 가이드라인** 포함
- 🔒 **권한 설정 템플릿** (settings.json)
- 🪝 **Hooks**: Biome 자동 포맷팅, 음성 알림
- 🛠️ **커스텀 Commands**: /beck, /refactor, /tidy, /tcr, /verify
- 🖥️ **Windows (PowerShell) + WSL/Linux/Mac** 지원

## 설치

### 1. 템플릿 저장소 클론

```bash
# WSL/Linux/Mac
git clone https://github.com/Treno87/claude-template.git ~/.claude-template

# Windows PowerShell
git clone https://github.com/Treno87/claude-template.git $HOME\.claude-template
```

### 2. 프로젝트에 적용

프로젝트 루트 디렉토리에서:

```bash
# WSL/Linux/Mac
~/.claude-template/setup.sh

# Windows PowerShell
~\.claude-template\setup.ps1
```

스크립트는 자동으로:
- 기존 `.claude` 디렉토리를 백업 (타임스탬프 포함)
- 템플릿을 현재 디렉토리에 복사
- Hook 실행 권한 설정 (Unix 계열)
- `settings.local.json` 생성 (gitignore 대상)

## 디렉토리 구조

```
.claude/
├── CLAUDE.md              # 핵심 프로젝트 가이드라인 (간결하게)
├── clean-code.md          # Clean Code 원칙
├── tdd.md                 # TDD 가이드라인
├── settings.json          # Claude 권한 설정 + Hooks 설정
├── settings.local.json    # 로컬 전용 설정 (gitignore)
├── hooks/
│   ├── biome/
│   │   └── post-write.ps1 # 파일 저장 시 Biome 자동 포맷팅
│   └── voice_notifications/ # 작업 완료 음성 알림
├── commands/
│   ├── beck.md            # Kent Beck 4원칙 리뷰
│   ├── refactor.md        # 즉시 리팩토링
│   ├── tidy.md            # 코드 정리 + 커밋
│   ├── tcr.md             # Test && Commit || Revert
│   └── verify.md          # 테스트 실행
├── skills/
│   └── voice-notification/ # 음성 알림 커스텀 스킬
└── plugins/               # MCP 플러그인 설정 (필요시)
```

## 사용법

### 프로젝트별 커스터마이징

1. **CLAUDE.md 수정**: Tech Stack, Commands, Rules를 프로젝트에 맞게 수정
2. **settings.json 수정**: 필요한 권한 추가/제거
3. **settings.local.json**: 로컬 환경별 설정 (gitignore 대상)

### Hooks

#### Pre-commit Hook
- Biome가 설치되어 있고 `biome.json`이 있으면 자동으로 실행
- 스테이징된 파일에 대해 lint/format 체크
- 실패 시 커밋 중단

#### Post-task Hook
- Claude 작업 완료 시 음성 알림
- macOS: `say` 사용
- Linux: `espeak` 사용
- WSL: PowerShell TTS 사용

### 템플릿 업데이트

```bash
# WSL/Linux/Mac
cd ~/.claude-template && git pull

# Windows PowerShell
cd $HOME\.claude-template; git pull
```

업데이트 후 프로젝트에 다시 `setup.sh` 또는 `setup.ps1` 실행

## 권장 워크플로우

1. **새 프로젝트 생성**
   ```bash
   mkdir my-project && cd my-project
   ~/.claude-template/setup.sh
   ```

2. **CLAUDE.md 커스터마이징**
   - Tech Stack 명시
   - 프로젝트별 규칙 추가

3. **개발 시작**
   - TDD 사이클 준수: RED → GREEN → REFACTOR
   - Clean Code 원칙 적용
   - Pre-commit hook으로 코드 품질 유지

4. **템플릿 동기화**
   - 주기적으로 `~/.claude-template` 업데이트
   - 개선사항을 템플릿에 반영

## 파일 설명

### CLAUDE.md
- Claude가 매번 읽는 핵심 가이드라인
- **간결하게 유지** (500토큰 이하 권장)
- 상세한 내용은 별도 `.md`로 분리하여 `@참조` 사용

### settings.json
- Claude의 파일 접근 및 명령 실행 권한 설정
- `allow`: 허용할 작업
- `deny`: 명시적으로 거부할 작업

### settings.local.json
- 로컬 환경별 설정 (gitignore 대상)
- 개인 선호 설정, 로컬 경로 등

## 토큰 최적화 팁

- **CLAUDE.md**: 핵심만 작성, 상세 내용은 `@clean-code.md`, `@tdd.md` 참조
- **hooks, commands, plugins**: 토큰에 영향 없음
- **skills**: 필요할 때만 참조되므로 자유롭게 추가

## 기여

개선 사항이나 버그 수정은 Pull Request 환영합니다!

## 라이센스

MIT

## 참고 자료

- [Claude Code 공식 문서](https://github.com/anthropics/claude-code)
- [Clean Code - Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)
- [TDD by Example - Kent Beck](https://www.oreilly.com/library/view/test-driven-development/0321146530/)
