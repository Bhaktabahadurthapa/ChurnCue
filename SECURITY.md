# Security policy

Security and privacy are product boundaries for ChurnCue, not optional add-ons.

## Supported versions

| Version | Supported |
|---|---|
| Latest `main` | Yes |
| Latest `1.x` release | Yes |
| Older snapshots | No |

## Report a vulnerability

Do not open a public issue for a suspected vulnerability or include customer data, credentials, exploit details, or sensitive logs in public channels.

Use the repository's **Security → Report a vulnerability** flow to create a private GitHub Security Advisory. If private vulnerability reporting is unavailable, contact the repository owner through their GitHub profile and request a private reporting channel before sharing technical details.

Please include:

- Affected commit, version, component, and deployment mode
- Reproduction steps or a minimal proof of concept
- Expected and observed impact
- Suggested mitigation, if known
- Whether the issue may expose PII, credentials, model artifacts, or MCP tool access

## Response targets

The maintainer will aim to acknowledge a report within three business days, provide an initial assessment within seven business days, and coordinate disclosure after a fix is available. These are best-effort targets for an open-source project, not contractual service levels.

## Security model

- ChurnCue accepts anonymous customer records and rejects common PII fields.
- MCP input size, shape, and scalar boundaries are validated.
- Experiment artifacts are resolved only beneath the configured trusted directory.
- The service does not execute user-supplied code or send external messages.
- Slack delivery and source-system credentials stay in Archestra-assigned MCP services.
- The container runs without root privileges or Linux capabilities.

Operators remain responsible for authenticated TLS termination, network isolation, secrets management, dependency updates, access control, backups, and incident monitoring.
