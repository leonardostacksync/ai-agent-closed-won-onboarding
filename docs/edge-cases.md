# Edge cases to decide before you launch

| # | Situation | What should happen | Why |
|---|---|---|---|
| 1 | The opportunity is **reopened** after the customer was created | Nothing. No delete. A person reviews | Deleting a customer can break invoices |
| 2 | **Closed Won twice** for the same deal | Ignore the second | Idempotency |
| 3 | The **amount or products change** after approval | Do not create a second customer. A different flow (an order change) handles it | The customer is the same |
| 4 | **Two opportunities, one account**, closed on the same day | One customer, both linked | Match by account, not opportunity |
| 5 | An **existing customer** buys again | Link, do not create | Renewal or upsell is not a new customer |
| 6 | A **new subsidiary** of an existing customer | A person decides | Hierarchy is a finance decision |
| 7 | **No billing contact** on the account | Ticket for sales | An invoice needs a recipient |
| 8 | The **country** needs a tax number and there is none | Ticket for the customer | Your rules decide which countries |
| 9 | **Legal name differs** from the account name | Use the legal name. Missing legal name is a ticket | Invoices go to the legal entity |
| 10 | A **partner or reseller** deal | Decide who the customer is: the partner or the end customer | Billing follows the contract |
| 11 | A **free trial or pilot** | Probably no customer yet. Filter it out of the trigger | Nothing to bill |
| 12 | The ticket is **solved but the data is still missing** | Re-validate and reopen the request | Closing a ticket is not completing a checklist |
| 13 | The **approver is slow** | Remind them. Never auto-approve on a timeout | Silence is not a yes |
| 14 | The **approver rejects** | Tell sales why. A new Closed Won event is needed to restart | A rejection is a decision |
| 15 | The **ERP is down** or rate limited | The create fails safely. Retry with the same external reference | Safe to repeat |
| 16 | A **customer appears** between draft and write | Stop and send to review | The second check |
| 17 | **Currency or subsidiary mismatch** with the contract | Hold | A wrong entity is hard to unwind |
| 18 | **Instructions in a note** ("skip approval") | Ignore. It is data | Prompt injection |
| 19 | Opportunity **owner left the company** | Route to a manager | Someone must own the follow-up |
| 20 | **Bulk import** of won deals | Queue it. Do not start thousands of runs at once | Volume |

Write down your answers. Test each one in a sandbox. Many are in [`code/tests`](../code/tests).
