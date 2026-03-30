def clean_scheme(raw_scheme):
    return {
        "name": raw_scheme.get("name", "").strip(),

        # Add realistic defaults for MVP
        "income_limit": raw_scheme.get("income_limit", 300000),

        "category": raw_scheme.get("category", ["General"]),

        "state": raw_scheme.get("state", "All"),

        "documents": raw_scheme.get("documents", [
            "Aadhaar Card",
            "Income Certificate"
        ]),

        "description": raw_scheme.get("description", "")
    }