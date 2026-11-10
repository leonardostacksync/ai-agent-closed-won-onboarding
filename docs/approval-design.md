# Approval design: finance approves before the customer exists

## The principle

The agent prepares the customer. A named person approves. The ERP is written only after a decision, and the decision is recorded with who made it.

## Why every create needs approval

A customer record drives invoices, credit, tax and reporting. A wrong entity, currency or subsidiary does not fail loudly. It quietly misbills. Start at **100 percent approval**. In the Genie configuration this is the skill's `approval_policy` set to `approval_required`: the run pauses with the full payload, a reviewer approves, rejects or edits, and the run continues from where it stopped.

## What the reviewer should see

| Show | Why |
|---|---|
| The draft customer record, field by field | What will be created |
| Where each value came from in Salesforce | To spot a wrong source |
| The contract link | The evidence |
| The result of the existing-customer check | The most important check |
| What was missing earlier, and who supplied it | The history |
| The deal amount and owner | Context |

## The reviewers

- **Finance** approves customer creation.
- The reviewer is **not the account owner of the deal**, if your controls forbid it.
- The assistant that builds or tunes the Genie **never** decides an approval for you.

## Approve, reject, edit

| Decision | Effect |
|---|---|
| **Approve** | The agent checks once more for an existing customer, then creates the customer once |
| **Reject** | Nothing is created. Say why. The sales owner is told |
| **Edit** | Fix a field in the draft. The agent refreshes its request |

A decision cannot be decided twice. An approval for a draft that later changes is refreshed, not silently reused.

## What approval does not replace

After approval the agent **still** checks for an existing customer and uses the external reference. Approval says "yes, create it". It does not say "yes, even if it is a duplicate".

## Letting some deals skip approval

Do not, at first. If you ever do, apply it to a narrow case only (an established customer, a small amount, a complete record) and only after weeks of watching the agent agree with your reviewers. Thresholds live in your own workflow or policy logic. Define them explicitly.

## Log everything

Each decision is logged with who made it. The log explorer shows every step of a run and lets you replay one after fixing a cause. See [Stacksync AI agent governance](https://www.stacksync.com/security/ai-agents), which includes a worked example of a NetSuite write held for approval.
