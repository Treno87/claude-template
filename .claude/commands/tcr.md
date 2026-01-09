---
description: TCR(Test && Commit || Revert)을 실행합니다.
---
# Role
당신은 냉혹한 심판관입니다.

# Task
아래 논리를 쉘 명령어로 실행하세요.
`npm test && git add . && git commit -m "feat: TCR passed" || git reset --hard`

(프로젝트에 따라 npm test 대신 다른 테스트 명령어가 필요하면 수정해서 실행하세요)
