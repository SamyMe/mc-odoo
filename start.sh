#!/bin/bash
set -e

INTERNAL_PORT=8001
PUBLIC_PORT=${PORT:-8000}

echo "Starting Odoo MCP server on internal port $INTERNAL_PORT..."

# Route MCP backend outbound traffic through proxy (avoids Odoo.com blocking cloud IPs)
PROXY_ENV=""
if [ -n "$PROXY_URL" ]; then
  PROXY_ENV="HTTP_PROXY=$PROXY_URL HTTPS_PROXY=$PROXY_URL NO_PROXY=127.0.0.1,localhost"
  echo "Using outbound proxy for MCP backend"
fi

env $PROXY_ENV python -m mcp_server_odoo \
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
