# AGENTS.md

이 문서는 OMNI-ARCHIVE 프로젝트에서 활동하는 AI 에이전트를 위한 통합 가이드입니다.

---

## 빌드/테스트 명령어

### 설치
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install fastapi langgraph moviepy opencv-python playwright supabase pinecone-client "httpx<0.29" "packaging<25"
```

### 테스트 실행
```bash
# 연결 테스트 (모든 코드 수정 후 필수)
python connection_test.py

# 개별 에이전트 실행 예시
python src/agents/scout_arxiv.py
```

### 단일 테스트 실행
이 프로젝트는 공식 테스트 프레임워크를 사용하지 않습니다. 대신 `connection_test.py`를 실행하여 모든 외부 연결을 검증합니다.

---

## 코드 스타일 가이드라인

### 1. Import 순서
```python
# 1. 표준 라이브러리
import os
import asyncio

# 2. 서드파티 라이브러리
import httpx
import xml.etree.ElementTree as ET

# 3. 로컬 모듈
from typing import Any
from __future__ import annotations  # 최상단에 배치
```

### 2. 비동기 우선 (Async-First)
모든 I/O 작업은 반드시 `async/await` 사용:
```python
async def fetch_data() -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return parse_data(response.text)
```

### 3. 타입 어노테이션
- 명시적 타입 힌트 필수
- 소문자 컬렉션 타입 사용 (`list[str]` not `List[str]`)
- 유니온 타입 (`|`) 우선:
```python
from typing import Any

def fetch(keywords: list[str], max_results: int = 5) -> list[dict[str, Any]]:
    pass

def process(data: str | None) -> str | None:
    return data
```

### 4. 네이밍 컨벤션
- 파일/함수/변수: `snake_case`
- 상수: `UPPER_SNAKE_CASE`
- 에이전트 이름: 문서에서 "The" 접두사 (The Scout, The Architect)

### 5. Docstring (한국어)
모든 함수/클래스는 Google 스타일 한국어 Docstring 필수:
```python
def build_query_url(keywords: list[str], max_results: int = 5) -> str:
    """키워드 기반 ArXiv 검색 URL을 생성한다.

    Args:
        keywords: 논문에 반드시 포함될 키워드 목록.
        max_results: 가져올 논문 개수.

    Returns:
        ArXiv API 요청 URL 문자열.
    """
```

### 6. 에러 핸들링
- `Tuple[bool, str]` 패턴 사용 (성공 여부, 상세 메시지)
- 폴백 메커니즘 구현:
```python
from typing import Tuple

def check_service() -> Tuple[bool, str]:
    try:
        # API 호출
        return True, "connected"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
```

### 7. 환경 변수
- 모든 비밀값은 `.env`에서만 로드
- 절대 하드코딩 금지:
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")  # 하드코딩 금지
```

### 8. 의존성 제약
```bash
# 엄격 버전 준수
"httpx<0.29"
"packaging<25"
```

### 9. 로깅
모든 활동은 `logs/omni_system.log`에 실시간 기록.

### 10. 마일스톤 기록 (필수)
모든 주요 기능 구현/시스템 변경 후 `docs/PROGRESS.md`에 기록:
```markdown
- 2026-01-15: [Scout] 새로운 소스 추가 기능 구현
```

---

## 프로젝트 특수 규칙

1. **검증 의무화**: 모든 코드 수정 후 반드시 `python connection_test.py` 실행
2. **원자적 작업**: 한 번에 하나의 기능 단위만 개선
3. **팩트 최우선**: Scout이 수집한 모든 데이터는 원본 출처(URL/DOI) 메타데이터 보존
4. **역사적 무결성**: 인물 성격은 사료 기반, 상황만 현대적으로 비틀기
5. **인간적 결함**: 기계적 완벽함은 에러로 간주, Humanizer 검증 필수

---

## 프로젝트 구조

```
shorts_vibe_gemini/
├── src/agents/         # 에이전트 구현
├── docs/               # 문서 (RULES.md, PROGRESS.md, PRD.md, TRD.md)
├── connection_test.py  # 연결 검증 (모든 수정 후 필수)
├── .env                # 환경 변수 (유일한 비밀값 소스)
└── AGENTS.md           # 이 파일
```
