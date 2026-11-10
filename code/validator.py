"""Is a closed-won deal complete enough to create a customer in the ERP?

Validation is rules, not AI. The rules live in rules.json so Finance and Sales can read and change
them. The result names exactly what is missing and WHO can supply it, which is what a ticket needs.
Standard library only. Python 3.9 or newer.
"""
from __future__ import annotations

import json
import pathlib
import re

RULES = json.loads((pathlib.Path(__file__).parent / "rules.json").read_text())
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def get(bundle: dict, path: str):
    node = bundle
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _ok(rule: dict, value) -> tuple[bool, str]:
    text = "" if value is None else str(value).strip()
    if not text:
        return False, "missing"
    check = rule["check"]
    if check == "country" and not re.fullmatch(r"[A-Za-z]{2}", text):
        return False, "must be a 2 letter country code"
    if check == "currency" and not re.fullmatch(r"[A-Za-z]{3}", text):
        return False, "must be a 3 letter currency code"
    if check == "one_of" and text not in rule["allowed"]:
        return False, f"must be one of: {', '.join(rule['allowed'])}"
    return True, ""


def validate(bundle: dict, rules: dict | None = None) -> dict:
    """Return {"ok": bool, "problems": [{field, label, owner, reason}]}."""
    rules = rules or RULES
    problems: list[dict] = []

    for rule in rules["required"]:
        ok, reason = _ok(rule, get(bundle, rule["path"]))
        if not ok:
            problems.append({"field": rule["path"], "label": rule["label"], "owner": rule["owner"], "reason": reason})

    billing = [c for c in bundle.get("contacts", []) if "billing" in c.get("roles", []) and EMAIL.fullmatch(str(c.get("email", "")).strip())]
    if not billing:
        spec = rules["billing_contact"]
        problems.append({"field": "contacts", "label": spec["label"], "owner": spec["owner"], "reason": "missing"})

    country = str(get(bundle, "account.billing_address.country") or "").upper()
    if country in rules["tax_id_required_countries"]:
        spec = rules["tax_id"]
        if not str(get(bundle, spec["path"]) or "").strip():
            problems.append({"field": spec["path"], "label": spec["label"], "owner": spec["owner"], "reason": f"required for {country}"})

    return {"ok": not problems, "problems": problems}
