# ⚖️ OMNI-ARCHIVE 프로젝트 실행 규칙 (RULES.md)

> **Version:** 2.5 (High-Performance & Historical Integrity Optimized)
> **Principle:** 고지능적 사료 분석(Intelligence)과 의도적 불완전함(Humanizer)의 완벽한 조화.

---

## 1. 코딩 가이드라인 (Coding Standards)
- **비동기 프로그래밍:** 모든 I/O 작업(API 요청, 파일 시스템 접근, 크롤링)은 반드시 `async/await`를 사용한다.
- **의존성 고정:** 라이브러리 충돌 및 환경 재현성을 위해 `packaging<25`, `httpx<0.29` 범위를 엄격히 준수한다.
- **보안:** 모든 비밀 키(API Keys, DB Secret)는 `.env` 파일에서만 로드하며, 코딩 툴이 이를 코드에 직접 노출하지 않도록 감시한다.
- **모듈화:** 각 에이전트(Scout, Architect, Humanizer, Swarm)는 독립된 디렉토리와 파일로 관리하며, 기능 간 결합도를 최소화한다.

## 2. 콘텐츠 및 역사적 무결성 (Historical Integrity)
- **팩트 최우선:** `Scout` 에이전트가 가져온 논문 및 사료 데이터는 가공 전 원본 출처(URL/DOI)를 반드시 메타데이터로 보존한다.
- **페르소나 보존:** 인물의 성격과 가치관은 역사적 사실에 근거하되, 오직 **'놓여진 상황'**만을 현대적으로 비튼다. 역사 왜곡(왜곡된 사실 유포)은 절대 금지한다.
- **AI 탐지 회피:** 모든 최종 출력물은 `Humanizer` 모듈의 검증을 거쳐야 한다. 기계적인 완벽함이 감지될 경우 에러로 간주하고 재편집한다.

## 3. 리소스 및 성능 최적화 (Resource Management)
- **멀티쓰레딩:** Ryzen 7 5825U의 16쓰레드를 풀가동하기 위해 영상 합성 및 렌더링 시 `multiprocessing` 또는 `concurrent.futures`를 적극 활용한다.
- **지능형 캐싱:** `cache/` 폴더를 운영하여 동일한 논문 분석 결과나 이미지 생성 프롬프트에 대한 중복 호출을 방지하고 비용을 절감한다.
- **임시 파일 클리닝:** `temp/` 폴더에 생성되는 중간 렌더링 파일은 영상 합성이 완료되는 즉시 삭제하는 가비지 컬렉션 로직을 포함한다.

## 4. 멀티 에이전트 병렬 협업 규칙 (Multi-Agent Governance)
- **작업 영역 준수:** 에이전트 1(Scout)은 `src/agents/scout/`, 에이전트 2(Architect)는 `src/agents/architect/`와 같이 지정된 폴더 내부에서만 쓰기 권한을 가진다.
- **파일 잠금 원칙:** 동일한 파일을 두 에이전트가 동시에 수정하는 것은 절대 금지하며, 수정 전 반드시 파일의 최신 상태를 `read`하여 타 에이전트의 변경 사항을 동기화한다.
- **상태 공유(Sync):** 모든 에이전트는 작업을 시작할 때 `docs/` 내의 최신 PRD/TRD를 읽고, 종료 시 `docs/PROGRESS.md`에 작업 내용을 기록하여 동료 에이전트에게 알린다.
- **원자적 커밋:** 한 번의 작업으로 한 가지 모듈만 개선하며, 작업 완료 후 전체 시스템 영향도를 체크하기 위해 반드시 `connection_test.py`를 수행한다.

## 5. 예외 처리 및 복구 (Fail-safe)
- **API 폴백(Fallback):** 특정 API(예: Flux, Gemini Pro)가 응답하지 않을 경우, 즉시 하위 모델(Gemini Flash)이나 로컬 백업 자산을 사용하도록 설계한다.
- **로그 통합:** 모든 에이전트의 활동과 오류는 `logs/omni_system.log`에 실시간 기록하며, 중요 에러 발생 시 시스템을 중단하고 사용자에게 보고한다.

## 6. 버전 관리 및 문서화 (Git & Documentation)
- **README 우선주의:** 프로젝트의 주요 변경 사항은 즉시 `README.md`에 반영하여, 새로 투입되는 에이전트가 즉시 상황을 파악할 수 있게 한다.
- **의미 있는 커밋 (Conventional Commits):** 에이전트는 작업을 마칠 때마다 `git commit -m "feat: Scout 모듈 ArXiv 연동 완료"`와 같이 명확한 메시지를 남긴다.
- **자동 검증:** 모든 Pull Request나 Push 발생 시, GitHub Actions를 통해 `connection_test.py`를 자동 실행하여 시스템 무결성을 확인한다.
- **민감 정보 보호:** `.env` 파일과 `cache/`, `temp/` 폴더는 반드시 `.gitignore`에 등록하여 깃허브에 유출되지 않도록 철저히 관리한다.