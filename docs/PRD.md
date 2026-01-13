# 🛸 OMNI-ARCHIVE: 자율형 초지능 역사 소환 제국

> **Project Level:** State-of-the-Art (SOTA) Autonomous Content Engine
> **Core Concept:** 역사적 팩트(논문/사료) 기반 인물의 현대적 재구성 및 자율형 쇼츠 생성 시스템
> **Architecture:** OMNI-OS (Hybrid Local-Cloud)

---

## 1. 프로젝트 비전 (Vision)
단순한 정보 전달을 넘어, 역사적 인물의 실제 성격과 업적을 현대적 상황에 배치하여 '근거 있는 병맛' 서사를 구축합니다. AI가 만들었지만 인간의 정성이 느껴지는 'Ghost Engine' 기술을 통해 플랫폼 알고리즘을 지배하고 글로벌 미디어 수익을 창출합니다.

---

## 2. 시스템 아키텍처 (Hybrid Infrastructure)

### [Local: Command & Control]
- **Hardware:** Ryzen 7 5825U Optimized
- **Engine:** Python, FastAPI, LangGraph
- **Role:** 에이전트 지휘, 데이터 크롤링, 최종 영상 물리 합성 (MoviePy/OpenCV)

### [Cloud: Intelligence & Assets]
- **Models:** Gemini 1.5 Pro (Deep Reasoning), Flux/Sora (Visual), Edge-TTS
- **Role:** 논문 분석, 시나리오 추론, 고화질 이미지/영상 생성

### [Database: Dual-Intelligence]
- **Supabase (SQL):** 콘텐츠 로그, 성과 지표(Retention, 수익) 관리
- **Pinecone (Vector):** 인물별 페르소나, 논문 요약, 성공 시나리오 패턴 저장(RAG)

---

## 3. 에이전틱 워크플로우 (Swarm Intelligence)

| 에이전트 | 미션 (Mission) | 핵심 기술 (Core Logic) |
| :--- | :--- | :--- |
| **The Scout** | **심층 데이터 채굴** | ArXiv, 역사 논문 DB, Reddit 비동기 크롤링 및 지식 추출 |
| **The Architect** | **시공간 변환 설계** | 팩트 기반 인물을 현대 상황(SNS, 경영, 연애 등)에 배치한 대본 생성 |
| **The Humanizer** | **적대적 엔지니어링** | 미세 흔들림, 가우시안 노이즈, 숨소리 삽입으로 AI 탐지 회피 |
| **The Swarm Master** | **글로벌 군집 관리** | 다국어 최적화 및 멀티 채널 자율 배포 및 피드백 수집 |

---

## 4. 핵심 기술 명세 (Technical Specs)

### 🛠️ Adversarial Humanizer (알고리즘 해킹)
- **Visual Jitter:** OpenCV를 이용한 프레임별 ±1~2px 랜덤 쉐이크 레이어.
- **Audio Jitter:** TTS 피치(Pitch)를 랜덤하게 변동시켜 기계적 완벽함 파괴.
- **Human Glitch:** 나레이션 무음 구간에 0.3s 인간 숨소리(Breathing) 샘플 랜덤 믹싱.

### 🧠 Historical Persona RAG
- 인물의 실제 기록(논문)에서 추출된 '결정 패턴'을 AI에게 주입하여, 현대적 상황에서도 그 인물다운 판단을 내리게 함. (예: 이순신 장군의 원칙 중심 경영)

---

## 5. 바이브 코딩 실무 규칙 (Vibe Coding Rules)

1. **의도적 결함 우선:** 코드는 완벽해야 하지만, 결과물(영상)은 의도적으로 불완전(Human-like)해야 함을 명시할 것.
2. **모듈형 아키텍처:** 각 에이전트는 독립적인 서비스로 작동하며, 상태는 LangGraph로 관리함.
3. **리소스 최적화:** 로컬 환경의 부담을 줄이기 위해 모든 I/O 작업은 비동기(Async)로 처리함.
4. **철저한 기록:** 성공한 영상의 데이터는 즉시 Vector DB에 업데이트하여 시스템이 스스로 진화하게 함.

---

## 6. 실행 로드맵 (Execution Roadmap)

- [ ] **Phase 1: Deep Ingestion** - 역사 논문 및 레딧 크롤링 모듈 완성 (1주)
- [ ] **Phase 2: Ghost Engine** - Humanizer의 적대적 편집 알고리즘 및 합성 엔진 구현 (2주)
- [ ] **Phase 3: Empire Expansion** - 인물 현대 소환 시나리오 최적화 및 글로벌 다채널 가동 (1개월~)

---

### 💡 Project Mantra
"우리는 역사를 왜곡하지 않는다. 다만 현대라는 무대에 그들을 다시 세울 뿐이다."