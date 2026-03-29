from __future__ import annotations

import os
import requests


HEADERS = {"User-Agent": "Mozilla/5.0"}

# Optional. Leave empty if you do not want GNews.
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")


def normalize(name: str) -> str:
    return name.lower().strip().replace(".", "").replace("_", "").replace(" ", "")


def discover_scheme_links(source_url=None, source_name="", max_links=20):
    source = normalize(source_name)
    results = []
    seen = set()

    # =========================
    # 🔵 myScheme
    # =========================
    if source == "myscheme":
        print("\n🔵 Auto-discovering myScheme schemes")

        slugs = [
            "pmsby",
            "sui",
            "sl",
            "nps-tsep",
            "post-dis",
            "wos-c",
            "nos-swd",
        ]

        for slug in slugs:
            url = f"https://www.myscheme.gov.in/schemes/{slug}"
            if url in seen:
                continue
            seen.add(url)
            results.append(
                {
                    "title": slug,
                    "url": url,
                    "source": "myscheme",
                }
            )

        print(f"✅ Found {len(results)} myScheme schemes")
        return results[:max_links]

    # =========================
    # 🟢 GNews (optional updater)
    # =========================
    elif source == "gnews":
        print("\n🟢 Fetching schemes from GNews API")

        if not GNEWS_API_KEY:
            print("⚠ No GNews API key found. Skipping GNews.")
            return []

        url = (
            "https://gnews.io/api/v4/search"
            "?q=india+government+scheme+yojana+welfare"
            f"&lang=en&max={max_links}&apikey={"65154682645884371dd29f2da5cff849"}"
        )

        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print("GNews error:", e)
            return []

        articles = data.get("articles", [])

        for article in articles:
            title = article.get("title", "")
            link = article.get("url", "")
            desc = article.get("description", "")

            if not title or not link:
                continue

            text = f"{title} {desc}".lower()

            # Light filtering only
            if not any(
                k in text
                for k in [
                    "scheme",
                    "yojana",
                    "welfare",
                    "benefit",
                    "subsidy",
                    "insurance",
                    "pension",
                    "scholarship",
                    "government",
                ]
            ):
                continue

            if link in seen:
                continue

            seen.add(link)
            results.append(
                {
                    "title": title,
                    "url": link,
                    "source": "gnews",
                }
            )

            if len(results) >= max_links:
                break

        print(f"✅ Found {len(results)} GNews articles")
        return results

    # =========================
    # ❌ fallback
    # =========================
    else:
        print(f"\n⚪ No source matched: {source}")
        return []