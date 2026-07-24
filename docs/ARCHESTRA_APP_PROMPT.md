# Paste-ready Archestra App prompt

```text
Create an internal authenticated application named “ChurnCue” for a customer-success team. Archestra is the interface and MCP orchestrator. The product promise is “turn churn signals into the next best customer action.” Do not implement browser fetch calls, invent sample results, calculate ML metrics in JavaScript, or substitute fake data when a tool fails. Every external operation must use an assigned MCP tool.

Build a polished responsive weekly-review workspace with a clear “Run Weekly Review” primary button. The button must orchestrate real assigned tools in this order: call load_demo_dataset, pass its dataset_id to profile_dataset and train_models, pass dataset_id plus train_models.experiment_id to score_customers, then pass score_customers.score_run_id to compare_weekly_risk, get_portfolio_insights, and generate_rescue_report. Preserve the returned structured values without recomputing metrics. Never copy customer rows through the model context or tool arguments.

Show: a data-quality summary; a three-model comparison table with accuracy, precision, recall, F1, ROC-AUC, and confusion matrices; the recommended model; High/Medium/Low risk cards; monthly and annual revenue-at-risk cards; weekly movement totals; plan and renewal-window exposure segments from get_portfolio_insights; and a newly-at-risk customer queue. Add filters for risk level and renewal period and sort customers by annual revenue at risk by default. Include a compact focus recommendation from largest_exposure_segment so the manager knows where to start.

Each top-risk preview row opens a customer detail panel with anonymous customer ID, plan, renewal window, risk, revenue exposure, evidence-based risk factors, next_best_action, and recommended_contact_window. For detail evidence, call explain_risk with the active score_run_id and selected customer_id. Label reasons as observed signals, not proven causes. Make the next-best action prominent but editable by the human; it is a deterministic playbook recommendation, not an autonomous decision.

Add a Slack message preview using only generate_rescue_report.slack_ready_summary. Add an explicit approval dialog that shows the exact channel and message, with Cancel and “Approve and send” actions. Never invoke the assigned Slack send tool until the authenticated human clicks Approve and send. Show success/failure and keep an audit-friendly intervention status. Do not imply that ChurnCue sends messages.

Implement loading states for every tool sequence, empty states for no records/no at-risk customers, actionable tool error states with retry, and authentication-required states for Slack. Keep user-specific display/filter preferences in private storage. Keep intervention owner/status/notes in shared storage so the team sees consistent state. Do not store source customer rows or credentials in public browser storage.

Use accessible contrast, keyboard navigation, semantic labels, confirmation feedback, compact executive cards, and a readable customer table. Never display names, emails, phone numbers, or other PII. Add a small “How this is governed” panel: model output comes from deterministic Python services, customer rows remain behind opaque IDs, and external messages require human approval. Validate the entire app, exercise the real tool flow including a customer detail explanation and portfolio segments, and fix all runtime and schema errors before calling it complete.
```

## Refinement prompts

Paste these one at a time if the initial generation needs tightening:

1. `Connect the Run Weekly Review button to the real assigned MCP tools in the specified order. Remove all fabricated fallback results and browser fetch calls.`
2. `Add filters for risk level and renewal period, and preserve those user preferences in private storage.`
3. `Sort customers by annual revenue at risk descending, while allowing the user to change sorting.`
4. `Add the Slack approval dialog. Show the exact channel/message and invoke the Slack send tool only after the authenticated human confirms.`
5. `Store intervention statuses, owner, and notes in shared storage while keeping display preferences private.`
6. `Add explicit loading, empty, MCP error, Sheets authentication, and Slack authentication states.`
7. `Validate the app against the installed tool schemas, run the real weekly-review path, exercise a customer detail explanation and portfolio segment view, and fix all runtime errors.`
