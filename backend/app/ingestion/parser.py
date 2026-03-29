def clean_scheme(raw_scheme):
    return {
        "name": raw_scheme.get("name"),
        "income_limit": raw_scheme.get("income_limit", 0),
        "category": raw_scheme.get("category", []),
        "state": raw_scheme.get("state", "All"),
        "documents": raw_scheme.get("documents", [])
    }