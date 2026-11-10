import copy
import json
import pathlib
import sys
import unittest

CODE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE))

from customer_match import domain_of, find_existing, normalize_name, normalize_tax_id  # noqa: E402
from demo import build  # noqa: E402
from pipeline import AWAITING_APPROVAL, CANCELLED, CREATED, EXISTING_REVIEW, INCOMPLETE, LINKED, REJECTED  # noqa: E402
from validator import validate  # noqa: E402

BUNDLES = json.loads((CODE / "data" / "opportunities.json").read_text())
CUSTOMERS = json.loads((CODE / "data" / "erp_customers.json").read_text())


class ValidatorTests(unittest.TestCase):
    def test_complete_deal_is_ok(self):
        self.assertTrue(validate(BUNDLES["O-1"])["ok"])

    def test_missing_fields_name_who_can_supply_them(self):
        problems = {p["field"]: p for p in validate(BUNDLES["O-2"])["problems"]}
        self.assertEqual(problems["account.payment_terms"]["owner"], "finance")
        self.assertEqual(problems["contacts"]["owner"], "sales")
        self.assertEqual(problems["account.tax_id"]["owner"], "customer")
        self.assertIn("DE", problems["account.tax_id"]["reason"])

    def test_tax_id_is_only_required_where_rules_say_so(self):
        self.assertTrue(validate(BUNDLES["O-1"])["ok"])  # US, no tax id

    def test_format_checks(self):
        bundle = copy.deepcopy(BUNDLES["O-1"])
        bundle["account"]["currency"] = "DOLLARS"
        bundle["account"]["billing_address"]["country"] = "USA"
        bundle["account"]["payment_terms"] = "whenever"
        fields = {p["field"] for p in validate(bundle)["problems"]}
        self.assertEqual(fields, {"account.currency", "account.billing_address.country", "account.payment_terms"})

    def test_a_billing_contact_needs_a_valid_email(self):
        bundle = copy.deepcopy(BUNDLES["O-1"])
        bundle["contacts"][0]["email"] = "not-an-email"
        self.assertIn("contacts", {p["field"] for p in validate(bundle)["problems"]})


class MatchTests(unittest.TestCase):
    def test_normalizers(self):
        self.assertEqual(normalize_name("Acme, Inc."), "acme")
        self.assertEqual(normalize_tax_id("DE 123-456.789"), "DE123456789")
        self.assertEqual(domain_of("https://www.Acme.example/about"), "acme.example")
        self.assertEqual(domain_of("ana@acme.example"), "acme.example")

    def test_exact_by_tax_id_even_when_names_differ(self):
        m = find_existing(BUNDLES["O-3"]["account"], BUNDLES["O-3"]["contacts"], CUSTOMERS)
        self.assertEqual((m["level"], m["candidates"][0]["id"]), ("EXACT", "C-100"))

    def test_likely_by_name_without_a_tax_id(self):
        m = find_existing(BUNDLES["O-4"]["account"], BUNDLES["O-4"]["contacts"], CUSTOMERS)
        self.assertEqual((m["level"], m["candidates"][0]["id"]), ("LIKELY", "C-101"))

    def test_no_match(self):
        self.assertEqual(find_existing(BUNDLES["O-1"]["account"], BUNDLES["O-1"]["contacts"], CUSTOMERS)["level"], "NONE")

    def test_a_shared_domain_alone_is_not_enough(self):
        account = {**BUNDLES["O-1"]["account"], "website": "https://globex.example", "legal_name": "Totally Different Co"}
        self.assertEqual(find_existing(account, [], CUSTOMERS)["level"], "NONE")


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.flow = build()

    def test_complete_deal_waits_for_approval_and_writes_nothing(self):
        state = self.flow.handle_closed_won("O-1")
        self.assertEqual(state["status"], AWAITING_APPROVAL)
        self.assertEqual(self.flow.erp.writes, [])
        self.assertEqual(state["draft"]["external_id"], "opp-O-1")

    def test_a_deal_that_is_not_closed_won_is_ignored(self):
        state = self.flow.handle_closed_won("O-5")
        self.assertIsNone(state["status"])
        self.assertEqual(self.flow.tickets.tickets, [])

    def test_incomplete_deal_opens_exactly_one_ticket_even_if_triggered_often(self):
        for _ in range(4):
            self.flow.handle_closed_won("O-2")
        self.assertEqual(len(self.flow.tickets.tickets), 1)
        self.assertEqual(self.flow.states["O-2"]["status"], INCOMPLETE)
        self.assertIn("Payment terms", self.flow.tickets.tickets[0]["body"])

    def test_ticket_is_updated_not_duplicated_when_the_missing_list_changes(self):
        self.flow.handle_closed_won("O-2")
        self.flow.crm.bundles["O-2"]["account"]["payment_terms"] = "Net 30"
        self.flow.handle_closed_won("O-2")
        self.assertEqual(len(self.flow.tickets.tickets), 1)
        self.assertEqual(self.flow.tickets.tickets[0]["updates"], 1)
        self.assertNotIn("Payment terms", self.flow.tickets.tickets[0]["body"])

    def test_completing_the_details_closes_the_ticket_and_asks_for_approval(self):
        self.flow.handle_closed_won("O-2")
        b = self.flow.crm.bundles["O-2"]
        b["account"].update(payment_terms="Net 30", tax_id="DE999999999")
        b["contacts"].append({"id": "K-x", "name": "Fin Contact", "email": "fin@soylent.example", "roles": ["billing"]})
        state = self.flow.handle_closed_won("O-2")
        self.assertEqual(state["status"], AWAITING_APPROVAL)
        self.assertEqual(self.flow.tickets.tickets[0]["status"], "solved")

    def test_existing_customers_are_never_created_again(self):
        for opp in ["O-3", "O-4"]:
            self.assertEqual(self.flow.handle_closed_won(opp)["status"], EXISTING_REVIEW)
        self.assertEqual(self.flow.erp.writes, [])

    def test_a_reviewer_can_link_an_existing_customer(self):
        self.flow.handle_closed_won("O-3")
        state = self.flow.link_existing("O-3", "finance@example.com", "C-100")
        self.assertEqual((state["status"], self.flow.crm.erp_ids["O-3"]), (LINKED, "C-100"))
        with self.assertRaises(PermissionError):
            self.flow.link_existing("O-3", None, "C-100")

    def test_no_approver_no_customer(self):
        self.flow.handle_closed_won("O-1")
        with self.assertRaises(PermissionError):
            self.flow.decide("O-1", None, "approve")
        self.assertEqual(self.flow.erp.writes, [])

    def test_approval_creates_once_links_back_and_notifies_once(self):
        self.flow.handle_closed_won("O-1")
        state = self.flow.decide("O-1", "finance@example.com", "approve")
        self.assertEqual(state["status"], CREATED)
        self.assertEqual(len(self.flow.erp.writes), 1)
        self.assertEqual(self.flow.crm.erp_ids["O-1"], state["erp_id"])
        self.assertEqual(sum("now exists" in m for m in self.flow.chat.messages), 1)

    def test_retriggering_after_creation_does_nothing(self):
        self.flow.handle_closed_won("O-1")
        self.flow.decide("O-1", "finance@example.com", "approve")
        for _ in range(3):
            self.flow.handle_closed_won("O-1")
        self.assertEqual(len(self.flow.erp.writes), 1)

    def test_you_cannot_approve_twice(self):
        self.flow.handle_closed_won("O-1")
        self.flow.decide("O-1", "finance@example.com", "approve")
        with self.assertRaises(ValueError):
            self.flow.decide("O-1", "finance@example.com", "approve")

    def test_rejection_creates_nothing_and_says_why(self):
        self.flow.handle_closed_won("O-1")
        state = self.flow.decide("O-1", "finance@example.com", "reject", "wrong entity")
        self.assertEqual(state["status"], REJECTED)
        self.assertEqual(self.flow.erp.writes, [])
        self.assertTrue(any("wrong entity" in m for m in self.flow.chat.messages))

    def test_a_customer_that_appears_before_the_write_stops_the_write(self):
        self.flow.handle_closed_won("O-1")
        self.flow.erp.customers.append({"id": "C-555", "name": "Umbrella Incorporated", "tax_id": "", "domain": "umbrella.example"})
        state = self.flow.decide("O-1", "finance@example.com", "approve")
        self.assertEqual(state["status"], EXISTING_REVIEW)
        self.assertEqual(self.flow.erp.writes, [])

    def test_the_erp_create_is_idempotent_on_the_external_id(self):
        self.flow.handle_closed_won("O-1")
        draft = self.flow.states["O-1"]["draft"]
        first = self.flow.erp.create_customer(draft)
        second = self.flow.erp.create_customer(draft)
        self.assertEqual(first, second)
        self.assertEqual(len(self.flow.erp.writes), 1)

    def test_reopening_cancels_a_pending_approval_and_reclosing_starts_again(self):
        self.flow.handle_closed_won("O-1")
        self.flow.crm.bundles["O-1"]["opportunity"]["stage"] = "Negotiation"
        self.assertEqual(self.flow.handle_closed_won("O-1")["status"], CANCELLED)
        self.flow.crm.bundles["O-1"]["opportunity"]["stage"] = "Closed Won"
        self.assertEqual(self.flow.handle_closed_won("O-1")["status"], AWAITING_APPROVAL)
        self.assertEqual(self.flow.erp.writes, [])

    def test_reopening_after_creation_never_creates_or_deletes_anything(self):
        self.flow.handle_closed_won("O-1")
        self.flow.decide("O-1", "finance@example.com", "approve")
        self.flow.crm.bundles["O-1"]["opportunity"]["stage"] = "Negotiation"
        state = self.flow.handle_closed_won("O-1")
        self.assertEqual(state["status"], CREATED)
        self.assertEqual(len(self.flow.erp.writes), 1)

    def test_a_changed_draft_refreshes_the_approval_request(self):
        self.flow.handle_closed_won("O-1")
        before = self.flow.states["O-1"]["fingerprint"]
        self.flow.crm.bundles["O-1"]["account"]["payment_terms"] = "Net 45"
        state = self.flow.handle_closed_won("O-1")
        self.assertNotEqual(state["fingerprint"], before)
        self.assertEqual(state["draft"]["terms"], "Net 45")
        self.assertTrue(any("refreshed" in line for line in state["log"]))

    def test_every_step_is_logged(self):
        self.flow.handle_closed_won("O-1")
        self.flow.decide("O-1", "finance@example.com", "approve")
        text = " ".join(self.flow.states["O-1"]["log"])
        self.assertIn("approval requested", text)
        self.assertIn("finance@example.com", text)


class HygieneTests(unittest.TestCase):
    def test_no_em_dashes(self):
        for path in CODE.parent.rglob("*.md"):
            self.assertNotIn(chr(0x2014), path.read_text(encoding="utf-8"), str(path))

    def test_data_is_synthetic(self):
        text = (CODE / "data" / "opportunities.json").read_text()
        self.assertNotIn("gmail.com", text)
        self.assertNotIn("stacksync", text.lower())


if __name__ == "__main__":
    unittest.main()
