# Build the agent from Claude or ChatGPT (Stacksync MCP)

The [Stacksync MCP server](https://www.stacksync.com/mcp) (`https://mcp.stacksync.com/mcp`) lets an assistant draft, save and test a Genie in your workspace, with exactly your permissions. You sign in with OAuth. **No key, token or ERP credential goes into the chat.** Setup: [docs.stacksync.com/mcp](https://docs.stacksync.com/mcp).

## Safe order of work

1. **Sandbox first.** Create connections through the secure sign-in link. One each for Salesforce, NetSuite, your help desk and Slack.
2. **Describe the job.** Paste [`genie/job-description.md`](../genie/job-description.md). The assistant asks business questions only: what the Genie does, which apps, which actions need approval and who may use it.
3. **Review the draft** in plain words. Nothing is saved until you say yes.
4. **Set approval** on the customer create. The assistant must not leave it on `always_allow`.
5. **Add the Trigger** (Salesforce, Opportunity, stage becomes Closed Won). The assistant sets it up, then you check it is on.
6. **Validate** the configuration: `python genie/check_genie_doc.py`.
7. **Test** with `genies_ask`, then by moving a sandbox opportunity to Closed Won. Read the activity log.
8. **Share** only after it behaves.

## Approvals

When the Genie pauses for the customer create, the assistant shows you the action and its details and asks you to approve or reject. **It never decides for you.** A decided approval cannot be decided again.

## If it misbehaves

Follow the Genie troubleshooting steps: locate the conversation, read its steps and errors, explain the cause, suggest a fix, apply it after your yes, confirm. A Genie that seems stuck is often paused on an approval. A Trigger that never fires is usually paused, missing or filtered to nothing.

## What the MCP server does not replace

Your checklist, your approval policy, your NetSuite role design and your controls.

Prompts: [`prompts/prompts.md`](../prompts/prompts.md).
