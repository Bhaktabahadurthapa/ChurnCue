# ChurnCue demo — under three minutes

**0:00–0:20 — Problem.** “Every Monday, customer success must find cancellations before renewal, understand what changed, and prioritize revenue—usually across disconnected spreadsheets.” Show the demo-safe Sheet and state that it contains anonymous synthetic data.

**0:20–0:40 — Archestra and prompt.** Open Archestra and briefly show the app prompt. “Archestra creates the internal interface and orchestrates governed MCP tools; MCP is the typed contract to real capabilities.”

**0:40–1:05 — Run.** Click **Run Weekly Review**. Show the labeled demo loader returning a dataset ID and compact summary, then the quality summary. Point out that customer rows remain inside ChurnCue and the browser does not generate results.

**1:05–1:30 — Models.** Show Logistic Regression, Random Forest, and Gradient Boosting metrics plus the recommended model. “Every metric and probability comes from scikit-learn in ChurnCue, not from the LLM.”

**1:30–1:55 — Risk and revenue.** Show high/medium/low cards, annual revenue at risk, weekly movement, plan/renewal-window segments, and the newly-at-risk queue sorted by annual exposure. Point to the focus recommendation: it tells the manager where the largest exposure is concentrated.

**1:55–2:15 — Evidence.** Open one customer. Show usage decline, payment/support/login/renewal/satisfaction reason codes. “These are deterministic observed signals, not causal claims.” Show the recommended contact window and next-best rescue action, then say the human can edit the playbook before acting.

**2:15–2:40 — Human approval.** Open the Slack preview. Cancel once to prove nothing sends automatically, reopen, confirm the channel and exact text, then click **Approve and send**. Show the Slack MCP success and channel message.

**2:40–2:55 — Close.** “ChurnCue keeps demo data behind opaque identifiers and performs deterministic ML, Archestra governs the app and tool flow, and Slack receives only human-approved notifications. That turns Monday triage into an auditable rescue workflow.”
