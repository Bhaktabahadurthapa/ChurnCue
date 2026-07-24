# Archestra setup

UI labels can change between Archestra releases; the sequence below follows the current Platform workflow.

## 1. Start Archestra

For a local hackathon environment with Docker:

```bash
docker pull archestra/platform:latest
docker run --name archestra -p 127.0.0.1:9000:9000 -p 127.0.0.1:3000:3000 \
  -e ARCHESTRA_QUICKSTART=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v archestra-postgres-data:/var/lib/postgresql/data \
  -v archestra-app-data:/app/data \
  --add-host=host.docker.internal:host-gateway \
  archestra/platform:latest
```

Open `http://localhost:3000`. Docker socket access is powerful and appropriate only for a trusted development machine. Use Archestra's Helm deployment for production.

## 2. Add an LLM provider

In Studio, open **Model Providers** (older builds may say **Settings → LLM API Keys**), add OpenAI, Anthropic, Gemini, Cerebras, or Ollama, enter the credential in Archestra—not this repository—and test the provider.

## 3. Start ChurnCue

From this repository run `docker compose up --build`, then verify `curl http://localhost:8000/health` returns `healthy`.

## 4. Register the remote MCP server

Open **MCP Registry / Private MCP Registry**, create a remote server named **ChurnCue**, select **Streamable HTTP**, and enter:

```text
http://host.docker.internal:8000/mcp
```

If Archestra itself runs directly on the host, use `http://localhost:8000/mcp`. Linux Docker users must add `host.docker.internal:host-gateway` to the Archestra container as shown above. Save/install the registry entry. Do not enter credentials; this local demo server has none.

## 5. Inspect health

Open the installed connection's MCP Inspector, connect, list tools, select `health_check`, and run it with `{}`. Expect service `ChurnCue`, version `1.0.0`, status `healthy`, transport `streamable-http`, and an ISO timestamp. A browser GET is not an MCP tool call and is not a supported app integration.

## 6. Assign tools to the app

Create/open the Archestra App, assign all nine ChurnCue tools, and paste `ARCHESTRA_APP_PROMPT.md` into Archestra Chat. Tool assignment is required; the generated app must not calculate or fabricate ML output in browser code.

## 7. Add production data ingestion later

The demo loader stores its synthetic rows inside ChurnCue and returns a `dataset_id`; no customer rows cross the LLM boundary. A production Google Sheets or warehouse adapter should ingest directly into trusted service-side storage and return the same identifier contract. Do not map complete external rows through Archestra chat tool arguments.

## 8. Connect Slack

Install/configure Slack MCP with least-privilege permission for a demo channel. Assign message-preview/read tools as needed and the send tool only to the human-approved action. ChurnCue's report sets `slack_message_sent: false`; only the Slack MCP performs delivery.

## 9. Refresh tools after code changes

Rebuild/restart ChurnCue, return to the installed MCP connection, choose **Refresh/Rescan tools** (or disconnect/reconnect on older builds), verify all schemas in Inspector, then reload/validate the App.

## 10. Troubleshooting

- **Connection refused:** check `docker compose ps`, port 8000, `/health`, and whether Archestra needs `host.docker.internal`.
- **404:** use exactly `/mcp`; `/health` is only a container probe.
- **406/400 in curl:** MCP requires a protocol initialization and correct Accept headers; use MCP Inspector.
- **No tools in App:** install the registry connection, refresh tools, and explicitly assign them.
- **Demo data unavailable:** ensure the image contains `data/demo/customer_churn_demo.csv` and the demo path env var is correct.
- **Artifact unavailable:** inspect volume permissions and keep DB/artifact volumes paired.
- **Sheets/Slack authentication required:** reauthorize their MCP connection in Archestra; never copy tokens into `.env`.
- **Linux host lookup failure:** add the host-gateway mapping to the Archestra service/container.
- **Schema/runtime error:** inspect the MCP tool error, correct scalar types/required keys, refresh tools, and re-run App validation.

Current reference points: [Archestra Platform Deployment](https://archestra.ai/docs/platform-deployment), [Archestra Quickstart](https://archestra.ai/docs/platform-quickstart), [Archestra MCP Orchestrator](https://archestra.ai/docs/platform-orchestrator), and the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).
