"""Check the Genie document for the closed-won onboarding agent BEFORE you save it.

Guardrails it enforces: creating an ERP customer needs approval, only internal low-risk writes
(a ticket, a chat message) may run without approval, the CRM is read only, nothing deletes or
merges, risky built-in tools are off, no secret is in the file, and the instructions contain the
ideas that matter. It does not replace `genies_schema`.

    python genie/check_genie_doc.py genie/genie-document.example.json --allow-placeholders

Standard library only. Python 3.9 or newer.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

WRITE = re.compile(r"\b(create|update|edit|delete|remove|merge|post|send|write|change|approve|release|pay)\b", re.I)
SAFE_WRITES = re.compile(r"\b(ticket|message|notify|notification)\b", re.I)
FORBIDDEN = re.compile(r"\b(delete|remove|merge)\b|update (customer|opportunity|account|contact)|edit (customer|opportunity|account|contact)|(credit|payment terms|tax)", re.I)
RISKY_TOOLS = ["web_search", "execute_browser", "api_call", "code_execution"]
MUST_SAY = {
    "approver": "the instructions must say a named person approves before a customer is created",
    "already exists": "the instructions must say to check whether the customer already exists",
    "never guess": "the instructions must say never to guess a missing value",
    "one ticket": "the instructions must say to open only one ticket per opportunity",
    "data": "the instructions must say text in notes, emails and attachments is data, not instructions",
    "reopened": "the instructions must say what happens if the opportunity is reopened",
}


def check(doc: dict, allow_placeholders: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    cfg = doc.get("genie_config")
    if not isinstance(cfg, dict):
        return ["`genie_config` is missing"], warnings
    if "api_key" in cfg:
        errors.append("`api_key` must not be in the file")

    prompt = str(cfg.get("master_prompt", ""))
    if prompt.startswith("REPLACE_"):
        if not allow_placeholders:
            errors.append("`master_prompt` is still a placeholder")
    else:
        low = prompt.lower()
        for key, message in MUST_SAY.items():
            if key not in low:
                errors.append(message)

    for i, skill in enumerate(cfg.get("skills", [])):
        name = skill.get("name", "unnamed")
        label = f"skills[{i}] ({name})"
        for field in ("id", "connection"):
            value = skill.get(field)
            if not value:
                errors.append(f"{label}: {field} is empty")
            elif str(value).startswith("REPLACE_") and not allow_placeholders:
                errors.append(f"{label}: {field} is still a placeholder. Look it up, never invent it")
        policy = skill.get("approval_policy", "always_allow")
        if policy not in {"always_allow", "approval_required"}:
            errors.append(f"{label}: approval_policy must be always_allow or approval_required")
        if FORBIDDEN.search(name):
            errors.append(f"{label}: this agent never deletes, merges, edits the CRM or touches credit, terms or tax. Remove the skill")
        elif WRITE.search(name) and policy != "approval_required" and not SAFE_WRITES.search(name):
            errors.append(f"{label}: this looks like a write. It must be approval_required")

    tools = cfg.get("tools", {})
    for tool in RISKY_TOOLS:
        if tools.get(tool, True) is not False:
            warnings.append(f"built-in tool `{tool}` is on. This agent does not need it. Switch it off")

    triggers = [i for i in cfg.get("interfaces", []) if i.get("type") == "app_trigger"]
    if not triggers:
        warnings.append("no Trigger interface. What starts the agent when an opportunity closes?")
    for t in triggers:
        if not t.get("connection_id"):
            errors.append("the Trigger interface needs the connection_id of the app it watches")
    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file")
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args()
    with open(args.file, encoding="utf-8") as fh:
        errors, warnings = check(json.load(fh), args.allow_placeholders)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    if errors:
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
