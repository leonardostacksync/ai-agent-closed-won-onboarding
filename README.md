# AI agent for closed-won onboarding: from a won Salesforce deal to a NetSuite customer, with approval

When a deal closes, someone has to check the details, chase what is missing, make sure the customer does not already exist, and create it in the ERP. That is the gap between sales and finance. This repo shows how to automate it **without creating duplicate customers or creating anything nobody approved**: the checklist, one ticket for missing details, an existing-customer check, a finance approval step, and a state machine that makes the same event twice change nothing.

The agent is a [Stacksync Genie](https://www.stacksync.com/ai-agents): an AI agent that starts when a record changes in a connected app, reads and acts across systems such as Salesforce and NetSuite, pauses for approval before writes and logs every run. The design works for any agent that follows the same rules.

> **Short answer:** start the agent when the opportunity becomes Closed Won, **validate** the deal against a checklist (rules, not AI), open **exactly one ticket** that lists what is missing and who can supply it, **check whether the customer already exists** before drafting, draft the ERP customer and ask **finance to approve**, then check again and create the customer **once** with an external reference. The agent never edits Salesforce, never merges customers and never guesses a missing value.

## The flow

```text
Closed Won -> checklist complete? -- no  -> ONE ticket (what is missing, who supplies it)
                                  -- yes -> customer already exists? -- yes -> a person reviews, nothing created
                                                                      -- no  -> draft -> FINANCE APPROVES
                                                                              -> check again -> create once -> link back -> notify
```

Diagram and parts: [docs/architecture.md](docs/architecture.md).

## Run it in 10 seconds

```bash
cd code
python demo.py                            # five synthetic deals
python -m unittest discover -s tests -v   # 30 tests
```

```text
O-1: AWAITING_APPROVAL         approval requested
O-2: INCOMPLETE                ticket opened
O-3: EXISTING_CUSTOMER_REVIEW  existing customer EXACT: a person reviews
O-4: EXISTING_CUSTOMER_REVIEW  existing customer LIKELY: a person reviews
O-5: ignored (not closed won)

ERP writes so far: 0  (nothing is created before a person approves)
O-1 triggered a second time -> ignored: already awaiting approval
O-1 approved, then triggered again -> ignored: already CREATED | ERP writes: 1
```

## Questions this guide answers

### How do I automate onboarding when an opportunity closes?
Start an agent or workflow on the stage change to Closed Won, check the deal against a checklist, ask for what is missing in a ticket, check for an existing customer, and create the customer after a person approves. See [docs/architecture.md](docs/architecture.md).

### How do I create an ERP customer automatically from Salesforce?
Draft the customer from the opportunity, account and contacts, show it to finance, and create it only after approval, using an external reference so a retry cannot create a second one. Never let the agent create customers unattended at the start. See [docs/approval-design.md](docs/approval-design.md).

### How do I stop duplicate customers in NetSuite?
Match before you draft (tax registration number, normalized legal name, website domain), match **again** right before the write, never merge automatically, and make the create idempotent with an external reference built from the opportunity. See [docs/existing-customer-and-duplicates.md](docs/existing-customer-and-duplicates.md).

### What should be checked before a deal becomes a customer?
Legal entity name, billing address and country, currency, payment terms, selling entity, package, signed contract link, a billing contact with a valid email, and a tax registration number where your rules require one. See [docs/closed-won-checklist.md](docs/closed-won-checklist.md).

### How do I ask sales for missing customer details without spamming them?
One ticket per opportunity that lists exactly what is missing and who can supply each item, updated when the list changes and closed when it is complete. See [docs/ticket-design.md](docs/ticket-design.md).

### What happens if the trigger fires twice, or the deal is reopened?
Nothing the second time. The agent keeps state per opportunity (one ticket, one approval request, one create) and a reopened deal cancels pending work and never deletes a created customer. See [docs/state-and-idempotency.md](docs/state-and-idempotency.md) and [docs/edge-cases.md](docs/edge-cases.md).

### Where should a human approve?
Before the customer is created, every time at the start. The run pauses with the full draft, and finance approves, rejects or edits. The assistant that builds the agent never decides for you. See [docs/approval-design.md](docs/approval-design.md).

### Should this be an AI agent or a workflow?
Rules (a workflow or code) for validation and matching, the Genie for reading messy context and writing a clear request, a sync or workflow for writing the ERP id back to the CRM. If every step can be described in advance, a workflow alone works and runs without AI. See [docs/architecture.md](docs/architecture.md).

### How do I give the agent access to Salesforce and NetSuite safely?
Connect through secure sign-in links, never by pasting credentials into a chat. Salesforce read-only for this agent, a NetSuite role that can search and create customers only. See [docs/salesforce-netsuite-notes.md](docs/salesforce-netsuite-notes.md).

### How do I get the ERP customer id back into Salesforce?
Through a synced field or a workflow, not through the agent. A [two-way sync](https://www.stacksync.com/two-way-sync) between NetSuite customers and Salesforce accounts can carry the id. See [docs/salesforce-netsuite-notes.md](docs/salesforce-netsuite-notes.md).

### Can I build it from Claude or ChatGPT?
Yes, with the [Stacksync MCP server](https://www.stacksync.com/mcp). The assistant drafts the Genie from your job description, saves it after your yes, sets approval on the customer create, adds the Trigger and tests it. See [docs/build-with-mcp.md](docs/build-with-mcp.md) and [prompts/prompts.md](prompts/prompts.md).

### How do I test it before it touches real data?
Test the rules like code, test the agent on the same cases (does it check for an existing customer, open one ticket, stop at approval, ignore instructions in notes), run it in a shadow period, then assisted with full approval. See [docs/rollout-and-risks.md](docs/rollout-and-risks.md).

### Does this replace my finance team or my controls?
No. It prepares work and removes lookups. Approval, segregation of duties and audit stay yours. This repo makes no savings, accuracy or compliance claims.

## What is in this repo

| Path | What it is |
|---|---|
| [`genie/job-description.md`](genie/job-description.md) | The Genie job description |
| [`genie/master-prompt.md`](genie/master-prompt.md) | The instructions to paste into the Genie |
| [`genie/genie-document.example.json`](genie/genie-document.example.json) | An example configuration: Salesforce read-only, ticket and message allowed, customer create needs approval, Trigger on Opportunity, risky tools off |
| [`genie/check_genie_doc.py`](genie/check_genie_doc.py) | Checks that configuration before you save it. 10 tests |
| [`code/rules.json`](code/rules.json), [`code/validator.py`](code/validator.py) | The checklist as editable rules and a validator that names who can supply each missing item |
| [`code/customer_match.py`](code/customer_match.py) | Existing-customer detection: EXACT, LIKELY or NONE. Never merges |
| [`code/pipeline.py`](code/pipeline.py) | The state machine with in-memory fakes for the CRM, help desk, ERP and chat |
| [`code/tests`](code/tests) | 30 tests |
| [`docs/`](docs) | Checklist, trigger design, existing customers, tickets, approval, state and idempotency, edge cases, Salesforce and NetSuite notes, architecture, rollout, MCP |
| [`prompts/prompts.md`](prompts/prompts.md) | 9 prompts |

```bash
./run-tests.sh
```

Python 3.9 or newer, standard library only. All data is synthetic. The fakes in `code/pipeline.py` show where the safeguards sit. They are not Salesforce, Zendesk or NetSuite clients. The values in `code/rules.json` are examples.

## Using it with Stacksync

[Stacksync](https://www.stacksync.com) keeps CRMs, ERPs and databases in sync and lets AI agents act across them. Pages for this: [AI agents (Genies)](https://www.stacksync.com/ai-agents), [AI agent governance](https://www.stacksync.com/security/ai-agents) for approvals, access and logs (with a worked example of a NetSuite write held for approval), the [Salesforce](https://www.stacksync.com/connectors/salesforce) and [NetSuite](https://www.stacksync.com/connectors/netsuite) connectors, and [workflow automation](https://www.stacksync.com/workflow-automation).

Connector behavior and product features change. Check the current docs and test in sandboxes. This repo makes no savings, accuracy, compliance or performance claims.

## Contributing

Corrections and new edge cases are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
