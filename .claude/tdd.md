# TDD (Test-Driven Development) Guidelines

## TDD 사이클

```
RED → GREEN → REFACTOR
```

1. **RED**: 실패하는 테스트 작성
2. **GREEN**: 테스트를 통과하는 최소한의 코드 작성
3. **REFACTOR**: 중복 제거 및 코드 개선 (테스트는 통과 상태 유지)

## TDD의 3가지 법칙

1. 실패하는 단위 테스트를 작성하기 전에는 프로덕션 코드를 작성하지 않는다
2. 컴파일은 실패하지 않으면서 실행이 실패하는 정도로만 단위 테스트를 작성한다
3. 현재 실패하는 테스트를 통과할 정도로만 프로덕션 코드를 작성한다

## 테스트 작성 원칙

### F.I.R.S.T

- **Fast**: 빠르게 실행
- **Independent**: 독립적으로 실행 가능
- **Repeatable**: 반복 가능
- **Self-Validating**: 자체 검증 (bool 결과)
- **Timely**: 적시에 작성 (프로덕션 코드 직전)

### Given-When-Then 패턴

```typescript
test('사용자는 장바구니에 상품을 추가할 수 있다', () => {
  // Given: 초기 상태 설정
  const cart = new ShoppingCart()
  const product = new Product('Book', 10000)

  // When: 행동 실행
  cart.addProduct(product)

  // Then: 결과 검증
  expect(cart.getTotal()).toBe(10000)
  expect(cart.getItemCount()).toBe(1)
})
```

## 테스트 범위

1. **단위 테스트 (Unit Test)**: 함수/메서드 단위
2. **통합 테스트 (Integration Test)**: 모듈 간 연동
3. **E2E 테스트 (End-to-End Test)**: 전체 시스템 흐름

## 좋은 테스트 코드

- **하나의 개념만 테스트**: 하나의 assert 권장
- **테스트 이름은 명확하게**: 무엇을 테스트하는지 드러낼 것
- **테스트는 문서다**: 테스트를 읽으면 기능을 이해할 수 있어야 함
- **실패 메시지가 명확해야 함**

## Kent Beck의 TCR (Test && Commit || Revert)

```bash
test && commit || revert
```

- 테스트 통과 → 자동 커밋
- 테스트 실패 → 자동 Revert

극단적이지만 TDD의 정신을 잘 보여주는 방법론

## 테스트 더블

- **Dummy**: 인스턴스화만 되고 사용되지 않음
- **Stub**: 미리 준비된 답변 반환
- **Spy**: 호출 기록 저장
- **Mock**: 기대값 설정 및 검증
- **Fake**: 실제 동작하는 간단한 구현체

## 실전 팁

1. **테스트하기 쉬운 코드가 좋은 코드**
2. **프라이빗 메서드는 테스트하지 않는다** (공개 API를 통해 간접 테스트)
3. **테스트 코드도 리팩토링 대상**
4. **느린 테스트는 분리** (통합 테스트 등)
5. **CI/CD에서 자동 실행**

## 커버리지 목표

- **라인 커버리지**: 80% 이상 권장
- **브랜치 커버리지**: 70% 이상 권장
- **단, 100%가 목표는 아님**: 중요한 로직에 집중
