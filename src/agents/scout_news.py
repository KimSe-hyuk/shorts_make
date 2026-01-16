"""AI 기술 및 반도체 뉴스 헤드라인 수집을 담당하는 The Scout 에이전트."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Tuple
import xml.etree.ElementTree as ET

import httpx

DEFAULT_TIMEOUT = 20.0
RATE_LIMIT_SECONDS = 1.5
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_PATH = os.path.join(ROOT_DIR, "logs", "omni_system.log")

NEWS_SOURCES = [
    {
        "topic": "ai",
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "topic": "ai",
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    },
    {
        "topic": "ai",
        "name": "Hacker News AI",
        "url": "https://hnrss.org/newest?q=AI+OR+machine+learning&count=50",
    },
    {
        "topic": "semiconductor",
        "name": "Tech Xplore Semiconductors",
        "url": "https://techxplore.com/rss-feed/semiconductors/",
    },
    {
        "topic": "semiconductor",
        "name": "Semiconductor Today",
        "url": "https://semiconductor-today.com/rss/news.xml",
    },
    {
        "topic": "semiconductor",
        "name": "IEEE Spectrum Semiconductors",
        "url": "https://spectrum.ieee.org/feeds/topic/semiconductors.rss",
    },
]

AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "generative ai",
    "llm",
]
SEMICONDUCTOR_KEYWORDS = [
    "semiconductor",
    "chip",
    "foundry",
    "fab",
    "wafer",
    "gpu",
    "memory",
    "hbm",
]


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


def _parse_rss_items(xml_text: str, source_name: str, source_url: str) -> list[dict[str, Any]]:
    """RSS XML 문자열을 파싱해 항목 목록을 반환한다.

    Args:
        xml_text: RSS XML 문자열.
        source_name: 소스 이름.
        source_url: 소스 URL.

    Returns:
        RSS 항목 목록.
    """
    root = ET.fromstring(xml_text)
    items: list[dict[str, Any]] = []

    for item in root.findall(".//item"):
        title = _normalize_text(item.findtext("title"))
        link = _normalize_text(item.findtext("link"))
        published = _normalize_text(item.findtext("pubDate"))
        summary = _normalize_text(item.findtext("description"))
        if not title:
            continue
        items.append(
            {
                "title": title,
                "url": link,
                "published": published,
                "summary": summary,
                "source": source_name,
                "source_url": source_url,
            }
        )

    return items


def _matches_keywords(text: str, keywords: list[str]) -> bool:
    """키워드 매칭 여부를 확인한다.

    Args:
        text: 대상 텍스트.
        keywords: 키워드 목록.

    Returns:
        키워드 포함 여부.
    """
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _filter_headlines(
    items: list[dict[str, Any]],
    topic: str,
) -> list[dict[str, Any]]:
    """토픽에 맞는 헤드라인만 필터링한다.

    Args:
        items: RSS 항목 목록.
        topic: 대상 토픽.

    Returns:
        필터링된 RSS 항목 목록.
    """
    if topic == "ai":
        keywords = AI_KEYWORDS
    else:
        keywords = SEMICONDUCTOR_KEYWORDS

    filtered: list[dict[str, Any]] = []
    for item in items:
        combined = f"{item.get('title', '')} {item.get('summary', '')}"
        if _matches_keywords(combined, keywords):
            filtered.append(item)

    return filtered


async def _rate_limited_get(
    client: httpx.AsyncClient,
    url: str,
    lock: asyncio.Lock,
    last_request: list[float],
) -> Tuple[bool, str]:
    """RSS 요청을 레이트 리밋에 맞춰 수행한다.

    Args:
        client: 공유 AsyncClient.
        url: 호출할 RSS URL.
        lock: 단일 요청 보장을 위한 락.
        last_request: 마지막 요청 시각을 담은 리스트.

    Returns:
        성공 여부와 RSS XML 또는 에러 메시지.
    """
    async with lock:
        now = asyncio.get_event_loop().time()
        wait_seconds = max(0.0, RATE_LIMIT_SECONDS - (now - last_request[0]))
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        try:
            response = await client.get(url)
            response.raise_for_status()
        except Exception as exc:
            return False, f"{type(exc).__name__}: {exc}"
        last_request[0] = asyncio.get_event_loop().time()
        return True, response.text


async def fetch_news_source(
    client: httpx.AsyncClient,
    source: dict[str, str],
    lock: asyncio.Lock,
    last_request: list[float],
) -> Tuple[bool, str]:
    """단일 뉴스 소스를 수집한다.

    Args:
        client: 공유 AsyncClient.
        source: 뉴스 소스 정보.
        lock: 단일 요청 보장을 위한 락.
        last_request: 마지막 요청 시각을 담은 리스트.

    Returns:
        성공 여부와 RSS XML 또는 에러 메시지.
    """
    return await _rate_limited_get(client, source["url"], lock, last_request)


async def collect_news_headlines(
    sources: list[dict[str, str]],
    max_items: int = 5,
) -> Tuple[bool, str]:
    """뉴스 헤드라인을 수집해 JSON 문자열로 반환한다.

    Args:
        sources: 뉴스 소스 목록.
        max_items: 반환할 헤드라인 수.

    Returns:
        성공 여부와 수집된 헤드라인 데이터 또는 에러 메시지.
    """
    if not sources:
        return False, "뉴스 소스가 비어 있습니다."

    lock = asyncio.Lock()
    last_request = [0.0]

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:

        async def fetch_source(source: dict[str, str]) -> Tuple[bool, str]:
            """소스별 RSS를 가져온다."""
            return await fetch_news_source(client, source, lock, last_request)

        tasks = [fetch_source(source) for source in sources]
        results = await asyncio.gather(*tasks)

    payload: list[dict[str, Any]] = []
    errors: list[str] = []

    for source, (ok, xml_text) in zip(sources, results):
        if not ok:
            errors.append(f"{source['name']}: {xml_text}")
            continue
        try:
            items = _parse_rss_items(xml_text, source["name"], source["url"])
        except ET.ParseError as exc:
            errors.append(f"{source['name']}: XML 파싱 실패 ({exc})")
            continue
        filtered_items = _filter_headlines(items, source["topic"])
        payload.append(
            {
                "topic": source["topic"],
                "source": source["name"],
                "source_url": source["url"],
                "items": filtered_items[: max_items * 2],
            }
        )

    if errors:
        await log_event(f"뉴스 RSS 수집 실패: {' | '.join(errors)}")
        return False, "; ".join(errors)

    await log_event(f"뉴스 RSS 수집 성공: {len(payload)}개 소스")
    return True, _safe_json_dumps(payload)


def _select_top_headlines(
    groups: list[dict[str, Any]],
    max_headlines: int = 5,
) -> list[dict[str, Any]]:
    """토픽별로 상위 헤드라인을 추출한다.

    Args:
        groups: 소스별 헤드라인 그룹.
        max_headlines: 반환할 헤드라인 개수.

    Returns:
        헤드라인 목록.
    """
    ai_items: list[dict[str, Any]] = []
    semiconductor_items: list[dict[str, Any]] = []

    for group in groups:
        if group.get("topic") == "ai":
            ai_items.extend(group.get("items", []))
        else:
            semiconductor_items.extend(group.get("items", []))

    return [
        {
            "topic": "ai",
            "items": ai_items[:max_headlines],
        },
        {
            "topic": "semiconductor",
            "items": semiconductor_items[:max_headlines],
        },
    ]


def _format_headline_output(headline: dict[str, Any], index: int) -> str:
    """헤드라인 출력을 위한 문자열을 생성한다.

    Args:
        headline: 헤드라인 데이터.
        index: 출력 순번.

    Returns:
        출력 문자열.
    """
    published = headline.get("published", "")
    summary = headline.get("summary", "")
    summary_line = f"- 요약: {summary}\n" if summary else ""
    return (
        f"[{index}] {headline.get('title', '')}\n"
        f"- 발행일: {published}\n"
        f"- 링크: {headline.get('url', '')}\n"
        f"- 출처: {headline.get('source', '')}\n"
        f"{summary_line}"
    )


async def run_scout() -> Tuple[bool, str]:
    """AI/반도체 뉴스 헤드라인을 수집하고 보고서를 생성한다.

    Returns:
        성공 여부와 보고서 텍스트.
    """
    ok, payload = await collect_news_headlines(NEWS_SOURCES, max_items=5)
    if not ok:
        return False, payload

    try:
        report_groups = json.loads(payload)
    except json.JSONDecodeError as exc:
        await log_event(f"뉴스 보고서 JSON 파싱 실패: {exc}")
        return False, f"JSONDecodeError: {exc}"

    selected = _select_top_headlines(report_groups, max_headlines=5)
    output_lines = ["News Scout Report"]
    for group in selected:
        topic = group.get("topic", "")
        output_lines.append(f"\n[Topic] {topic}")
        items = group.get("items", [])
        if not items:
            output_lines.append("- 검색 결과 없음")
            continue
        for index, item in enumerate(items, start=1):
            output_lines.append(_format_headline_output(item, index))

    report_text = "\n".join(output_lines).strip()
    await log_event("뉴스 헤드라인 보고서 생성 완료")
    return True, report_text


async def main() -> Tuple[bool, str]:
    """News Scout 실행 진입점."""
    return await run_scout()


if __name__ == "__main__":
    success, message = asyncio.run(main())
    if success:
        print(message)
        raise SystemExit(0)
    print(f"ERROR: {message}")
    raise SystemExit(1)
