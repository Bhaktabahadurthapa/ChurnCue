# ChurnCue demo — under three minutes

**0:00–0:20 — Problem.** “Every Monday, customer success must find cancellations before renewal, understand what changed, and prioritize revenue—usually across disconnected spreadsheets.” Show the demo-safe Sheet and state that it contains anonymous synthetic data.

**0:20–0:40 — Archestra and prompt.** Open Archestra and briefly show the app prompt. “Archestra creates the internal interface and orchestrates governed MCP tools; MCP is the typed contract to real capabilities.”

**0:40–1:05 — Run.** Click **Run Weekly Review**. Show the Google Sheets MCP load (or labeled demo loader), then the quality summary. Point out loading/error states and that the browser does not generate results.

**1:05–1:30 — Models.** Show Logistic Regression, Random Forest, and Gradient Boosting metrics plus the recommended model. “Every metric and probability comes from scikit-learn in ChurnCue, not from the LLM.”

**1:30–1:55 — Risk and revenue.** Show high/medium/low cards, annual revenue at risk, weekly movement, and the newly-at-risk queue sorted by annual exposure.

**1:55–2:15 — Evidence.** Open one customer. Show usage decline, payment/support/login/renewal/satisfaction reason codes. “These are deterministic observed signals, not causal claims.” Show the recommended rescue action.

**2:15–2:40 — Human approval.** Open the Slack preview. Cancel once to prove nothing sends automatically, reopen, confirm the channel and exact text, then click **Approve and send**. Show the Slack MCP success and channel message.

**2:40–2:55 — Close.** “Google Sheets provides demo-safe data, ChurnCue MCP performs deterministic ML, Archestra governs the app and tool flow, and Slack receives only human-approved notifications. That turns Monday triage into an auditable rescue workflow.”
