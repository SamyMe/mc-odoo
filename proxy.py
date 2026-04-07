import os
import base64
import hashlib
import secrets
import time
import logging
import urllib.parse
import httpx
from fastapi import FastAPI, Request, Response, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse

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

# In-memory authorization code store: code_hash -> {redirect_uri, code_challenge, code_challenge_method, expiry}
_auth_codes: dict[str, dict] = {}
AUTH_CODE_EXPIRY_SECONDS = 300


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


@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata(request: Request):
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
    base = str(request.base_url).rstrip("/")
    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "code_challenge_methods_supported": ["S256"],
    })


@app.get("/authorize")
async def authorize(
    response_type: str = Query(""),
    client_id: str = Query(""),
    redirect_uri: str = Query(""),
    state: str = Query(""),
    code_challenge: str = Query(""),
    code_challenge_method: str = Query("S256"),
):
    """OAuth 2.0 Authorization endpoint — auto-approves for this single-user server."""
    if response_type != "code":
        return JSONResponse({"error": "unsupported_response_type"}, status_code=400)

    if client_id != OAUTH_CLIENT_ID:
        return JSONResponse({"error": "invalid_client"}, status_code=400)

    if not redirect_uri:
        return JSONResponse({"error": "missing redirect_uri"}, status_code=400)

    # Generate authorization code
    code = secrets.token_urlsafe(48)
    _auth_codes[_hash(code)] = {
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "expiry": time.time() + AUTH_CODE_EXPIRY_SECONDS,
    }

    # Redirect back to Claude with the code
    params = {"code": code}
    if state:
        params["state"] = state
    redirect_url = f"{redirect_uri}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=redirect_url, status_code=302)


@app.post("/oauth/token")
async def oauth_token(
    grant_type: str = Form("client_credentials"),
    client_id: str = Form(""),
    client_secret: str = Form(""),
    code: str = Form(""),
    redirect_uri: str = Form(""),
    code_verifier: str = Form(""),
):
    """OAuth 2.0 token endpoint — supports authorization_code and client_credentials."""
    if grant_type == "authorization_code":
        # Look up the authorization code
        code_hash = _hash(code)
        stored = _auth_codes.get(code_hash)
        if not stored or stored["expiry"] < time.time():
            if stored:
                del _auth_codes[code_hash]
            return JSONResponse({"error": "invalid_grant"}, status_code=400)

        # Validate redirect_uri matches
        if redirect_uri and redirect_uri != stored["redirect_uri"]:
            return JSONResponse({"error": "invalid_grant", "detail": "redirect_uri mismatch"}, status_code=400)

        # Validate PKCE code_verifier
        if stored["code_challenge"]:
            if not code_verifier:
                return JSONResponse({"error": "invalid_grant", "detail": "missing code_verifier"}, status_code=400)
            # S256: BASE64URL(SHA256(code_verifier)) == code_challenge
            digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
            expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
            if expected != stored["code_challenge"]:
                return JSONResponse({"error": "invalid_grant", "detail": "PKCE verification failed"}, status_code=400)

        # Consume the code (one-time use)
        del _auth_codes[code_hash]

        # Issue access token
        access_token = secrets.token_urlsafe(48)
        _access_tokens[_hash(access_token)] = time.time() + TOKEN_EXPIRY_SECONDS
        return JSONResponse({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRY_SECONDS,
        })

    elif grant_type == "client_credentials":
        if client_id != OAUTH_CLIENT_ID or client_secret != OAUTH_CLIENT_SECRET:
            return JSONResponse({"error": "invalid_client"}, status_code=401)

        access_token = secrets.token_urlsafe(48)
        _access_tokens[_hash(access_token)] = time.time() + TOKEN_EXPIRY_SECONDS
        return JSONResponse({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRY_SECONDS,
        })

    else:
        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)


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
        if k.lower() not in (
            "host", "content-length", "transfer-encoding",
            # Strip proxy/Cloudflare headers so the backend doesn't
            # think it's behind HTTPS and issue bogus 307 redirects
            "x-forwarded-proto", "x-forwarded-for", "x-forwarded-host",
            "x-real-ip", "cf-connecting-ip", "cf-visitor", "cf-ray",
            "cf-ipcountry", "cf-worker", "cdn-loop",
            "true-client-ip",
        )
    }

    url = f"{MCP_BACKEND}/{path}"
    logger.info(f"Proxying {request.method} /{path} -> {url}")

    # Use streaming so SSE / chunked MCP responses work correctly
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
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        await client.aclose()
        return Response(
            content=f'{{"error":"proxy_error","detail":"{e}"}}',
            status_code=502,
            media_type="application/json",
        )

    # Forward response headers, filtering hop-by-hop
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
