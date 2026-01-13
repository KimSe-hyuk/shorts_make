"""ArXiv 논문 수집을 담당하는 Scout 에이전트."""

from __future__ import annotations

import asyncio
from typing import Any
import xml.etree.ElementTree as ET
from urllib.parse import quote

import httpx

ARXIV_API_URL = "https://export.arxiv.org/api/query"


def build_query_url(
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


def parse_arxiv_feed(xml_text: str) -> list[dict[str, Any]]:
    """ArXiv Atom 피드를 파싱해 논문 정보를 반환한다.

    Args:
        xml_text: ArXiv Atom XML 문자열.

    Returns:
        논문 메타데이터 목록.
    """
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    entries = []

    for entry in root.findall("atom:entry", namespace):
        title = entry.findtext("atom:title", default="", namespaces=namespace).strip()
        summary = entry.findtext("atom:summary", default="", namespaces=namespace).strip()
        paper_id = entry.findtext("atom:id", default="", namespaces=namespace).strip()
        published = entry.findtext("atom:published", default="", namespaces=namespace).strip()
        authors = [
            author.findtext("atom:name", default="", namespaces=namespace).strip()
            for author in entry.findall("atom:author", namespace)
        ]

        entries.append(
            {
                "title": title,
                "summary": summary,
                "id": paper_id,
                "published": published,
                "authors": [author for author in authors if author],
            }
        )

    return entries


async def fetch_arxiv_papers(
    keywords: list[str],
    max_results: int = 5,
    sort_by: str | None = None,
    sort_order: str | None = None,
) -> list[dict[str, Any]]:
    """ArXiv API를 호출해 논문 정보를 수집한다.

    Args:
        keywords: 검색에 사용할 키워드 목록.
        max_results: 가져올 논문 개수.
        sort_by: 정렬 기준 필드.
        sort_order: 정렬 방식.

    Returns:
        논문 메타데이터 목록.
    """
    query_url = build_query_url(
        keywords,
        max_results=max_results,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(query_url)
        response.raise_for_status()

    return parse_arxiv_feed(response.text)


def format_paper_output(paper: dict[str, Any], index: int) -> str:
    """논문 정보를 출력 문자열로 정리한다.

    Args:
        paper: 논문 메타데이터.
        index: 출력 순번.

    Returns:
        화면 출력용 문자열.
    """
    authors = ", ".join(paper.get("authors", [])) or "알 수 없음"
    return (
        f"[{index}] {paper.get('title', '')}\n"
        f"- 발표일: {paper.get('published', '')}\n"
        f"- 저자: {authors}\n"
        f"- 링크: {paper.get('id', '')}\n"
        f"- 요약: {paper.get('summary', '')}\n"
    )


def format_history_of_science_output(paper: dict[str, Any], index: int) -> str:
    """History of Science 논문을 제목과 요약으로 정리한다.

    Args:
        paper: 논문 메타데이터.
        index: 출력 순번.

    Returns:
        화면 출력용 문자열.
    """
    title = paper.get("title", "")
    summary = paper.get("summary", "")
    return f"[{index}] {title}\n- 요약: {summary}\n"


async def print_history_of_science_papers(max_results: int = 3) -> None:
    """History of Science 최신 논문 정보를 출력한다."""
    keywords = ["History of Science"]
    papers = await fetch_arxiv_papers(
        keywords,
        max_results=max_results,
        sort_by="submittedDate",
        sort_order="descending",
    )

    if not papers:
        print("검색 결과가 없습니다.")
        return

    for index, paper in enumerate(papers, start=1):
        print(format_history_of_science_output(paper, index))


async def main() -> None:
    """History of Science 최신 논문 3편을 출력한다."""
    await print_history_of_science_papers()


if __name__ == "__main__":
    asyncio.run(main())
