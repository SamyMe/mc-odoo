import os
import hashlib
import secrets
import time
import logging
import httpx
from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import StreamingResponse, JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proxy")

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

    url = f"{MCP_BACKEND}/{path}"
    logger.info(f"Proxying {request.method} /{path} -> {url}")

    # Use a long-lived client for streaming — MCP tool calls can take time
    client = httpx.AsyncClient(timeout=300.0, follow_redirects=True)

    try:
        backend_req = client.stream(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=dict(request.query_params),
        )

        resp = await backend_req.__aenter__()

        logger.info(f"Backend responded: {resp.status_code} content-type={resp.headers.get('content-type')}")

        # Filter hop-by-hop headers from the backend response
        fwd_headers = {
            k: v for k, v in resp.headers.multi_items()
            if k.lower() not in ("transfer-encoding", "content-length", "connection")
        }

        async def stream_body():
            try:
                chunk_count = 0
                async for chunk in resp.aiter_raw():
                    chunk_count += 1
                    if chunk_count <= 3:
                        logger.info(f"Chunk #{chunk_count} ({len(chunk)} bytes)")
                    yield chunk
                logger.info(f"Stream complete: {chunk_count} chunks total")
            except Exception as e:
                logger.error(f"Stream error: {e}")
                raise
            finally:
                await resp.aclose()
                await client.aclose()

        return StreamingResponse(
            content=stream_body(),
            status_code=resp.status_code,
            headers=dict(fwd_headers),
            media_type=resp.headers.get("content-type"),
        )
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        await client.aclose()
        return Response(
            content=f'{{"error":"proxy_error","detail":"{e}"}}',
            status_code=502,
            media_type="application/json",
        )
