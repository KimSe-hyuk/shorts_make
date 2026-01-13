# 🛠️ TRD: OMNI-ARCHIVE 기술 요구사항 정의서

> **Project:** OMNI-ARCHIVE (Ghost Engine 2.0)
> **Goal:** 논문 기반 역사 고증 + 현대적 서사 변환 + 적대적 편집을 통한 자율형 쇼츠 생성 시스템 구축

---

## 1. 시스템 아키텍처 (Hybrid Infrastructure)

### [Local 지휘부]
- **Framework:** FastAPI (비동기 통신), LangGraph (에이전트 워크플로우 제어)
- **Video Engine:** MoviePy, OpenCV-Python, FFmpeg
- **Task:** 에이전트 오케스트레이션, 데이터 크롤링, 최종 영상 물리 합성 및 결함 주입

### [Cloud 두뇌]
- **LLM:** Gemini 1.5 Pro (심층 추론/논문 해석), Gemini 1.5 Flash (고속 생산)
- **Generative:** Flux.1 (이미지), Sora/Kling (비디오 자산), Edge-TTS (음성)
- **Task:** 역사 사료 해석, 시나리오 생성, 고화질 멀티모달 자산 생성

---

## 2. 에이전틱 워크플로우 명세

### 🤖 Agent 1: The Scout (심층 채굴)
- **Sources:** ArXiv API, Reddit(PRAW), 전문 웹 크롤링(Playwright)
- **Logic:** 논문의 핵심 팩트와 레딧의 트렌드 키워드를 추출하여 지식 베이스(Pinecone)에 저장.

### 🤖 Agent 2: The Architect (시공간 변환 설계)
- **Logic:** 인물의 역사적 성격과 현대적 상황을 매칭한 대본 작성.
- **Structure:** 2s Hook (질문) -> 30s Narrative (역사 팩트 + 현대적 비틀기) -> 5s Loop (수미상관).

### 🤖 Agent 3: The Humanizer (적대적 편집 - 핵심)
- **Visual:** 매 프레임 ±1~2px 랜덤 진동, 가우시안 노이즈 오버레이.
- **Audio:** TTS 주파수 랜덤 변동(Jitter), 문장 간 인간 숨소리(Breathing) 샘플 무작위 삽입.

---

## 3. 데이터베이스 스키마

### [Supabase (Relational)]
- `contents`: 영상 제작 로그, 플랫폼별 업로드 상태, 성과 지표(Retention) 저장.
- `personas`: 역사적 인물별 성격 파라미터 및 주요 어록 데이터.

### [Pinecone (Vector)]
- `knowledge_ragi`: 논문 초록 및 역사적 사건 임베딩 데이터 (Dimension: 1536).

---

## 4. 바이브 코딩 실무 규칙
- 모든 파일은 모듈형으로 작성할 것 (예: `agents/scout.py`, `fx/visual.py`).
- 로컬 리소스 보호를 위해 모든 I/O 및 렌더링은 `asyncio` 기반으로 처리할 것.
- AI 코딩 툴 사용 시, 반드시 "적대적 결함 주입(Humanizer)" 모듈의 정밀도를 우선시할 것.