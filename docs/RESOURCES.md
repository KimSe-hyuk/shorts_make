# 📦 RRD: OMNI-ARCHIVE 자원 요구사항 정의서

> **Project:** OMNI-ARCHIVE (Ghost Engine 2.0)
> **Efficiency:** Zero-Cost 전략 기반 고성능 리소스 배분

---

## 1. 하드웨어 리소스 (Local)

| 항목 | 요구 사양 | 비고 |
| :--- | :--- | :--- |
| **CPU** | Ryzen 7 5825U (8C/16T) | 병렬 영상 렌더링 및 에이전트 구동용 |
| **RAM** | 16GB (32GB 권장) | 이미지/프레임 버퍼 및 로컬 DB 캐싱용 |
| **Storage** | NVMe SSD 500GB+ | 소스 자산 및 학습 데이터 저장용 |
| **Network** | 100Mbps 이상 | 실시간 스트림 수집 및 API 통신용 |

---

## 2. 소프트웨어 스택

- **Runtime:** Python 3.10+
- **Dev Tools:** Cursor / Windsurf (Vibe Coding 핵심 도구)
- **Core Libs:** `fastapi`, `moviepy`, `opencv-python`, `langgraph`, `playwright`, `supabase`, `pinecone-client`
- **Infra:** Cloudflare Tunnel (모바일 커맨드 센터 연결용)

---

## 3. 외부 API 및 비용 관리 (Zero-Cost 전략)

| 서비스 | 모델/API | 비용 전략 |
| :--- | :--- | :--- |
| **Google AI** | Gemini 1.5 Flash | Free Tier (대량 데이터 처리용) |
| **Google AI** | Gemini 1.5 Pro | Pay-as-you-go (핵심 시나리오 추론용) |
| **Image** | Leonardo.ai / Flux | Daily Free Credits 활용 |
| **Voice** | Edge-TTS | Open Source (무료 무제한) |
| **Database** | Supabase / Pinecone | Free Tier (Starter Plan) |

---

## 4. 지식 및 콘텐츠 자산

- **Data Sources:** Google Scholar, ArXiv API, Reddit API (PRAW), 역사 사료 DB.
- **SFX Assets:** 인간 숨소리(Breathing), 필름 노이즈(Film Grain), 수동 카메라 셔터음 등 '인간적 질감'용 샘플.

---

## 5. 실행 지침 (Instruction)
- AI에게 코딩을 시킬 때, **"로컬 CPU(Ryzen 7 5825U)의 멀티코어를 최대한 활용하는 멀티프로세싱 구조"**를 요구할 것.
- 비용 절감을 위해 모든 API 호출 전에는 **로컬 캐시(Redis 또는 JSON)**를 먼저 확인하는 로직을 포함할 것.