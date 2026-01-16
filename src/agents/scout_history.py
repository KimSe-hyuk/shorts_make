"""역사 사료 기반 팩트 채굴을 담당하는 The Scout 에이전트."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Tuple
import xml.etree.ElementTree as ET
from urllib.parse import quote

import httpx

ARXIV_API_URL = "https://export.arxiv.org/api/query"
DEFAULT_TIMEOUT = 20.0
RATE_LIMIT_SECONDS = 3.0
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_PATH = os.path.join(ROOT_DIR, "logs", "omni_system.log")
DEFAULT_QUERIES = [
    ["Napoleon Bonaparte"],
    ["Waterloo battle"],
    ["Russian campaign 1812"],
    ["Napoleonic Wars logistics"],
    ["French Empire politics"],
]


def _build_query_url(
    keywords: list[str],
    max_results: int = 5,
    sort_by: str | None = None,
    sort_order: str | None = None,
) -> str:
    """키워드 기반 ArXiv 검색 URL을 생성한다.

    Args:
        keywords: 논문에 반드시 포함될 키워드 목록.
        max_results: 가져올 논문 개수.
        sort_by: 정렬 기준 필드.
        sort_order: 정렬 방식.

    Returns:
        ArXiv API 요청 URL 문자열.
    """
    query_terms = [
        f"all:{keyword}" if " " not in keyword else f'all:"{keyword}"'
        for keyword in keywords
    ]
    search_query = quote(" AND ".join(query_terms))
    request_url = (
        f"{ARXIV_API_URL}?search_query={search_query}"
        f"&start=0&max_results={max_results}"
    )
    if sort_by:
        request_url += f"&sortBy={sort_by}"
    if sort_order:
        request_url += f"&sortOrder={sort_order}"
    return request_url


def _parse_arxiv_feed(xml_text: str) -> list[dict[str, Any]]:
    """ArXiv Atom 피드를 파싱해 논문 정보를 반환한다.

    Args:
        xml_text: ArXiv Atom XML 문자열.

    Returns:
        논문 메타데이터 목록.
    """
    namespace = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(xml_text)
    entries: list[dict[str, Any]] = []

    for entry in root.findall("atom:entry", namespace):
        title = entry.findtext("atom:title", default="", namespaces=namespace).strip()
        summary = entry.findtext(
            "atom:summary", default="", namespaces=namespace
        ).strip()
        paper_id = entry.findtext("atom:id", default="", namespaces=namespace).strip()
        published = entry.findtext(
            "atom:published", default="", namespaces=namespace
        ).strip()
        updated = entry.findtext("atom:updated", default="", namespaces=namespace).strip()
        doi = entry.findtext("arxiv:doi", default="", namespaces=namespace).strip()
        primary_category = entry.find("arxiv:primary_category", namespace)
        category_term = ""
        if primary_category is not None:
            category_term = primary_category.attrib.get("term", "")
        authors = [
            author.findtext("atom:name", default="", namespaces=namespace).strip()
            for author in entry.findall("atom:author", namespace)
        ]
        links = [
            link.attrib.get("href", "")
            for link in entry.findall("atom:link", namespace)
            if link.attrib.get("href")
        ]

        entries.append(
            {
                "title": title,
                "summary": summary,
                "id": paper_id,
                "published": published,
                "updated": updated,
                "authors": [author for author in authors if author],
                "doi": doi,
                "primary_category": category_term,
                "source_url": paper_id,
                "links": links,
            }
        )

    return entries


def _format_paper_output(paper: dict[str, Any], index: int) -> str:
    """논문 정보를 출력 문자열로 정리한다.

    Args:
        paper: 논문 메타데이터.
        index: 출력 순번.

    Returns:
        화면 출력용 문자열.
    """
    authors = ", ".join(paper.get("authors", [])) or "알 수 없음"
    doi = paper.get("doi") or ""
    doi_line = f"- DOI: {doi}\n" if doi else ""
    return (
        f"[{index}] {paper.get('title', '')}\n"
        f"- 발표일: {paper.get('published', '')}\n"
        f"- 저자: {authors}\n"
        f"- 링크: {paper.get('id', '')}\n"
        f"{doi_line}"
        f"- 요약: {paper.get('summary', '')}\n"
    )


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


async def _rate_limited_get(
    client: httpx.AsyncClient,
    query_url: str,
    lock: asyncio.Lock,
    last_request: list[float],
) -> Tuple[bool, str]:
    """ArXiv 호출을 레이트 리밋에 맞춰 수행한다.

    Args:
        client: 공유 AsyncClient.
        query_url: 호출할 URL.
        lock: 단일 요청 보장을 위한 락.
        last_request: 마지막 요청 시각을 담은 리스트.

    Returns:
        성공 여부와 Atom XML 또는 에러 메시지.
    """
    async with lock:
        now = asyncio.get_event_loop().time()
        wait_seconds = max(0.0, RATE_LIMIT_SECONDS - (now - last_request[0]))
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        try:
            response = await client.get(query_url)
            response.raise_for_status()
        except Exception as exc:
            return False, f"{type(exc).__name__}: {exc}"
        last_request[0] = asyncio.get_event_loop().time()
        return True, response.text


async def fetch_history_feed(
    client: httpx.AsyncClient,
    query_url: str,
    lock: asyncio.Lock,
    last_request: list[float],
) -> Tuple[bool, str]:
    """ArXiv API에서 역사 관련 Atom 피드를 가져온다.

    Args:
        client: 공유 AsyncClient.
        query_url: ArXiv API 요청 URL.
        lock: 단일 요청 보장을 위한 락.
        last_request: 마지막 요청 시각을 담은 리스트.

    Returns:
        성공 여부와 Atom XML 문자열 또는 에러 메시지.
    """
    return await _rate_limited_get(client, query_url, lock, last_request)


async def collect_history_facts(
    queries: list[list[str]],
    max_results: int = 5,
) -> Tuple[bool, str]:
    """나폴레옹 관련 역사 논문을 병렬 수집한다.

    Args:
        queries: 키워드 목록의 목록.
        max_results: 각 쿼리별 최대 결과 수.

    Returns:
        성공 여부와 수집된 논문 데이터 또는 에러 메시지.
    """
    if not queries:
        return False, "검색 키워드가 비어 있습니다."

    lock = asyncio.Lock()
    last_request = [0.0]
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:

        async def fetch_query(keywords: list[str]) -> Tuple[bool, str]:
            """키워드 묶음을 ArXiv에 질의한다."""
            query_url = _build_query_url(
                keywords,
                max_results=max_results,
                sort_by="submittedDate",
                sort_order="descending",
            )
            return await fetch_history_feed(client, query_url, lock, last_request)

        tasks = [fetch_query(keywords) for keywords in queries]
        results = await asyncio.gather(*tasks)

    payload: list[dict[str, Any]] = []
    errors: list[str] = []

    for keywords, (ok, xml_text) in zip(queries, results):
        if not ok:
            errors.append(f"{keywords}: {xml_text}")
            continue
        try:
            papers = _parse_arxiv_feed(xml_text)
        except ET.ParseError as exc:
            errors.append(f"{keywords}: XML 파싱 실패 ({exc})")
            continue
        payload.append({"keywords": keywords, "papers": papers})

    if errors:
        await log_event(f"History 수집 실패: {' | '.join(errors)}")
        return False, "; ".join(errors)

    await log_event(f"History 수집 성공: {len(payload)}개 쿼리")
    return True, _safe_json_dumps(payload)


async def run_scout() -> Tuple[bool, str]:
    """나폴레옹 관련 사료 보고서를 생성한다.

    Returns:
        성공 여부와 보고서 텍스트.
    """
    ok, payload = await collect_history_facts(DEFAULT_QUERIES)
    if not ok:
        return False, payload

    try:
        report_data = json.loads(payload)
    except json.JSONDecodeError as exc:
        await log_event(f"보고서 JSON 파싱 실패: {exc}")
        return False, f"JSONDecodeError: {exc}"

    output_lines = ["History Scout Report"]
    for group in report_data:
        keywords = " & ".join(group.get("keywords", []))
        output_lines.append(f"\n[Topic] {keywords}")
        papers = group.get("papers", [])
        if not papers:
            output_lines.append("- 검색 결과 없음")
            continue
        for index, paper in enumerate(papers, start=1):
            output_lines.append(_format_paper_output(paper, index))

    report_text = "\n".join(output_lines).strip()
    await log_event(f"History 보고서 생성 완료: {len(report_data)}개 쿼리")
    return True, report_text


async def main() -> Tuple[bool, str]:
    """History Scout 실행 진입점."""
    return await run_scout()


if __name__ == "__main__":
    success, message = asyncio.run(main())
    if success:
        print(message)
        raise SystemExit(0)
    print(f"ERROR: {message}")
    raise SystemExit(1)
