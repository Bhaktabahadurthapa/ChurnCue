# Contributing to ChurnCue

Thank you for helping improve ChurnCue. Contributions should preserve its core promise: deterministic, reviewable customer-risk analysis with human approval before external action.

## Before you begin

- Search existing issues and pull requests before opening a duplicate.
- Use GitHub Discussions or a feature request for broad design proposals.
- Report vulnerabilities privately according to [SECURITY.md](SECURITY.md).
- Never submit real customer PII, credentials, model artifacts, or production datasets.

## Development setup

```bash
git clone https://github.com/Bhaktabahadurthapa/ChurnCue.git
cd ChurnCue
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python scripts/generate_demo_data.py
```

## Make a focused change

1. Create a branch from the latest `main`.
2. Keep the change narrowly scoped and preserve existing public tool schemas unless a breaking change is intentional.
3. Add or update tests for changed behavior.
4. Update README or operator documentation when commands, configuration, or MCP contracts change.
5. Keep customer examples anonymous and deterministic.

## Required checks

```bash
ruff check .
ruff format --check .
pytest
docker build -t churncue:local .
```

Core coverage must remain at or above 80%. Metrics and probabilities must continue to come from scikit-learn rather than an LLM or browser calculation.

## Pull requests

A strong pull request includes:

- A concise statement of the problem and solution
- User, operator, and security impact
- Tests performed and their results
- Documentation changes
- Screenshots only when visual output changed
- No secrets, generated databases, or model artifacts

By contributing, you agree that your contribution is licensed under the repository's [MIT License](LICENSE) and that you will follow the [Code of Conduct](CODE_OF_CONDUCT.md).
