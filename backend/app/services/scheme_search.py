import json

def load_schemes():
    with open("backend/data/base_schemes.json", "r", encoding="utf-8") as f:
        base = json.load(f)

    with open("backend/data/processed/all_schemes.json", "r", encoding="utf-8") as f:
        auto = json.load(f)

    # merge
    seen = set()
    merged = []

    for s in base + auto:
        url = s.get("source_url")
        if url not in seen:
            seen.add(url)
            merged.append(s)

    return merged