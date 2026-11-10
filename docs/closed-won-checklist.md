# The closed-won checklist: what must be true before a customer is created

A deal marked Closed Won is a **sales** event. A customer in the ERP is a **finance** record, used for invoices, credit and tax. The checklist is the contract between them.

The runnable version is [`code/rules.json`](../code/rules.json). **The values in it are examples.** Finance, Legal and Sales set the real ones.

## The checklist

| Item | Why the ERP needs it | Usually supplied by |
|---|---|---|
| **Legal entity name** | Invoices go to a legal entity, not a brand | Sales, from the contract |
| **Billing address** (street, city, postal code, country) | Tax treatment and delivery of invoices | Sales, the customer |
| **Billing currency** | You cannot invoice without one | Sales, Finance |
| **Payment terms** | Due dates and cash planning | Finance |
| **Selling entity (subsidiary)** | Which of your companies sells | Finance |
| **Package or products sold** | What to bill | Sales |
| **Signed contract link** | Evidence and audit | Sales |
| **Billing contact with a valid email** | Who receives invoices | Sales, the customer |
| **Tax registration number**, where your rules require one | Invoicing and compliance in some countries | The customer |

## Rules for a good checklist

- **Every item has an owner.** A ticket that says "details missing" helps nobody. "Payment terms, finance can supply" does.
- **Required means required.** If it is optional, it is not on the list.
- **Values come from lists where possible.** Payment terms, selling entity and package are choices, not free text.
- **Format checks are cheap.** A 2 letter country, a 3 letter currency, an email with an at sign.
- **Country rules are yours.** Which countries need a tax number is a Finance and Legal decision. This repo makes no regulatory statement.

## Where each item lives in Salesforce

The checklist often forces a data-model decision. If the legal entity name and tax number do not exist as fields, **add them**. An agent cannot validate a field that does not exist, and it must not guess.

| Need | Typical place |
|---|---|
| Legal entity name | A custom field on Account |
| Tax registration number | A custom field on Account |
| Billing address | Account billing address |
| Payment terms, selling entity | Custom fields on Account or Opportunity |
| Billing contact | A contact with a billing role |
| Contract link | A field on Opportunity |

## Validation is rules, not AI

Checking that a field is present and well formed is deterministic. Keep it in rules where it is cheap, repeatable and testable (`code/validator.py`). The agent adds value by reading messy context and writing a clear request, not by deciding whether a field is empty.

## What a good result looks like

```text
Payment terms (missing). Who can supply it: finance
Billing contact with a valid email (role: billing) (missing). Who can supply it: sales
Tax registration number (required for DE). Who can supply it: customer
```

Run it: `python code/demo.py`.
