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
