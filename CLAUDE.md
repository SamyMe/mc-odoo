# CLAUDE.md — Odoo MCP Server for Railway

You are building a **remote MCP server** that connects Claude to an Odoo ERP instance,
deployable on Railway with zero manual infrastructure work.

---

## Project goal

Create a Docker-based Python application that:
1. Runs `mcp-server-odoo` with `streamable-http` transport
2. Sits behind a lightweight auth proxy that validates Bearer tokens and supports OAuth 2.0 `client_credentials` flow (for Claude web app compatibility)
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

A FastAPI reverse proxy that:
- Returns `200 OK` on `GET /health` with no auth (required by Railway health check)
- Provides an OAuth 2.0 `client_credentials` token endpoint at `POST /oauth/token` (for Claude web app)
- Validates `Authorization: Bearer <token>` on all other routes (accepts both static `BEARER_TOKEN` and OAuth-issued tokens)
- Streams responses from the MCP backend transparently so SSE and chunked transfers work

```python
import os
import hashlib
import secrets
import time
import httpx
from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI(title="Odoo MCP Auth Proxy")

BEARER_TOKEN = os.environ.get("BEARER_TOKEN", "")
OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID", "odoo-mcp")
OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET", BEARER_TOKEN)
INTERNAL_PORT = int(os.environ.get("MCP_BACKEND_PORT", "8001"))
MCP_BACKEND = f"http://127.0.0.1:{INTERNAL_PORT}"

# In-memory token store: token_hash -> expiry timestamp
_access_tokens: dict[str, float] = {}
TOKEN_EXPIRY_SECONDS = 3600


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _valid_token(token: str) -> bool:
    """Check if a token is valid (either a static BEARER_TOKEN or an issued OAuth token)."""
    if BEARER_TOKEN and token == BEARER_TOKEN:
        return True
    h = _hash(token)
    if h in _access_tokens:
        if _access_tokens[h] > time.time():
            return True
        del _access_tokens[h]
    return False


@app.get("/health")
async def health():
    """Railway health check endpoint — no auth required."""
    return {"status": "ok"}


@app.post("/oauth/token")
async def oauth_token(
    grant_type: str = Form("client_credentials"),
    client_id: str = Form(""),
    client_secret: str = Form(""),
):
    """OAuth 2.0 client_credentials token endpoint."""
    if grant_type != "client_credentials":
        return JSONResponse(
            {"error": "unsupported_grant_type"},
            status_code=400,
        )

    if client_id != OAUTH_CLIENT_ID or client_secret != OAUTH_CLIENT_SECRET:
        return JSONResponse(
            {"error": "invalid_client"},
            status_code=401,
        )

    access_token = secrets.token_urlsafe(48)
    _access_tokens[_hash(access_token)] = time.time() + TOKEN_EXPIRY_SECONDS

    return JSONResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": TOKEN_EXPIRY_SECONDS,
    })


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    # Enforce auth on all non-health routes
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ") if auth_header.startswith("Bearer ") else ""
    if not _valid_token(token):
        return Response(
            content='{"error":"Unauthorized","hint":"Provide Authorization: Bearer <token>"}',
            status_code=401,
            media_type="application/json",
        )

    body = await request.body()
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "transfer-encoding")
    }

    # Use a long-lived client for streaming — MCP tool calls can take time
    client = httpx.AsyncClient(timeout=300.0)

    backend_req = client.stream(
        method=request.method,
        url=f"{MCP_BACKEND}/{path}",
        headers=headers,
        content=body,
        params=dict(request.query_params),
    )

    resp = await backend_req.__aenter__()

    # Filter hop-by-hop headers from the backend response
    fwd_headers = {
        k: v for k, v in resp.headers.multi_items()
        if k.lower() not in ("transfer-encoding", "content-length", "connection")
    }

    async def stream_body():
        try:
            async for chunk in resp.aiter_bytes():
                yield chunk
        finally:
            await resp.aclose()
            await client.aclose()

    return StreamingResponse(
        content=stream_body(),
        status_code=resp.status_code,
        headers=dict(fwd_headers),
        media_type=resp.headers.get("content-type"),
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

# OAuth (for Claude web app integration)
OAUTH_CLIENT_ID=odoo-mcp
OAUTH_CLIENT_SECRET=same_as_BEARER_TOKEN_by_default

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
| `BEARER_TOKEN` | Yes | Secret token for direct Bearer auth (Claude Desktop / CLI) |
| `OAUTH_CLIENT_ID` | No | OAuth client ID (defaults to `odoo-mcp`) |
| `OAUTH_CLIENT_SECRET` | No | OAuth client secret (defaults to `BEARER_TOKEN`) |
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

## Claude Desktop / Claude Code / Claude Web configuration (for the human)

Once deployed, the human adds this to their Claude config:

**Claude Web App** (claude.ai):
1. Go to Settings → Connectors → Add custom connector
2. Fill in:
   - **Name:** `odoo`
   - **Remote MCP server URL:** `https://<your-app>.up.railway.app/mcp/`
   - **OAuth Client ID:** `odoo-mcp` (or your custom `OAUTH_CLIENT_ID`)
   - **OAuth Client Secret:** your `BEARER_TOKEN` value (or custom `OAUTH_CLIENT_SECRET`)

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
claude mcp add --transport http odoo \
  https://<your-app>.up.railway.app/mcp/ \
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
- [ ] `POST /oauth/token` with valid `client_id` and `client_secret` returns an `access_token`
- [ ] `POST /oauth/token` with invalid credentials returns `401`
- [ ] OAuth-issued tokens are accepted on MCP routes
- [ ] No secrets appear in any committed file
- [ ] `railway.toml` healthcheck points to `/health`
- [ ] `.gitignore` excludes `.env`
