import os
import re
import sys
from typing import Optional, Tuple


def load_local_secrets() -> None:
    secrets_path = os.path.join(os.path.dirname(__file__), "db 비밀 번호.txt")
    if not os.path.exists(secrets_path):
        return

    try:
        with open(secrets_path, "r", encoding="utf-8") as secrets_file:
            content = secrets_file.read()
    except OSError:
        return

    supabase_url_match = re.search(r"슈퍼베이스 URL:\s*(\S+)", content)
    supabase_key_match = re.search(r"API키\s*:\s*(\S+)", content)
    pinecone_key_match = re.search(r"PINECONE\.IO API키\s*:\s*(\S+)", content)

    if supabase_url_match and not os.getenv("SUPABASE_URL"):
        os.environ["SUPABASE_URL"] = supabase_url_match.group(1)
    if supabase_key_match and not os.getenv("SUPABASE_ANON_KEY"):
        os.environ["SUPABASE_ANON_KEY"] = supabase_key_match.group(1)
    if pinecone_key_match and not os.getenv("PINECONE_API_KEY"):
        os.environ["PINECONE_API_KEY"] = pinecone_key_match.group(1)


def load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    load_local_secrets()


def _sanitize_env_value(value: str) -> str:
    """환경 변수 값을 정리한다.

    Args:
        value: 원본 환경 변수 문자열.

    Returns:
        주석과 따옴표를 제거한 값.
    """
    cleaned = value.strip()
    if "#" in cleaned:
        cleaned = cleaned.split("#", 1)[0].rstrip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (
        cleaned.startswith("'") and cleaned.endswith("'")
    ):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def get_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value:
            cleaned = _sanitize_env_value(value)
            if cleaned:
                return cleaned
    return None


def check_supabase() -> Tuple[bool, str]:
    supabase_url = get_env("SUPABASE_URL", "SUPABASE_PROJECT_URL")
    supabase_key = get_env(
        "SUPABASE_KEY",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_API_KEY",
    )

    if not supabase_url or not supabase_key:
        return False, "missing SUPABASE_URL or SUPABASE_KEY"

    try:
        import requests

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
        }
        response = requests.get(
            f"{supabase_url.rstrip('/')}/rest/v1/",
            headers=headers,
            timeout=10,
        )
        if response.ok:
            return True, f"HTTP {response.status_code}"
        return False, f"HTTP {response.status_code}: {response.text.strip()}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def check_pinecone() -> Tuple[bool, str]:
    pinecone_key = get_env("PINECONE_API_KEY", "PINECONE_KEY")
    pinecone_host = get_env("PINECONE_HOST", "PINECONE_INDEX_HOST")

    if not pinecone_key:
        return False, "missing PINECONE_API_KEY"

    try:
        from pinecone import Pinecone

        if pinecone_host:
            client = Pinecone(api_key=pinecone_key, host=pinecone_host)
        else:
            client = Pinecone(api_key=pinecone_key)
        indexes = client.list_indexes()

        if indexes is None:
            return True, "connected"
        return True, "indexes reachable"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def check_gemini() -> Tuple[bool, str]:
    gemini_key = get_env("GEMINI_API_KEY", "GOOGLE_API_KEY")
    if not gemini_key:
        return False, "missing GEMINI_API_KEY"

    model_name = get_env("GEMINI_MODEL", "GEMINI_MODEL_NAME") or "gemini-1.5-flash"

    try:
        import google.generativeai as genai

        genai.configure(api_key=gemini_key)
        try:
            model = genai.GenerativeModel(model_name=model_name)
            response = model.generate_content("ping")
            if response is None:
                return False, "no response"
            return True, f"model {model_name}"
        except Exception:
            available_models = list(genai.list_models())
            for candidate in available_models:
                methods = getattr(candidate, "supported_generation_methods", [])
                if "generateContent" in methods:
                    fallback_name = candidate.name.replace("models/", "")
                    model = genai.GenerativeModel(model_name=fallback_name)
                    response = model.generate_content("ping")
                    if response is None:
                        return False, f"no response from {fallback_name}"
                    return True, f"model {fallback_name}"
            return False, "no compatible generateContent model found"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    load_env()

    checks = {
        "Supabase": check_supabase(),
        "Pinecone": check_pinecone(),
        "Gemini": check_gemini(),
    }

    all_success = True
    for name, (ok, detail) in checks.items():
        status = "SUCCESS" if ok else "FAIL"
        print(f"{name}: {status} ({detail})")
        all_success = all_success and ok

    if all_success:
        print("ALL CONNECTIONS: SUCCESS")
        return 0

    print("One or more connections failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
