from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


# ---------- helpers ----------

def _normalize_text(value: Any) -> str:
    return str(value).strip().lower()


def _safe_int(value: Any):
    try:
        return int(float(value))
    except Exception:
        return None


def parse_age_rule(rule: Any) -> Tuple[int | None, int | None]:
    """
    Converts:
      "18-70" -> (18, 70)
      "18+"   -> (18, None)
      "70-"   -> (None, 70)
      "18"    -> (18, 18)
    """
    if rule is None:
        return None, None

    text = _normalize_text(rule)
    if not text:
        return None, None

    text = text.replace("years", "").replace("year", "").strip()

    m = re.match(r"^(\d+)\s*-\s*(\d+)$", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = re.match(r"^(\d+)\s*\+$", text)
    if m:
        return int(m.group(1)), None

    m = re.match(r"^(\d+)\s*-$", text)
    if m:
        return None, int(m.group(1))

    m = re.match(r"^(\d+)$", text)
    if m:
        n = int(m.group(1))
        return n, n

    return None, None


def parse_income_rule(rule: Any) -> Tuple[int | None, int | None]:
    """
    Supports:
      "low", "low/middle", "middle", "high"
      "< 300000", "300000", "3 lakh", "₹3 lakh"
    Returns rough numeric bands in rupees.
    """
    if rule is None:
        return None, None

    text = _normalize_text(rule)
    if not text:
        return None, None

    # band-based qualitative rules
    if "low/middle" in text or "low and middle" in text:
        return 0, 500000
    if "low" in text and "middle" not in text:
        return 0, 300000
    if "middle" in text:
        return 300000, 1000000
    if "high" in text:
        return 1000000, None

    # numeric extraction
    text = text.replace("₹", "").replace(",", "").replace("rs.", "").replace("rs", "")
    text = text.replace("lakh", "00000")

    m = re.search(r"(\d+)\s*-\s*(\d+)", text)
    if m:
        return int(m.group(1)), int(m.group(2))

    m = re.search(r"<\s*(\d+)", text)
    if m:
        return 0, int(m.group(1))

    m = re.search(r"(\d+)\s*\+", text)
    if m:
        return int(m.group(1)), None

    m = re.search(r"(\d+)", text)
    if m:
        n = int(m.group(1))
        return 0, n

    return None, None


def _matches_list_rule(user_value: str, rule_value: Any) -> bool:
    if not rule_value:
        return True

    user_text = _normalize_text(user_value)
    if not user_text:
        return False

    if isinstance(rule_value, list):
        return any(user_text == _normalize_text(x) or user_text in _normalize_text(x) or _normalize_text(x) in user_text for x in rule_value)

    rule_text = _normalize_text(rule_value)
    if not rule_text:
        return True

    parts = [p.strip() for p in re.split(r"[,/|]", rule_text) if p.strip()]
    if parts:
        return any(user_text == p or user_text in p or p in user_text for p in parts)

    return user_text == rule_text or user_text in rule_text or rule_text in user_text


def _get_eligibility(scheme: Dict[str, Any]) -> Dict[str, Any]:
    eligibility = scheme.get("eligibility", {})
    if isinstance(eligibility, dict):
        return eligibility
    return {}


def _extract_scheme_name(scheme: Dict[str, Any]) -> str:
    return scheme.get("scheme_name") or scheme.get("title") or "Unknown Scheme"


# ---------- scoring ----------

def score_scheme(user: Dict[str, Any], scheme: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
      {
        "scheme_name": ...,
        "score": 0-100,
        "eligible": bool,
        "reasons": [...],
        "missing": [...]
      }
    """
    eligibility = _get_eligibility(scheme)
    reasons: List[str] = []
    missing: List[str] = []
    score = 0

    # weights
    W_AGE = 25
    W_GENDER = 10
    W_INCOME = 20
    W_CATEGORY = 15
    W_OCCUPATION = 10
    W_EDUCATION = 10
    W_STATE = 5
    W_RURAL_URBAN = 5

    # AGE
    user_age = _safe_int(user.get("age"))
    age_rule = eligibility.get("age")
    min_age, max_age = parse_age_rule(age_rule)

    if min_age is not None or max_age is not None:
        if user_age is None:
            missing.append("age")
        else:
            ok = True
            if min_age is not None and user_age < min_age:
                ok = False
            if max_age is not None and user_age > max_age:
                ok = False

            if ok:
                score += W_AGE
                reasons.append(f"Age matches ({user_age})")
            else:
                return {
                    "scheme_name": _extract_scheme_name(scheme),
                    "score": 0,
                    "eligible": False,
                    "reasons": ["Age does not match"],
                    "missing": missing,
                }

    # GENDER
    user_gender = user.get("gender", "")
    gender_rule = eligibility.get("gender")
    if gender_rule:
        if _matches_list_rule(user_gender, gender_rule):
            score += W_GENDER
            reasons.append("Gender matches")
        else:
            return {
                "scheme_name": _extract_scheme_name(scheme),
                "score": 0,
                "eligible": False,
                "reasons": ["Gender does not match"],
                "missing": missing,
            }

    # INCOME
    user_income = _safe_int(user.get("income"))
    income_rule = eligibility.get("income")
    min_income, max_income = parse_income_rule(income_rule)

    if income_rule:
        if user_income is None:
            missing.append("income")
        else:
            ok = True
            if min_income is not None and user_income < min_income:
                ok = False
            if max_income is not None and user_income > max_income:
                ok = False

            if ok:
                score += W_INCOME
                reasons.append("Income matches")
            else:
                score += 0
                reasons.append("Income does not fully match")

    # CATEGORY / CASTE
    user_category = user.get("category", "")
    category_rule = eligibility.get("caste_category") or eligibility.get("category")
    if category_rule:
        if _matches_list_rule(user_category, category_rule):
            score += W_CATEGORY
            reasons.append("Category matches")
        else:
            reasons.append("Category does not match")

    # OCCUPATION
    user_occupation = user.get("occupation", "")
    occupation_rule = eligibility.get("occupation")
    if occupation_rule:
        if _matches_list_rule(user_occupation, occupation_rule):
            score += W_OCCUPATION
            reasons.append("Occupation matches")
        else:
            reasons.append("Occupation does not match")

    # EDUCATION
    user_education = user.get("education", "")
    education_rule = eligibility.get("education")
    if education_rule:
        if _matches_list_rule(user_education, education_rule):
            score += W_EDUCATION
            reasons.append("Education matches")
        else:
            reasons.append("Education does not match")

    # STATE
    user_state = user.get("state", "")
    state_rule = eligibility.get("state")
    if state_rule and _normalize_text(state_rule) not in ["all", "any", "pan india"]:
        if _matches_list_rule(user_state, state_rule):
            score += W_STATE
            reasons.append("State matches")
        else:
            reasons.append("State does not match")

    # RURAL / URBAN
    user_ru = user.get("rural_urban", "")
    ru_rule = eligibility.get("rural_urban")
    if ru_rule:
        if _matches_list_rule(user_ru, ru_rule):
            score += W_RURAL_URBAN
            reasons.append("Area type matches")
        else:
            reasons.append("Area type does not match")

    score = min(score, 100)

    # eligible if age/gender are satisfied and score is reasonable
    eligible = score >= 40

    return {
        "scheme_name": _extract_scheme_name(scheme),
        "score": score,
        "eligible": eligible,
        "reasons": reasons,
        "missing": missing,
        "source_url": scheme.get("source_url", ""),
        "category": scheme.get("category", ""),
        "benefits": scheme.get("benefits", ""),
        "documents_required": scheme.get("documents_required", []),
    }


def recommend_schemes(user: Dict[str, Any], schemes: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    scored = [score_scheme(user, scheme) for scheme in schemes]
    scored = sorted(scored, key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def recommend_nearby_schemes(user: Dict[str, Any], schemes: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Includes schemes with score >= 25 so the user can see near-match suggestions too.
    """
    scored = [score_scheme(user, scheme) for scheme in schemes]
    scored = [s for s in scored if s["score"] >= 25]
    scored = sorted(scored, key=lambda x: x["score"], reverse=True)
    return scored[:top_k]