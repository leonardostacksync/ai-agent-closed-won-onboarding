# Rollout and risks

## Rollout in four steps

1. **Sandbox.** Salesforce sandbox, NetSuite sandbox, a test help desk. Run [`code/tests`](../code/tests) and `genies_ask` on every case in [edge cases](edge-cases.md).
2. **Shadow.** The agent drafts and opens tickets. Nobody creates a customer from its output. Compare its drafts with what finance creates by hand. Count differences without inventing targets.
3. **Assisted.** Finance approves every create from the agent's draft. Keep it here for a while. It already removes the lookup work.
4. **Review.** Look weekly at holds, rejections and existing-customer flags. Tune the checklist and the instructions.

Do not skip to automatic creation.

## Risks and controls

| Risk | Control |
|---|---|
| A wrong entity, currency or subsidiary | Validation, a values list, and approval with the evidence on screen |
| A duplicate customer | Match before the draft, again before the write, and an external reference |
| Two tickets or two creates from a repeated trigger | Idempotency (state, markers, external reference) |
| The agent edits sales data | Read-only CRM access. The checker forbids those skills |
| A deal reopened | Cancel pending work. Never delete a created customer |
| Hidden instructions in notes or emails | Treat all text as data. Say so in the instructions. The agent cannot approve its own work |
| Too much access | A NetSuite role that can search and create customers only. A Salesforce user that reads only |
| Silent failure | Alerts, a log you read, a weekly look at stuck states |
| Sensitive data leaving your control | Decide what may be sent to a model provider. Keep contract text out of tickets. See the governance page |
| An approver who is always "yes" | Show evidence. Sample approvals. Rotate reviewers |

## Stop conditions

Pause the agent and go back a step if:

- a second customer is created for the same company
- a customer is created without an approver
- a ticket is duplicated
- instructions hidden in a note change its behavior
- you changed the checklist, the instructions, the model or the skills and have not re-tested

## Ownership

Name an owner for the agent, for the checklist, for the ERP integration role and for the approval policy.

## What this repo does not claim

It makes no claims about time saved, accuracy, compliance or audit readiness. It does not replace your controls, your segregation of duties or your auditors. Whether AI features are in scope of your certifications is something to confirm in writing during a security review. See [Stacksync AI agent governance](https://www.stacksync.com/security/ai-agents).
