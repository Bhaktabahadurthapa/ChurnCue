# Paste-ready Archestra App prompt

```text
Create an internal authenticated application named “ChurnCue” for a customer-success team. Archestra is the interface and MCP orchestrator. Do not implement browser fetch calls, invent sample results, calculate ML metrics in JavaScript, or substitute fake data when a tool fails. Every external operation must use an assigned MCP tool.

Build a polished responsive weekly-review workspace with a clear “Run Weekly Review” primary button. The button must orchestrate real assigned tools in this order: load customer rows from the assigned Google Sheets MCP when available (allow the ChurnCue load_demo_dataset tool as an explicitly labeled demo fallback), call profile_dataset, call train_models, pass its experiment_id and rows to score_customers, call compare_weekly_risk, then call generate_rescue_report. Preserve the returned structured values without recomputing metrics.

Show: a data-quality summary; a three-model comparison table with accuracy, precision, recall, F1, ROC-AUC, and confusion matrices; the recommended model; High/Medium/Low risk cards; monthly and annual revenue-at-risk cards; weekly movement totals; and a newly-at-risk customer queue. Add filters for risk level and renewal period and sort customers by annual revenue at risk by default.

Each queue row opens a customer detail panel with anonymous customer ID, current and previous risk, risk change, renewal timing, revenue exposure, evidence-based risk factors, and a rescue-action recommendation. For detail evidence, call explain_risk with the active experiment_id and selected record. Label reasons as observed signals, not proven causes.

Add a Slack message preview using only generate_rescue_report.slack_ready_summary. Add an explicit approval dialog that shows the exact channel and message, with Cancel and “Approve and send” actions. Never invoke the assigned Slack send tool until the authenticated human clicks Approve and send. Show success/failure and keep an audit-friendly intervention status. Do not imply that ChurnCue sends messages.

Implement loading states for every tool sequence, empty states for no rows/no at-risk customers, actionable tool error states with retry, and authentication-required states for Google Sheets and Slack. Keep user-specific display/filter preferences in private storage. Keep intervention owner/status/notes in shared storage so the team sees consistent state. Do not store source customer rows or credentials in public browser storage.

Use accessible contrast, keyboard navigation, semantic labels, confirmation feedback, compact executive cards, and a readable customer table. Never display names, emails, phone numbers, or other PII. Validate the entire app, exercise the real tool flow, and fix all runtime and schema errors before calling it complete.
```

## Refinement prompts

Paste these one at a time if the initial generation needs tightening:

1. `Connect the Run Weekly Review button to the real assigned MCP tools in the specified order. Remove all fabricated fallback results and browser fetch calls.`
2. `Add filters for risk level and renewal period, and preserve those user preferences in private storage.`
3. `Sort customers by annual revenue at risk descending, while allowing the user to change sorting.`
4. `Add the Slack approval dialog. Show the exact channel/message and invoke the Slack send tool only after the authenticated human confirms.`
5. `Store intervention statuses, owner, and notes in shared storage while keeping display preferences private.`
6. `Add explicit loading, empty, MCP error, Sheets authentication, and Slack authentication states.`
7. `Validate the app against the installed tool schemas, run the real weekly-review path, and fix all runtime errors.`
