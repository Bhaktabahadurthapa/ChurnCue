# Architecture

## Boundaries

Archestra owns the UI, orchestration, tool assignment, authentication states, user preferences, and shared intervention state. A customer-data MCP (for example Google Sheets) owns source reads. ChurnCue owns deterministic calculations and its experiment state. Slack MCP owns delivery, and may be invoked only after an explicit approval step in the app.

ChurnCue accepts JSON records, validates bounded scalar inputs, transforms them into pandas frames, and delegates all learned metrics and probabilities to scikit-learn. It never treats LLM calculations as model output.

## Training flow

1. Validate target, binary classes, minimum sample size, and columns.
2. Remove `customer_id`, the target, and known prediction/output leakage fields.
3. Stratify an 80/20 split with random state 42.
4. Median-impute and standardize numeric data; mode-impute and one-hot encode categories.
5. Fit three independent pipelines and calculate metrics on the held-out test set.
6. Select maximum `(ROC-AUC, F1)` and save its complete pipeline.
7. Atomically record immutable experiment metadata in SQLite.

## Trust and deployment

Artifacts can only be resolved from database records and must remain below the configured artifact directory. Joblib files are trusted service-created files; never place untrusted files in that volume. The container uses UID/GID 10001, drops Linux capabilities, and has `no-new-privileges`. For multi-instance production, replace local persistence and put authenticated TLS termination in front of `/mcp`.
