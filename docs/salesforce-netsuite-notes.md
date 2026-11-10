# Salesforce and NetSuite notes

From the Stacksync connector documentation. Check the current pages and test in sandboxes.

## Salesforce

- Connect a **dedicated user** made for Stacksync, with only the permissions it needs. It needs **API Enabled**.
- The org's **edition must include the API**. The Stacksync app must be installed in the org once.
- Try everything on a **Salesforce sandbox or developer org** first.
- **Custom fields** (legal entity name, tax number, payment terms) must be visible to the connected user through field-level security, or the agent cannot read them.
- **Formula fields** are read-only and computed. A value you validate may be a formula.
- Give this agent **read access** to Opportunities, Accounts and Contacts. Nothing to write.

## NetSuite

- Connecting needs an admin role, **REST web services** and **token-based authentication** enabled, and an integration record. You connect through a secure sign-in link. The account ID and tokens go into that form, **never into a chat**.
- **Customers** read and write. Vendors, contacts and many transactions do too. Accounts, periods, departments, classes and locations are read-only for now.
- A readable object is not automatically writable. Confirm write support for **customers** in your connection.
- NetSuite caps concurrent requests for the whole account. Stacksync never sends more than 3 at once. Set the integration's **Concurrency Limit** to 3 so it leaves room for others.
- Customer records usually carry fields such as company name, subsidiary, currency, terms, addresses, tax registration and an **external ID**. **Read your connection's live fields** with `connections_tables`. Do not guess names.

## The ERP id going back to Salesforce

After the customer is created, sales needs its ERP id on the account or opportunity. Do this with a **synced field or a workflow**, not with the agent:

- A [two-way sync](https://www.stacksync.com/two-way-sync) between NetSuite customers and Salesforce accounts can carry an id field.
- A workflow can write it after the create.
- A Genie runs single app actions. It never runs a whole workflow, and no workflow step calls a Genie. Keep the agent's skills minimal: read the CRM, search the ERP, create a ticket, create a customer after approval, post a message.

## Skills the agent should have

| Skill | Type | Approval |
|---|---|---|
| Read opportunity, account, contacts | Read | Not needed |
| Search customers (ERP) | Read | Not needed |
| Search tickets | Read | Not needed |
| Create ticket | Write, internal and reversible | Not needed. One per opportunity |
| **Create customer (ERP)** | **Write** | **Required** |
| Post a message | Write, internal | Not needed |

Skills it should **not** have: update or delete anything in Salesforce, update, merge or delete a customer, anything about credit, payment terms or tax on an existing customer. The checker in [`genie/check_genie_doc.py`](../genie/check_genie_doc.py) fails if they appear.

## Confirm before you build

- [ ] The legal name and tax number fields exist in Salesforce and are readable.
- [ ] Your NetSuite connection can **search and create customers**.
- [ ] Your help desk connector exposes a **create ticket** action.
- [ ] Your NetSuite connection exposes an **external ID** field, or you have another way to make the create idempotent.

Docs: [Salesforce connector](https://docs.stacksync.com/two-way-sync/connectors/salesforce), [NetSuite connector](https://docs.stacksync.com/two-way-sync/connectors/netsuite). Pages: [Salesforce](https://www.stacksync.com/connectors/salesforce), [NetSuite](https://www.stacksync.com/connectors/netsuite).
