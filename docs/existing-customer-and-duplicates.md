# Existing customers: do not create a second one

Creating a second ERP customer for a company you already bill splits its history, its credit limit and its statements. Merging customers later is slow and risky. **Check before you create.**

## What to match on

| Signal | Strength | Notes |
|---|---|---|
| **Tax registration number** | Strong | Same number, same legal entity. Normalize (ignore spaces and punctuation) |
| **Legal name**, normalized | Medium | Ignore case, punctuation and legal suffixes (`Inc`, `LLC`, `GmbH`). Not enough alone to prove anything |
| **Website domain** | Weak alone | Subsidiaries and sister companies share domains |
| **Billing email domain** | Weak | Same reason, and free mail domains mean nothing |

[`code/customer_match.py`](../code/customer_match.py) combines them into **EXACT** (the tax number matches), **LIKELY** (several signals agree) or **NONE**. A shared domain alone is **not** enough to flag a match, so you are not buried in noise.

## The rule: never merge, never guess

- **EXACT or LIKELY:** stop. A person decides: **link** this deal to the existing customer, or confirm it is a different company.
- **NONE:** continue to the draft and approval.
- The agent never merges, never updates the existing customer and never chooses for you.

## Check twice

1. When the details are complete, before drafting.
2. **Again, right before the write**, after approval. A customer may have been created by someone else while the request waited.

## Make the create itself idempotent

Give the new customer an **external reference** built from the opportunity (for example `opp-006Xx...`). If the create is retried, the ERP should return the same customer, not a second one. Many ERPs, NetSuite included, have an external ID field. Confirm that your Stacksync connection exposes it, and use it. If it does not, keep your own record of what was created for each opportunity and check it first.

## Parents, children and subsidiaries

A new subsidiary of an existing customer is a decision, not a duplicate and not a new top-level customer. Flag it for a person. Do not model hierarchies in the agent.

## What about the data you do not have?

If the account has no tax number and the name is close to an existing customer, the answer is **LIKELY**, not NONE. The agent reports it and a person decides.

## Test cases to keep

- Same tax number, different name spelling: EXACT.
- Same normalized name, no tax number: LIKELY.
- Same domain only: NONE.
- A customer that appears after the draft and before the write: no create.
- The create called twice for the same opportunity: one customer.

All of them are in [`code/tests`](../code/tests).
