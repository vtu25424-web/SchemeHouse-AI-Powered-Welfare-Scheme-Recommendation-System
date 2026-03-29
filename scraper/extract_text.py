from __future__ import annotations

import re
from bs4 import BeautifulSoup


def clean_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_from_html(html: str) -> str:
    """
    Convert HTML to readable plain text.
    Removes scripts/styles and normalizes spacing.
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "canvas"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [clean_whitespace(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    return "\n".join(lines)


def extract_title_from_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return clean_whitespace(soup.title.string)
    return ""


def extract_meta_description(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return clean_whitespace(meta["content"])
    return ""