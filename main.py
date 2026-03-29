from __future__ import annotations

import json
from pathlib import Path

from scraper.discover_links import discover_scheme_links
from scraper.fetch_pages import fetch_page
from scraper.extract_text import extract_text_from_html, extract_title_from_html, extract_meta_description
from scraper.save_data import (
    ensure_dirs,
    save_raw_html,
    save_raw_text,
    save_processed_record,
    build_empty_schema,
)


BASE_DATA_PATH = Path("data/base_schemes.json")

SOURCES = [
    {"name": "myscheme"},
    {"name": "gnews"},
]


def normalize_key(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalnum())


def load_base_dataset(path: Path) -> list[dict]:
    if not path.exists():
        print(f"⚠ Base dataset not found at {path}. Starting with empty base dataset.")
        return []

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠ Could not load base dataset: {e}")
        return []


def record_key(record: dict) -> str:
    return normalize_key(record.get("source_url") or record.get("scheme_name") or record.get("title") or "")


def merge_records(existing: list[dict], new_records: list[dict]) -> list[dict]:
    merged = {record_key(r): r for r in existing if record_key(r)}
    for r in new_records:
        k = record_key(r)
        if k:
            merged[k] = r
    return list(merged.values())


def build_record(source_name: str, scheme_url: str, html: str, text: str) -> dict:
    title = extract_title_from_html(html) or scheme_url
    description = extract_meta_description(html)

    record = build_empty_schema()
    record["scheme_name"] = title
    record["source_url"] = scheme_url
    record["ministry"] = source_name
    record["category"] = ""
    record["eligibility"] = {
        "age": "",
        "gender": "",
        "income": "",
        "caste_category": "",
        "state": "",
        "occupation": "",
        "disability": "",
        "education": "",
        "marital_status": "",
        "rural_urban": "",
    }
    record["documents_required"] = []
    record["benefits"] = description
    record["how_to_apply"] = ""
    record["last_updated"] = ""
    record["raw_text"] = text
    return record


def load_base_records() -> list[dict]:
    base_records = load_base_dataset(BASE_DATA_PATH)
    if base_records:
        print(f"✅ Loaded {len(base_records)} base schemes from {BASE_DATA_PATH}")
    return base_records


def process_source(source_name: str, max_links: int = 20) -> list[dict]:
    dirs = ensure_dirs("data")

    print(f"\n=== Discovering links from: {source_name} ===")

    links = discover_scheme_links(
        source_name=source_name,
        max_links=max_links,
    )

    print(f"Found {len(links)} links")

    processed_records = []

    for i, link in enumerate(links, 1):
        scheme_title = link["title"]
        scheme_url = link["url"]
        link_source = link.get("source", source_name)

        print(f"[{i}] Fetching: {scheme_title}")

        result = fetch_page(scheme_url)

        if not result.html:
            print("  Skipped (fetch failed)")
            continue

        text = extract_text_from_html(result.html)

        save_raw_html(dirs["raw"], scheme_title, scheme_url, result.html)
        save_raw_text(dirs["raw"], scheme_title, text)

        record = build_record(link_source, scheme_url, result.html, text)
        record["last_updated"] = result.fetched_at

        save_processed_record(dirs["processed"], scheme_title, record)
        processed_records.append(record)

    return processed_records


def main():
    all_records = load_base_records()

    for source in SOURCES:
        source_name = source["name"]
        new_records = process_source(source_name, max_links=20)
        all_records = merge_records(all_records, new_records)

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("data/processed/all_schemes.json").write_text(
        json.dumps(all_records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nDone. Saved {len(all_records)} total records")


if __name__ == "__main__":
    main()