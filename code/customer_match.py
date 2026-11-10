"""Does this customer already exist in the ERP? Run it BEFORE you create anything.

Creating a second customer for a company you already bill is the expensive mistake: split
history, two credit limits, two statements. Matching never merges. It only tells a person what
looks the same. Standard library only. Python 3.9 or newer.
"""
from __future__ import annotations

import difflib
import re

LEGAL_SUFFIXES = {"inc", "incorporated", "llc", "ltd", "limited", "corp", "corporation", "co", "company", "gmbh", "sa", "sas", "bv", "plc", "ag", "srl"}


def normalize_name(value: str | None) -> str:
    words = re.sub(r"[^\w\s]", " ", (value or "").lower()).split()
    while words and words[-1] in LEGAL_SUFFIXES:
        words.pop()
    return " ".join(words)


def normalize_tax_id(value: str | None) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def domain_of(value: str | None) -> str:
    text = re.sub(r"^[a-z]+://", "", (value or "").strip().lower())
    text = text.split("/", 1)[0].split(":", 1)[0]
    if "@" in text:
        text = text.split("@", 1)[1]
    return re.sub(r"^www\.", "", text)


def find_existing(account: dict, contacts: list[dict], customers: list[dict]) -> dict:
    """Return {"level": "EXACT" | "LIKELY" | "NONE", "candidates": [{id, score, reasons}]}."""
    tax = normalize_tax_id(account.get("tax_id"))
    name = normalize_name(account.get("legal_name") or account.get("name"))
    domain = domain_of(account.get("website"))
    emails = {domain_of(c.get("email")) for c in contacts if c.get("email")}
    out: list[dict] = []

    for cust in customers:
        score, reasons = 0.0, []
        if tax and tax == normalize_tax_id(cust.get("tax_id")):
            score += 1.0
            reasons.append("same tax registration number")
        cname = normalize_name(cust.get("name"))
        if name and cname:
            if name == cname:
                score += 0.5
                reasons.append("same legal name after normalizing")
            elif difflib.SequenceMatcher(None, name, cname).ratio() >= 0.9:
                score += 0.3
                reasons.append("very similar name")
        cdomain = domain_of(cust.get("domain"))
        if domain and cdomain and domain == cdomain:
            score += 0.3
            reasons.append("same website domain")
        if cdomain and cdomain in emails:
            score += 0.2
            reasons.append("a contact uses this domain")
        if score >= 0.5:
            out.append({"id": cust["id"], "score": round(score, 2), "reasons": reasons})

    out.sort(key=lambda c: -c["score"])
    if out and any("same tax registration number" in c["reasons"] for c in out):
        return {"level": "EXACT", "candidates": out}
    return {"level": "LIKELY" if out else "NONE", "candidates": out}
