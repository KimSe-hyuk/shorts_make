# ⚖️ OMNI-ARCHIVE 프로젝트 실행 규칙 (RULES.md)

> **Version:** 2.8 (Autonomous Workflow & Security Optimized)
> **Principle:** 고지능적 사료 분석과 의도적 불완전함의 조화, 그리고 완전 자율형 보고 체계.

---

## 1. 코딩 가이드라인 (Coding Standards)
- **비동기 프로그래밍:** 모든 I/O 작업(API 요청, DB 접근, 크롤링)은 반드시 `async/await`를 사용한다.
- **의존성 고정:** 라이브러리 충돌 방지를 위해 `packaging<25`, `httpx<0.29` 범위를 준수한다.
- **보안:** 모든 비밀 키는 `.env` 파일에서만 로드하며, 절대 코드에 직접 노출하지 않는다.

## 2. 주석 및 문서화 (Documentation)
- **Docstring 필수:** 모든 클래스와 함수 상단에는 기능, 파라미터, 반환값을 명시한다.
- **한글 주석 권장:** 사령관의 직관적인 검수를 위해 모든 주석은 한국어로 작성한다.
- **README 최신화:** 주요 변경 사항은 즉시 프로젝트 루트의 `README.md`에 반영한다.

## 3. 콘텐츠 및 역사적 무결성 (Historical Integrity)
- **팩트 최우선:** 수집된 사료의 원본 출처(URL/DOI)를 메타데이터로 반드시 보존한다.
- **역사 왜곡 금지:** 인물의 성격은 고증에 따르되 상황만 현대적으로 비튼다.

## 4. 멀티 에이전트 협업 규칙 (Multi-Agent Governance)
- **작업 영역 격리:** 각 에이전트는 지정된 폴더 내에서만 쓰기 권한을 가진다.
- **파일 잠금:** 동일 파일을 중복 수정하지 않으며, 작업 전 최신 상태를 `read`한다.

## 5. 리소스 및 성능 최적화 (Resource Management)
- **멀티쓰레딩:** Ryzen 7 5825U의 쓰레드를 활용하기 위해 렌더링 시 `multiprocessing`을 사용한다.
- **지능형 캐싱:** `cache/` 폴더를 운영하여 중복 API 비용을 절감한다.

## 6. 예외 처리 및 복구 (Fail-safe)
- **API 폴백:** 장애 발생 시 하위 모델(Gemini Flash)이나 로컬 백업으로 즉시 전환한다.

## 7. 자원 효율화 및 검증 수칙 (Resource Optimization & Verification) - [REVISED]
- **쿼터 방어 (Quota Defense):** 로직 수정 및 단위 테스트 단계에서는 실제 API 호출을 금지하고, 반드시 'Mock 데이터' 또는 'Cached Response'를 사용한다.
- **선택적 검증 (Selective Verification):** 전체 시스템 부하를 줄이기 위해 수정된 모듈만 선별하여 테스트한다. (예: `python connection_test.py --module scout`)
- **예외 조항 (Force Push Protocol):** 외부 API 장애 또는 쿼터 초과(Rate Limit) 발생 시, 사령관(User)의 명시적 승인 하에 연결 검증 단계를 우회하여 배포할 수 있다.
- **자동 푸시 실행:** 검증 통과 시 표준 절차에 따라 `git push`를 수행한다.
