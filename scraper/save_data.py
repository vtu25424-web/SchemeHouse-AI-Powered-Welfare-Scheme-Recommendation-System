from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict


def ensure_dirs(base_dir: str = "data") -> dict[str, Path]:
    base = Path(base_dir)
    raw_dir = base / "raw"
    processed_dir = base / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return {"base": base, "raw": raw_dir, "processed": processed_dir}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "item"


def save_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def append_jsonl(record: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_raw_html(raw_dir: Path, scheme_name: str, url: str, html: str) -> Path:
    file_name = f"{slugify(scheme_name)}.html"
    path = raw_dir / file_name
    path.write_text(html or "", encoding="utf-8")
    return path


def save_raw_text(raw_dir: Path, scheme_name: str, text: str) -> Path:
    file_name = f"{slugify(scheme_name)}.txt"
    path = raw_dir / file_name
    path.write_text(text or "", encoding="utf-8")
    return path


def save_processed_record(processed_dir: Path, scheme_name: str, record: Dict[str, Any]) -> Path:
    file_name = f"{slugify(scheme_name)}.json"
    path = processed_dir / file_name
    save_json(record, path)
    return path


def build_empty_schema() -> Dict[str, Any]:
    return {
        "scheme_name": "",
        "source_url": "",
        "ministry": "",
        "category": "",
        "eligibility": {
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
        },
        "documents_required": [],
        "benefits": "",
        "how_to_apply": "",
        "last_updated": "",
        "raw_text": "",
    }