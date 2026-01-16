"""수집된 논문/뉴스 데이터를 쇼츠 대본으로 변환하는 The Humanizer 에이전트."""
from __future__ import annotations

"""수집된 논문/뉴스 데이터를 쇼츠 대본으로 변환하는 The Humanizer 에이전트."""

import asyncio
import importlib.util
import json
import os
from datetime import datetime
from typing import Any, Tuple

import google.generativeai as genai

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_PATH = os.path.join(ROOT_DIR, "logs", "omni_system.log")
CACHE_DIR = os.path.join(ROOT_DIR, "cache")
ARXIV_CACHE_PATH = os.path.join(CACHE_DIR, "scout_arxiv.json")
NEWS_CACHE_PATH = os.path.join(CACHE_DIR, "scout_news.json")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash")
RALPH_LOOP_MAX_ATTEMPTS = 3


def _append_log_line(path: str, line: str) -> None:
    """로그 파일에 메시지를 추가한다.

    Args:
        path: 로그 파일 경로.
        line: 로그 라인 문자열.
    """
    with open(path, "a", encoding="utf-8") as log_file:
        log_file.write(line)


def _safe_json_dumps(payload: Any) -> str:
    """JSON 직렬화를 수행하고 실패 시 빈 배열을 반환한다.

    Args:
        payload: 직렬화 대상 데이터.

    Returns:
        JSON 문자열.
    """
    try:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return "[]"


async def log_event(message: str) -> Tuple[bool, str]:
    """활동 로그를 기록한다.

    Args:
        message: 로그에 기록할 메시지.

    Returns:
        로그 기록 성공 여부와 상세 메시지.
    """
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"{timestamp} | {message}\n"
    try:
        await asyncio.to_thread(os.makedirs, os.path.dirname(LOG_PATH), exist_ok=True)
        await asyncio.to_thread(_append_log_line, LOG_PATH, line)
        return True, "logged"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"



def _normalize_text(value: str | None) -> str:
    """텍스트를 정규화한다.

    Args:
        value: 원본 문자열.

    Returns:
        정규화된 문자열.
    """
    if not value:
        return ""
    return " ".join(value.replace("\n", " ").split()).strip()


def _build_summary_payload(
    arxiv_groups: list[dict[str, Any]],
    news_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Gemini 요약을 위한 핵심 데이터만 추린다.

    Args:
        arxiv_groups: ArXiv 그룹 데이터.
        news_groups: 뉴스 헤드라인 그룹 데이터.

    Returns:
        요약 대상 데이터 목록.
    """
    summary_items: list[dict[str, Any]] = []
    for group in arxiv_groups:
        keywords = group.get("keywords", [])
        for paper in group.get("papers", [])[:5]:
            summary_items.append(
                {
                    "type": "paper",
                    "keywords": keywords,
                    "title": paper.get("title", ""),
                    "summary": _normalize_text(paper.get("summary")),
                    "source_url": paper.get("source_url", paper.get("id", "")),
                    "published": paper.get("published", ""),
                }
            )

    for group in news_groups:
        topic = group.get("topic", "")
        for item in group.get("items", [])[:5]:
            summary_items.append(
                {
                    "type": "news",
                    "topic": topic,
                    "title": item.get("title", ""),
                    "summary": _normalize_text(item.get("summary")),
                    "source": item.get("source", ""),
                    "source_url": item.get("url", ""),
                    "published": item.get("published", ""),
                }
            )

    return summary_items


def _build_script_prompt(summary_payload: list[dict[str, Any]]) -> str:
    """Gemini에 전달할 쇼츠 대본 프롬프트를 생성한다.

    Args:
        summary_payload: 요약 대상 데이터.

    Returns:
        프롬프트 문자열.
    """
    payload_text = _safe_json_dumps(summary_payload)
    return (
        "너는 유튜브 쇼츠 작가다. 아래 JSON의 전문 용어를 대중적인 언어로 바꾸고, "
        "60초 분량의 쇼츠 대본을 작성하라. 반드시 흥미를 유발하는 Hook 한 줄을 첫 문장으로 포함하고, "
        "대본 형식은 다음을 따른다:\n"
        "- Hook: ...\n- Body: ...\n- Loop: ...\n"
        "Hook는 1~2문장, Body는 6~8문장, Loop는 1문장으로 구성한다. "
        "논문/뉴스 출처 URL과 발행일을 대본 말미에 간단히 나열하라.\n"
        f"JSON:\n{payload_text}"
    )


def _select_model_candidates() -> list[str]:
    """Gemini 모델 후보 목록을 생성한다.

    Returns:
        모델 이름 목록.
    """
    candidates = [GEMINI_MODEL]
    if GEMINI_FALLBACK_MODEL and GEMINI_FALLBACK_MODEL not in candidates:
        candidates.append(GEMINI_FALLBACK_MODEL)
    if "gemini-1.5-flash" not in candidates:
        candidates.append("gemini-1.5-flash")
    return candidates


def _configure_gemini(api_key: str) -> Tuple[bool, str]:
    """Gemini SDK 초기화를 수행한다.

    Args:
        api_key: Gemini API 키.

    Returns:
        성공 여부와 상세 메시지.
    """
    configure = getattr(genai, "configure", None)
    if not callable(configure):
        return False, "google.generativeai.configure를 사용할 수 없습니다."
    try:
        configure(api_key=api_key)
        return True, "configured"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _generate_with_model(model_name: str, prompt: str) -> Tuple[bool, str]:
    """Gemini 모델로 요약을 생성한다.

    Args:
        model_name: Gemini 모델 이름.
        prompt: 요약 프롬프트.

    Returns:
        성공 여부와 요약 텍스트 또는 에러 메시지.
    """
    model_factory = getattr(genai, "GenerativeModel", None)
    if model_factory is None:
        return False, "google.generativeai.GenerativeModel을 사용할 수 없습니다."
    try:
        model = model_factory(model_name=model_name)
        response = model.generate_content(prompt)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    text = getattr(response, "text", None)
    if not text:
        return False, "Gemini 응답에서 텍스트를 찾을 수 없습니다."
    return True, text.strip()


async def _summarize_with_gemini(prompt: str) -> Tuple[bool, str]:
    """Gemini API로 요약을 수행한다.

    Args:
        prompt: 요약 프롬프트.

    Returns:
        성공 여부와 요약 결과 또는 에러 메시지.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False, "GEMINI_API_KEY가 설정되지 않았습니다."

    ok, message = _configure_gemini(api_key)
    if not ok:
        return False, message

    last_error = ""
    for model_name in _select_model_candidates():
        ok, result = _generate_with_model(model_name, prompt)
        if ok:
            return True, result
        last_error = f"{model_name}: {result}"
    return False, last_error



async def _load_json_file(file_path: str) -> Tuple[bool, str]:
    """JSON 파일을 읽어 문자열로 반환한다.

    Args:
        file_path: JSON 파일 경로.

    Returns:
        성공 여부와 JSON 문자열 또는 에러 메시지.
    """
    try:
        payload = await asyncio.to_thread(_read_file, file_path)
        return True, payload
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _read_file(file_path: str) -> str:
    """파일을 읽어 문자열로 반환한다.

    Args:
        file_path: 파일 경로.

    Returns:
        파일 내용 문자열.
    """
    with open(file_path, "r", encoding="utf-8") as file_handle:
        return file_handle.read()


async def load_scout_outputs(
    arxiv_path: str,
    news_path: str,
) -> Tuple[bool, str]:
    """Scout JSON 파일을 읽어 파싱 가능한 문자열로 반환한다.

    Args:
        arxiv_path: ArXiv JSON 파일 경로.
        news_path: 뉴스 JSON 파일 경로.

    Returns:
        성공 여부와 JSON 문자열 또는 에러 메시지.
    """
    ok_arxiv, arxiv_payload = await _load_json_file(arxiv_path)
    if not ok_arxiv:
        return False, arxiv_payload
    ok_news, news_payload = await _load_json_file(news_path)
    if not ok_news:
        return False, news_payload
    combined = {
        "arxiv": arxiv_payload,
        "news": news_payload,
    }
    return True, _safe_json_dumps(combined)


def _ensure_cache_dir() -> None:
    """캐시 디렉터리를 준비한다."""
    os.makedirs(CACHE_DIR, exist_ok=True)


def _write_file(path: str, payload: str) -> None:
    """파일에 문자열을 기록한다.

    Args:
        path: 파일 경로.
        payload: 기록할 문자열.
    """
    with open(path, "w", encoding="utf-8") as file_handle:
        file_handle.write(payload)


async def _persist_payloads(arxiv_payload: str, news_payload: str) -> Tuple[bool, str]:
    """Scout 결과를 캐시에 저장한다.

    Args:
        arxiv_payload: ArXiv JSON 문자열.
        news_payload: 뉴스 JSON 문자열.

    Returns:
        성공 여부와 상세 메시지.
    """
    try:
        await asyncio.to_thread(_ensure_cache_dir)
        await asyncio.to_thread(_write_file, ARXIV_CACHE_PATH, arxiv_payload)
        await asyncio.to_thread(_write_file, NEWS_CACHE_PATH, news_payload)
        return True, "cached"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _import_scout_module(module_path: str, name: str) -> Tuple[bool, Any]:
    """경로 기반으로 Scout 모듈을 로드한다.

    Args:
        module_path: 모듈 파일 경로.
        name: 모듈 이름.

    Returns:
        성공 여부와 모듈 객체 또는 에러 메시지.
    """
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        return False, f"모듈 로딩 실패: {module_path}"
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return True, module


async def collect_scout_payloads() -> Tuple[bool, str]:
    """Scout 모듈에서 직접 데이터를 수집한다.

    Returns:
        성공 여부와 JSON 문자열 또는 에러 메시지.
    """
    arxiv_path = os.path.join(os.path.dirname(__file__), "scout_arxiv.py")
    news_path = os.path.join(os.path.dirname(__file__), "scout_news.py")

    ok_arxiv_module, arxiv_module = _import_scout_module(
        arxiv_path,
        "scout_arxiv",
    )
    if not ok_arxiv_module:
        return False, arxiv_module

    ok_news_module, news_module = _import_scout_module(
        news_path,
        "scout_news",
    )
    if not ok_news_module:
        return False, news_module

    ok_arxiv, arxiv_payload = await arxiv_module.collect_arxiv_papers(
        arxiv_module.DEFAULT_QUERIES,
        max_results=5,
        sort_by="submittedDate",
        sort_order="descending",
    )
    if not ok_arxiv:
        return False, arxiv_payload

    ok_news, news_payload = await news_module.collect_news_headlines(
        news_module.NEWS_SOURCES,
        max_items=5,
    )
    if not ok_news:
        return False, news_payload

    ok_cache, cache_message = await _persist_payloads(arxiv_payload, news_payload)
    if not ok_cache:
        await log_event(f"Humanizer 캐시 저장 실패: {cache_message}")

    combined = {
        "arxiv": arxiv_payload,
        "news": news_payload,
    }
    return True, _safe_json_dumps(combined)


async def build_shorts_script(
    arxiv_json: str,
    news_json: str,
) -> Tuple[bool, str]:
    """Scout JSON 문자열을 쇼츠 대본으로 변환한다.

    Args:
        arxiv_json: ArXiv JSON 문자열.
        news_json: 뉴스 JSON 문자열.

    Returns:
        성공 여부와 쇼츠 대본 또는 에러 메시지.
    """
    try:
        arxiv_groups = json.loads(arxiv_json)
        news_groups = json.loads(news_json)
    except json.JSONDecodeError as exc:
        return False, f"JSONDecodeError: {exc}"

    summary_payload = _build_summary_payload(arxiv_groups, news_groups)
    prompt = _build_script_prompt(summary_payload)
    ok, script = await _summarize_with_gemini(prompt)
    if not ok:
        await log_event(f"Humanizer 요약 실패: {script}")
        return False, script

    await log_event("Humanizer 쇼츠 대본 생성 완료")
    return True, script


async def run_humanizer() -> Tuple[bool, str]:
    """Humanizer 실행 진입점.

    Returns:
        성공 여부와 쇼츠 대본.
    """
    ok, payload = await collect_scout_payloads()
    if not ok:
        return False, payload

    try:
        combined = json.loads(payload)
    except json.JSONDecodeError as exc:
        await log_event(f"Humanizer JSON 파싱 실패: {exc}")
        return False, f"JSONDecodeError: {exc}"

    arxiv_json = combined.get("arxiv", "[]")
    news_json = combined.get("news", "[]")
    return await build_shorts_script(arxiv_json, news_json)


async def main() -> Tuple[bool, str]:
    """Humanizer 실행 진입점."""
    return await run_humanizer()


if __name__ == "__main__":
    success, message = asyncio.run(main())
    if success:
        print(message)
        raise SystemExit(0)
    print(f"ERROR: {message}")
    raise SystemExit(1)
