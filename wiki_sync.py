import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


LOCAL_WIKI_PATH = Path(__file__).with_name("wiki_local.json")
MAX_WIKI_PAGE_LENGTH = 12000
MAX_WIKI_PAGE_ID_LENGTH = 40


def is_valid_wiki_page_id(page_id):
    return (
        isinstance(page_id, str)
        and page_id == page_id.strip()
        and 0 < len(page_id) <= MAX_WIKI_PAGE_ID_LENGTH
        and all(ord(character) >= 32 for character in page_id)
    )


def _configured_service():
    url = os.environ.get("TOWER_WIKI_SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("TOWER_WIKI_SUPABASE_ANON_KEY", "").strip()
    if not url or not key:
        return None
    return url, key


def _normalize_pages(pages, defaults):
    if not isinstance(pages, dict):
        pages = {}
    normalized = {
        page_id: str(pages.get(page_id, default_content))[:MAX_WIKI_PAGE_LENGTH]
        for page_id, default_content in defaults.items()
    }
    for page_id, content in pages.items():
        if page_id not in normalized and is_valid_wiki_page_id(page_id):
            normalized[page_id] = str(content)[:MAX_WIKI_PAGE_LENGTH]
    return normalized


def _read_local_pages(defaults):
    try:
        with open(LOCAL_WIKI_PATH, "r", encoding="utf-8") as wiki_file:
            return _normalize_pages(json.load(wiki_file), defaults)
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        return _normalize_pages({}, defaults)


def _write_local_pages(pages):
    try:
        temporary_path = Path(f"{LOCAL_WIKI_PATH}.tmp")
        with open(temporary_path, "w", encoding="utf-8") as wiki_file:
            json.dump(pages, wiki_file, ensure_ascii=False)
        temporary_path.replace(LOCAL_WIKI_PATH)
        return True
    except OSError:
        return False


def _request(url, key, method, payload=None):
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=4) as response:
        response_body = response.read()
    if not response_body:
        return None
    return json.loads(response_body.decode("utf-8"))


def _upsert_remote_page(service, page_id, content):
    url, key = service
    endpoint = f"{url}/rest/v1/game_wiki_pages?on_conflict=page_id"
    _request(endpoint, key, "POST", [{"page_id": page_id, "content": content}])


def load_wiki_pages(defaults):
    service = _configured_service()
    if service is None:
        return _read_local_pages(defaults), "Local only"

    url, key = service
    try:
        rows = _request(
            f"{url}/rest/v1/game_wiki_pages?select=page_id,content,created_at&order=created_at.asc,page_id.asc",
            key,
            "GET",
        )
        local_pages = _read_local_pages(defaults)
        remote_pages = {
            row["page_id"]: row["content"]
            for row in rows or []
            if isinstance(row, dict) and isinstance(row.get("page_id"), str)
        }
        pages = _normalize_pages(remote_pages, defaults)
        for page_id, default_content in defaults.items():
            if page_id not in remote_pages:
                initial_content = local_pages.get(page_id, default_content)
                _upsert_remote_page(service, page_id, initial_content[:MAX_WIKI_PAGE_LENGTH])
                pages[page_id] = initial_content[:MAX_WIKI_PAGE_LENGTH]
        _write_local_pages(pages)
        return pages, "Shared"
    except (URLError, TimeoutError, OSError, ValueError, TypeError):
        return _read_local_pages(defaults), "Offline; using local copy"


def save_wiki_page(page_id, content, pages):
    if not is_valid_wiki_page_id(page_id):
        return False, f"Page titles must be 1-{MAX_WIKI_PAGE_ID_LENGTH} characters"
    if page_id not in pages:
        return False, "Unknown page"
    content = str(content)
    if len(content) > MAX_WIKI_PAGE_LENGTH:
        return False, f"Page limit: {MAX_WIKI_PAGE_LENGTH} characters"

    updated_pages = dict(pages)
    updated_pages[page_id] = content
    _write_local_pages(updated_pages)

    service = _configured_service()
    if service is None:
        return True, "Local only"
    try:
        _upsert_remote_page(service, page_id, content)
        return True, "Shared"
    except (URLError, TimeoutError, OSError, ValueError, TypeError):
        return True, "Offline; saved locally"