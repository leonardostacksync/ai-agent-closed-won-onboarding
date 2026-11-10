# Trigger design: when does the agent start?

"When an opportunity closes" is less simple than it sounds.

## The trigger

A [Genie can start when a record changes in a connected app](https://www.stacksync.com/ai-agents) through a **Trigger** interface. You choose the connection, the table (Opportunity), the changes (created, updated, deleted) and filters. For this agent: an update where the stage becomes **Closed Won**.

The Trigger is set up in two steps: the Genie gets an interface of type Trigger, then an app trigger defines the tables, operations and filters. Your assistant can do both through the Stacksync MCP server after you approve. Check that the trigger is switched on, and that its filters match something, or the Genie never starts.

## Triggers fire more than once

Assume every trigger can fire **again** for the same opportunity:

| Cause | What happens |
|---|---|
| Someone edits a field on an already won deal | An update event |
| A workflow or a sync touches the record | An update event |
| The stage is changed back and forth | Two or more Closed Won events |
| A retry after a failure | The same event |

So the agent must be **idempotent**: handling the same event twice must change nothing the second time. See [state and idempotency](state-and-idempotency.md).

## Filter as much as you can

Start the agent only for what it should handle:

| Filter | Why |
|---|---|
| Stage = Closed Won | The point |
| Record type is "New business" | Renewals and upsells are a different flow |
| Amount above zero | Free and internal deals may not need a customer |
| Not already onboarded | A status field avoids reprocessing |

Filters in the trigger save runs. The agent still checks the same conditions itself, because a trigger setting is not a guarantee.

## New customer, or an existing one?

A won deal from a customer you already bill should not create a customer. The agent checks the ERP first ([existing customers](existing-customer-and-duplicates.md)). Decide separately what an upsell or renewal should trigger: probably a sales order, which is a different agent.

## Volume

Per-record automation is designed for low volume, in the range of a few hundred changes an hour. Closed-won deals are far below that for almost every company. If a bulk update ever touches thousands of opportunities at once, queue the work instead.

## Test the trigger first

1. Create a test opportunity in a **sandbox**.
2. Move it to Closed Won.
3. Check that the Genie ran once, with `genies_activity`.
4. Move it back and forth. Check it did not duplicate anything.

## Reopened deals

A deal can come back from Closed Won. Decide what happens: cancel a pending approval, and **never delete a customer that was already created**. See [edge cases](edge-cases.md).
