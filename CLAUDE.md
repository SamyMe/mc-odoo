# CLAUDE.md — Odoo MCP Server for Railway

You are building a **remote MCP server** that connects Claude to an Odoo ERP instance,
deployable on Railway with zero manual infrastructure work.

---

## Project goal

Create a Docker-based Python application that:
1. Runs `mcp-server-odoo` with `streamable-http` transport
2. Sits behind a lightweight auth proxy that validates a Bearer token
3. Binds to `0.0.0.0:$PORT` so Railway can route public HTTPS traffic to it
4. Reads all secrets from environment variables (never hardcoded)

---

## Exact file structure to produce

```
odoo-mcp-railway/
├── CLAUDE.md              ← this file
├── Dockerfile
├── railway.toml
├── start.sh
├── proxy.py
├── requirements.txt
└── .env.example
```

Do not create anything outside this list unless explicitly asked.

---

## File specifications

### `requirements.txt`
```
mcp-server-odoo
fastapi
uvicorn[standard]
httpx
```

### `Dockerfile`
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv for fast package installs
RUN pip install --no-cache-dir uv

# Install Python dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application files
COPY proxy.py .
COPY start.sh .
RUN chmod +x start.sh

# Railway injects $PORT at runtime — do not hardcode it
CMD ["./start.sh"]
```

### `railway.toml`
```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

### `start.sh`

This script starts two processes:
- The MCP server on internal port 8001 (never exposed publicly)
- The auth proxy on `$PORT` (Railway's public-facing port)

```bash
#!/bin/bash
set -e

INTERNAL_PORT=8001
PUBLIC_PORT=${PORT:-8000}

echo "Starting Odoo MCP server on internal port $INTERNAL_PORT..."
python -m mcp_server_odoo \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port "$INTERNAL_PORT" &

MCP_PID=$!

# Give the MCP server a moment to initialise before accepting proxied requests
sleep 2

echo "Starting auth proxy on public port $PUBLIC_PORT..."
MCP_BACKEND_PORT="$INTERNAL_PORT" uvicorn proxy:app \
  --host 0.0.0.0 \
  --port "$PUBLIC_PORT" \
  --log-level info

# If uvicorn exits, kill the background MCP process too
kill $MCP_PID 2>/dev/null || true
```

### `proxy.py`

A minimal FastAPI reverse proxy that:
- Returns `200 OK` on `GET /health` with no auth (required by Railway health check)
- Validates `Authorization: Bearer <token>` on all other routes
- Streams responses from the MCP backend transparently so SSE and chunked transfers work

```python
import os
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

app = FastAPI(title="Odoo MCP Auth Proxy")

BEARER_TOKEN = os.environ.get("BEARER_TOKEN", "")
INTERNAL_PORT = int(os.environ.get("MCP_BACKEND_PORT", "8001"))
MCP_BACKEND = f"http://127.0.0.1:{INTERNAL_PORT}"


@app.get("/health")
async def health():
    """Railway health check endpoint — no auth required."""
    return {"status": "ok"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    # Enforce Bearer token on all non-health routes
    if BEARER_TOKEN:
        auth_header = request.headers.get("Authorization", "")
        if auth_header != f"Bearer {BEARER_TOKEN}":
            return Response(
                content='{"error":"Unauthorized","hint":"Provide Authorization: Bearer <token>"}',
                status_code=401,
                media_type="application/json",
            )

    body = await request.body()
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    # Use a long timeout — MCP tool calls can take time
    async with httpx.AsyncClient(timeout=300.0) as client:
        backend_response = await client.request(
            method=request.method,
            url=f"{MCP_BACKEND}/{path}",
            headers=headers,
            content=body,
            params=dict(request.query_params),
        )

    # Stream the response back — critical for MCP SSE / chunked payloads
    return StreamingResponse(
        content=iter([backend_response.content]),
        status_code=backend_response.status_code,
        headers=dict(backend_response.headers),
        media_type=backend_response.headers.get("content-type"),
    )
```

### `.env.example`
```dotenv
# Copy to .env for local testing — never commit .env to git

# Odoo connection
ODOO_URL=https://your-odoo-instance.com
ODOO_API_KEY=your_odoo_api_key_here
ODOO_DB=your_database_name

# Auth proxy — generate with: openssl rand -base64 32
BEARER_TOKEN=replace_with_a_strong_random_token

# Set automatically by Railway — only needed for local runs
PORT=8000
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ODOO_URL` | Yes | Full URL of your Odoo instance |
| `ODOO_API_KEY` | Yes | Odoo API key (Settings → Users → API Keys) |
| `ODOO_DB` | Yes | Odoo database name |
| `BEARER_TOKEN` | Yes | Secret token Claude uses to authenticate |
| `PORT` | Auto | Set by Railway automatically — do not set manually |

Set all of these in Railway's **Variables** tab, not in any committed file.

---

## What NOT to do

- Do not expose the MCP server port (8001) publicly — it must only be reachable by the proxy
- Do not hardcode any secrets, tokens, or URLs in source files
- Do not use `CMD ["uvx", "mcp-server-odoo"]` alone — it won't have the auth proxy
- Do not set `PORT` as a fixed value in `railway.toml` — Railway injects it dynamically
- Do not use `SSE` transport — it is deprecated; always use `streamable-http`
- Do not add a `.env` file to git — it must be in `.gitignore`

---

## .gitignore to create

```
.env
__pycache__/
*.pyc
.DS_Store
```

---

## Deployment steps (for the human, not for you to run)

After you generate all files, the human should:

1. Push the project to a GitHub repository
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select the repository
4. In the service **Variables** tab, add all variables from `.env.example`
5. Go to **Settings → Networking → Generate Domain** to get the public URL
6. Test with:
   ```bash
   curl -H "Authorization: Bearer <BEARER_TOKEN>" \
     https://<your-app>.up.railway.app/health
   ```

---

## Claude Desktop / Claude Code configuration (for the human)

Once deployed, the human adds this to their Claude config:

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "odoo": {
      "type": "streamable-http",
      "url": "https://<your-app>.up.railway.app/mcp/",
      "headers": {
        "Authorization": "Bearer <BEARER_TOKEN>"
      }
    }
  }
}
```

**Claude Code (CLI)**:
```bash
claude mcp add odoo \
  --transport http \
  --url https://<your-app>.up.railway.app/mcp/ \
  --header "Authorization: Bearer <BEARER_TOKEN>"
```

---

## Verification checklist

Before considering the task done, confirm:

- [ ] `Dockerfile` builds successfully with `docker build -t odoo-mcp .`
- [ ] `start.sh` is executable (`chmod +x start.sh` is in the Dockerfile)
- [ ] `GET /health` returns `{"status": "ok"}` with no auth header
- [ ] `GET /mcp/` without a token returns `401 Unauthorized`
- [ ] `GET /mcp/` with the correct `Authorization: Bearer <token>` header returns a valid MCP response
- [ ] No secrets appear in any committed file
- [ ] `railway.toml` healthcheck points to `/health`
- [ ] `.gitignore` excludes `.env`
