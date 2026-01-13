# OMNI-ARCHIVE

역사적 사료와 논문을 기반으로 인물을 현대적 상황에 재배치해, 근거 있는 서사를 담은 쇼츠를 자율 생성하는 멀티 에이전트 시스템입니다. 로컬 지휘부(FastAPI/LangGraph)에서 에이전트를 통제하고, 클라우드 모델(Gemini/Flux/Sora)을 활용해 고품질 멀티모달 자산을 생산합니다.

## 프로젝트 목표
- 논문 기반 고증과 현대적 서사를 결합한 쇼츠 자동화 파이프라인 구축
- 인간적 결함을 의도적으로 주입해 AI 탐지를 회피하는 Ghost Engine 구현
- 성과 로그와 지식 베이스를 축적해 스스로 진화하는 콘텐츠 엔진 완성

## 시스템 아키텍처
- Local 지휘부: FastAPI, LangGraph, MoviePy, OpenCV, FFmpeg
- Cloud 두뇌: Gemini 1.5 Pro/Flash, Flux/Sora, Edge-TTS
- 데이터베이스: Supabase(SQL), Pinecone(Vector)

## 에이전트 역할
- The Scout: ArXiv/Reddit/웹 소스에서 논문과 트렌드를 수집해 지식 베이스 구축
- The Architect: 역사적 인물의 성격과 현대 상황을 매칭한 대본 설계
- The Humanizer: 영상/오디오에 의도적 결함을 주입해 인간적 질감 유지
- The Swarm Master: 다국어 최적화와 멀티 채널 배포를 총괄

## 설치
- Python 3.10+ 권장
- 의존성 고정 규칙: `httpx<0.29`, `packaging<25`

```bash
python -m venv venv
venv\Scripts\activate
pip install fastapi langgraph moviepy opencv-python playwright supabase pinecone-client "httpx<0.29" "packaging<25"
```

## 실행 예시
### The Scout (ArXiv)
```bash
python src/agents/scout_arxiv.py
```

## 환경 변수
- API 키 및 비밀 값은 `.env`에서만 로드해야 합니다.

## 문서
- 제품 요구사항: `docs/PRD.md`
- 기술 요구사항: `docs/TRD.md`
- 실행 규칙: `docs/RULES.md`
- 자원 요구사항: `docs/RESOURCES.md`
