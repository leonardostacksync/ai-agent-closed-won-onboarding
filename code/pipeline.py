"""Closed-won onboarding as a small, testable state machine.

    opportunity closes
       -> validate (rules)                  incomplete -> ONE ticket listing what is missing
       -> does the customer already exist?  yes -> a person reviews, nothing is created
       -> draft the ERP customer            -> approval request
       -> a person approves                 -> check once more, create ONCE, link back, notify

The agent never creates a customer by itself. Every adapter here is an in-memory fake so the
logic runs offline. They show where the safeguards sit. They are not Salesforce, Zendesk or
NetSuite clients. Standard library only. Python 3.9 or newer.
"""
from __future__ import annotations

import hashlib
import json

from customer_match import find_existing
from validator import validate, get

INCOMPLETE, AWAITING_APPROVAL, EXISTING_REVIEW, CREATED, LINKED, REJECTED, CANCELLED = (
    "INCOMPLETE", "AWAITING_APPROVAL", "EXISTING_CUSTOMER_REVIEW", "CREATED", "LINKED", "REJECTED", "CANCELLED")


class FakeCRM:
    def __init__(self, bundles: dict):
        self.bundles = bundles
        self.erp_ids: dict[str, str] = {}

    def get(self, opp_id: str) -> dict:
        return self.bundles[opp_id]

    def set_erp_id(self, opp_id: str, erp_id: str) -> None:
        """In production this is a synced field or a workflow step. Keep it out of the agent's skills."""
        self.erp_ids[opp_id] = erp_id


class FakeTickets:
    def __init__(self):
        self.tickets: list[dict] = []

    def find_open(self, opp_id: str):
        return next((t for t in self.tickets if t["opp"] == opp_id and t["status"] == "open"), None)

    def create(self, opp_id: str, subject: str, body: str) -> dict:
        t = {"id": f"T-{len(self.tickets) + 1}", "opp": opp_id, "subject": subject, "body": body, "status": "open", "updates": 0}
        self.tickets.append(t)
        return t

    def update(self, ticket_id: str, body: str) -> None:
        t = next(t for t in self.tickets if t["id"] == ticket_id)
        t["body"], t["updates"] = body, t["updates"] + 1

    def close(self, ticket_id: str) -> None:
        next(t for t in self.tickets if t["id"] == ticket_id)["status"] = "solved"


class FakeERP:
    def __init__(self, customers: list[dict]):
        self.customers = list(customers)
        self.writes: list[dict] = []

    def create_customer(self, draft: dict) -> str:
        """Idempotent on external_id: a second call returns the existing customer and writes nothing."""
        existing = next((c for c in self.customers if c.get("external_id") == draft["external_id"]), None)
        if existing:
            return existing["id"]
        new_id = f"C-{200 + len(self.writes)}"
        self.customers.append({"id": new_id, "name": draft["company_name"], "tax_id": draft.get("tax_id", ""), "domain": "", "external_id": draft["external_id"]})
        self.writes.append(draft)
        return new_id


class FakeChat:
    def __init__(self):
        self.messages: list[str] = []

    def send(self, text: str) -> None:
        self.messages.append(text)


class Onboarding:
    def __init__(self, crm: FakeCRM, tickets: FakeTickets, erp: FakeERP, chat: FakeChat):
        self.crm, self.tickets, self.erp, self.chat = crm, tickets, erp, chat
        self.states: dict[str, dict] = {}

    # ------------------------------------------------------------------ helpers
    def _state(self, opp_id: str) -> dict:
        return self.states.setdefault(opp_id, {"status": None, "log": [], "ticket": None, "draft": None, "erp_id": None, "fingerprint": None})

    @staticmethod
    def _draft(opp_id: str, bundle: dict) -> dict:
        account = bundle["account"]
        billing = next(c for c in bundle["contacts"] if "billing" in c.get("roles", []))
        return {
            "external_id": f"opp-{opp_id}",
            "company_name": account["legal_name"], "subsidiary": account["subsidiary"], "currency": account["currency"],
            "terms": account["payment_terms"], "billing_address": account["billing_address"], "tax_id": account.get("tax_id", ""),
            "billing_contact": billing["name"], "billing_email": billing["email"],
            "source": {"salesforce_opportunity": opp_id, "contract_url": get(bundle, "opportunity.contract_url")},
        }

    @staticmethod
    def _fingerprint(draft: dict) -> str:
        return hashlib.sha256(json.dumps(draft, sort_keys=True).encode()).hexdigest()[:12]

    @staticmethod
    def _ticket_body(problems: list[dict]) -> str:
        lines = [f"- {p['label']} ({p['reason']}). Who can supply it: {p['owner']}" for p in problems]
        return "To onboard this customer we still need:\n" + "\n".join(lines)

    # ------------------------------------------------------------------ events
    def handle_closed_won(self, opp_id: str) -> dict:
        bundle = self.crm.get(opp_id)
        state = self._state(opp_id)
        if bundle["opportunity"]["stage"] != "Closed Won":
            return self.handle_stage_change(opp_id)

        if state["status"] in {CREATED, LINKED, REJECTED, EXISTING_REVIEW}:
            state["log"].append(f"ignored: already {state['status']}")
            return state

        result = validate(bundle)
        if not result["ok"]:
            body = self._ticket_body(result["problems"])
            open_ticket = self.tickets.find_open(opp_id)
            if open_ticket is None:
                state["ticket"] = self.tickets.create(opp_id, f"Onboarding details needed: {bundle['account']['name']}", body)["id"]
                state["log"].append("ticket opened")
            elif open_ticket["body"] != body:
                self.tickets.update(open_ticket["id"], body)
                state["log"].append("ticket updated")
            state["status"] = INCOMPLETE
            return state

        open_ticket = self.tickets.find_open(opp_id)
        if open_ticket:
            self.tickets.close(open_ticket["id"])
            state["log"].append("ticket closed: details complete")

        match = find_existing(bundle["account"], bundle["contacts"], self.erp.customers)
        if match["level"] != "NONE":
            state["status"], state["match"] = EXISTING_REVIEW, match
            state["log"].append(f"existing customer {match['level']}: a person reviews")
            self.chat.send(f"{bundle['account']['name']} may already exist in the ERP ({match['candidates'][0]['id']}). Nothing was created.")
            return state

        draft = self._draft(opp_id, bundle)
        fingerprint = self._fingerprint(draft)
        if state["status"] == AWAITING_APPROVAL and state["fingerprint"] != fingerprint:
            state["log"].append("draft changed: approval request refreshed")
        elif state["status"] == AWAITING_APPROVAL:
            state["log"].append("ignored: already awaiting approval")
            return state
        else:
            state["log"].append("approval requested")
        state["status"], state["draft"], state["fingerprint"] = AWAITING_APPROVAL, draft, fingerprint
        return state

    def handle_stage_change(self, opp_id: str) -> dict:
        state = self._state(opp_id)
        if state["status"] in {AWAITING_APPROVAL, INCOMPLETE}:
            state["status"] = CANCELLED
            state["log"].append("cancelled: the opportunity is no longer Closed Won")
        elif state["status"] == CREATED:
            state["log"].append("customer already created. No action. Review by hand")
        return state

    def decide(self, opp_id: str, approver: str | None, decision: str, reason: str | None = None) -> dict:
        if not approver:
            raise PermissionError("a decision needs a named approver")
        state = self._state(opp_id)
        if state["status"] != AWAITING_APPROVAL:
            raise ValueError(f"nothing to approve (status: {state['status']})")
        if decision == "reject":
            state["status"] = REJECTED
            state["log"].append(f"rejected by {approver}: {reason or 'no reason'}")
            self.chat.send(f"Onboarding for {opp_id} was rejected: {reason or 'no reason given'}")
            return state
        if decision != "approve":
            raise ValueError("decision must be approve or reject")

        bundle = self.crm.get(opp_id)
        # one more look right before the write: a customer may have appeared since the draft
        match = find_existing(bundle["account"], bundle["contacts"], self.erp.customers)
        if match["level"] != "NONE":
            state["status"], state["match"] = EXISTING_REVIEW, match
            state["log"].append("a matching customer appeared before the write. Nothing created")
            return state
        erp_id = self.erp.create_customer(state["draft"])
        state.update(status=CREATED, erp_id=erp_id)
        state["log"].append(f"customer created by approval of {approver}")
        self.crm.set_erp_id(opp_id, erp_id)
        self.chat.send(f"{bundle['account']['name']} now exists in the ERP as {erp_id}. Onboarding can continue.")
        return state

    def link_existing(self, opp_id: str, reviewer: str | None, erp_id: str) -> dict:
        if not reviewer:
            raise PermissionError("linking needs a named reviewer")
        state = self._state(opp_id)
        if state["status"] != EXISTING_REVIEW:
            raise ValueError(f"nothing to link (status: {state['status']})")
        state.update(status=LINKED, erp_id=erp_id)
        state["log"].append(f"linked to existing customer {erp_id} by {reviewer}")
        self.crm.set_erp_id(opp_id, erp_id)
        return state
