"""YouTube 인기 영상 수집을 담당하는 The Scout 에이전트."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Tuple

import httpx

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
DEFAULT_TIMEOUT = 20.0
DEFAULT_MAX_RESULTS = 5
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_PATH = os.path.join(ROOT_DIR, "logs", "omni_system.log")
DEFAULT_KEYWORDS = ["AI", "IT 트렌드"]


def _get_api_key() -> str | None:
    """YouTube API 키를 불러온다.

    Returns:
        API 키 문자열 또는 None.
    """
    return os.getenv("YOUTUBE_API_KEY")


def _build_search_params(keyword: str, api_key: str) -> dict[str, str | int]:
    """YouTube 검색 API 파라미터를 구성한다.

    Args:
        keyword: 검색 키워드.
        api_key: YouTube API 키.

    Returns:
        요청 파라미터 딕셔너리.
    """
    return {
        "part": "snippet",
        "type": "video",
        "order": "viewCount",
        "maxResults": DEFAULT_MAX_RESULTS,
        "q": keyword,
        "key": api_key,
    }


def _parse_youtube_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """YouTube API 응답 아이템을 영상 목록으로 변환한다.

    Args:
        items: API 응답의 items 리스트.

    Returns:
        영상 메타데이터 목록.
    """
    videos: list[dict[str, Any]] = []
    for item in items:
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId", "")
        link = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        videos.append(
            {
                "title": snippet.get("title", ""),
                "video_id": video_id,
                "published": snippet.get("publishedAt", ""),
                "channel": snippet.get("channelTitle", ""),
                "summary": snippet.get("description", ""),
                "link": link,
                "source_url": link,
            }
        )
    return videos


def _format_video_output(video: dict[str, Any], index: int) -> str:
    """영상 정보를 출력 문자열로 정리한다.

    Args:
        video: 영상 메타데이터.
        index: 출력 순번.

    Returns:
        화면 출력용 문자열.
    """
    channel = video.get("channel", "") or "알 수 없음"
    return (
        f"[{index}] {video.get('title', '')}\n"
        f"- 채널: {channel}\n"
        f"- 게시일: {video.get('published', '')}\n"
        f"- 링크: {video.get('link', '')}\n"
        f"- 요약: {video.get('summary', '')}\n"
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


async def fetch_youtube_videos(
    client: httpx.AsyncClient,
    keyword: str,
    api_key: str,
    semaphore: asyncio.Semaphore,
) -> Tuple[bool, str]:
    """YouTube 검색 API를 호출해 영상 데이터를 가져온다.

    Args:
        client: 공유 AsyncClient.
        keyword: 검색 키워드.
        api_key: YouTube API 키.
        semaphore: 동시성 제어 세마포어.

    Returns:
        성공 여부와 JSON 문자열 또는 에러 메시지.
    """
    params = _build_search_params(keyword, api_key)
    async with semaphore:
        try:
            response = await client.get(YOUTUBE_API_URL, params=params)
            response.raise_for_status()
            return True, response.text
        except Exception as exc:
            return False, f"{type(exc).__name__}: {exc}"


async def collect_youtube_videos(
    keywords: list[str],
) -> Tuple[bool, str]:
    """키워드별 YouTube 인기 영상을 병렬 수집한다.

    Args:
        keywords: 검색 키워드 목록.

    Returns:
        성공 여부와 수집된 영상 데이터 또는 에러 메시지.
    """
    if not keywords:
        return False, "검색 키워드가 비어 있습니다."

    api_key = _get_api_key()
    if not api_key:
        return False, "YOUTUBE_API_KEY가 설정되지 않았습니다."

    concurrency = min(len(keywords), 16)
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        tasks = [
            fetch_youtube_videos(client, keyword, api_key, semaphore)
            for keyword in keywords
        ]
        results = await asyncio.gather(*tasks)

    payload: list[dict[str, Any]] = []
    errors: list[str] = []

    for keyword, (ok, body) in zip(keywords, results):
        if not ok:
            errors.append(f"{keyword}: {body}")
            continue
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            errors.append(f"{keyword}: JSON 파싱 실패 ({exc})")
            continue
        items = data.get("items", []) if isinstance(data, dict) else []
        videos = _parse_youtube_items(items)
        payload.append({"keyword": keyword, "videos": videos})

    if errors:
        await log_event(f"YouTube 수집 실패: {' | '.join(errors)}")
        return False, "; ".join(errors)

    await log_event(f"YouTube 수집 성공: {len(payload)}개 키워드")
    return True, _safe_json_dumps(payload)


async def run_scout() -> Tuple[bool, str]:
    """YouTube 인기 영상 정보를 수집하고 보고서를 생성한다.

    Returns:
        성공 여부와 보고서 텍스트.
    """
    ok, payload = await collect_youtube_videos(DEFAULT_KEYWORDS)
    if not ok:
        return False, payload

    try:
        report_data = json.loads(payload)
    except json.JSONDecodeError as exc:
        await log_event(f"보고서 JSON 파싱 실패: {exc}")
        return False, f"JSONDecodeError: {exc}"

    output_lines = ["YouTube Scout Report"]
    for group in report_data:
        keyword = group.get("keyword", "")
        output_lines.append(f"\n[Keyword] {keyword}")
        videos = group.get("videos", [])
        if not videos:
            output_lines.append("- 검색 결과 없음")
            continue
        for index, video in enumerate(videos, start=1):
            output_lines.append(_format_video_output(video, index))

    report_text = "\n".join(output_lines).strip()
    await log_event(f"YouTube 보고서 생성 완료: {len(report_data)}개 키워드")
    return True, report_text


async def main() -> Tuple[bool, str]:
    """YouTube Scout 실행 진입점."""
    return await run_scout()


if __name__ == "__main__":
    success, message = asyncio.run(main())
    if success:
        print(message)
        raise SystemExit(0)
    print(f"ERROR: {message}")
    raise SystemExit(1)
