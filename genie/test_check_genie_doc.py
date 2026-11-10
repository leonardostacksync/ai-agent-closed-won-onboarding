import copy
import json
import pathlib
import re
import unittest

from check_genie_doc import check

HERE = pathlib.Path(__file__).parent
EXAMPLE = json.loads((HERE / "genie-document.example.json").read_text())
PROMPT = (HERE / "master-prompt.md").read_text()


def filled():
    doc = copy.deepcopy(EXAMPLE)
    doc["genie_config"]["master_prompt"] = PROMPT
    for s in doc["genie_config"]["skills"]:
        s["id"], s["connection"] = "mod_1", "conn_1"
    doc["genie_config"]["interfaces"][0]["connection_id"] = "conn_1"
    return doc


def skill(doc, name):
    return next(s for s in doc["genie_config"]["skills"] if s["name"] == name)


class GenieDocTests(unittest.TestCase):
    def test_example_is_valid_with_placeholders_allowed(self):
        self.assertEqual(check(EXAMPLE, allow_placeholders=True)[0], [])

    def test_example_needs_real_ids(self):
        self.assertTrue(any("placeholder" in e for e in check(EXAMPLE)[0]))

    def test_filled_document_is_clean(self):
        self.assertEqual(check(filled()), ([], []))

    def test_create_customer_must_need_approval(self):
        doc = filled()
        skill(doc, "Create customer")["approval_policy"] = "always_allow"
        self.assertTrue(any("must be approval_required" in e for e in check(doc)[0]))

    def test_ticket_and_message_may_run_without_approval(self):
        doc = filled()
        self.assertEqual(skill(doc, "Create ticket")["approval_policy"], "always_allow")
        self.assertEqual(check(doc)[0], [])

    def test_the_crm_is_read_only_and_nothing_deletes_or_merges(self):
        for name in ["Update opportunity", "Delete customer", "Merge customers", "Update customer credit limit", "Edit account"]:
            with self.subTest(name=name):
                doc = filled()
                doc["genie_config"]["skills"].append({"id": "m", "name": name, "type": "Module", "enabled": True, "connection": "c", "approval_policy": "approval_required"})
                self.assertTrue(any("never deletes" in e for e in check(doc)[0]))

    def test_risky_tools_left_on_are_warned(self):
        doc = filled()
        del doc["genie_config"]["tools"]["code_execution"]
        self.assertTrue(any("code_execution" in w for w in check(doc)[1]))

    def test_a_trigger_interface_is_expected(self):
        doc = filled()
        doc["genie_config"]["interfaces"] = []
        self.assertTrue(any("Trigger" in w for w in check(doc)[1]))

    def test_secret_in_file(self):
        doc = filled()
        doc["genie_config"]["api_key"] = "x"
        self.assertTrue(any("api_key" in e for e in check(doc)[0]))

    def test_prompt_missing_an_idea_fails(self):
        for word, phrase in [("already exists", "exists already"), ("one ticket", "a ticket"), ("reopened", "changed")]:
            with self.subTest(word=word):
                doc = filled()
                doc["genie_config"]["master_prompt"] = re.sub(f"(?i){re.escape(word)}", phrase, PROMPT)
                self.assertTrue(check(doc)[0])


if __name__ == "__main__":
    unittest.main()
