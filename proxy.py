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
