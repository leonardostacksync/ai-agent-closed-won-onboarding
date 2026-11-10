# The ticket for missing details

When the checklist is not complete, the agent asks people for what is missing. A ticket is a good place, because it has an owner, a status and a history.

## One ticket per opportunity

A trigger can fire many times. The agent looks for an **open ticket for this opportunity** first. If one exists it updates it. If not, it creates one. Never two. This is the most common bug in an onboarding automation.

To make that lookup reliable, put the opportunity id in the ticket (a custom field, a tag or the subject) and search for it.

## What goes in the ticket

```text
Subject: Onboarding details needed: <account name>

To onboard this customer we still need:
- Payment terms (missing). Who can supply it: finance
- Billing contact with a valid email (role: billing) (missing). Who can supply it: sales
- Tax registration number (required for DE). Who can supply it: customer
```

| Include | Why |
|---|---|
| Exactly what is missing | So nobody has to guess |
| Who can supply each item | So it is routed, not broadcast |
| A link to the opportunity | One click to fix it |
| The deal's amount and close date | Context for priority |
| Never a secret or full contract text | Tickets are widely visible |

## Keep it current

- When the missing list **changes**, update the ticket. Do not open a new one.
- When everything is present, **close** it with a note.
- If a ticket sits open for too long, remind its owner. A scheduled Genie task is a good fit for "check onboarding tickets older than N days". See [scheduled Genie tasks](https://www.stacksync.com/ai-agents).

## Assign by item, if you can

Route the finance items to the finance queue and the sales items to the account owner. One ticket with several owners works less well than a clear primary owner and clear items.

## Confirm the action exists

A Genie runs single app actions from the connector catalog. **Check that your help desk connector exposes a create-ticket action** and that your connection can use it. Some connectors sync tickets but expose no create action. If yours does not, create the ticket with a workflow, or with the help desk's own automation, and keep the agent to reading and commenting.

## Idempotency test

Trigger the same incomplete opportunity four times. There must be one ticket. See `test_incomplete_deal_opens_exactly_one_ticket_even_if_triggered_often`.
