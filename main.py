"""Odoo MCP Server — PrefectHQ FastMCP wrapper for Alpic deployment.

Wraps mcp-server-odoo's tool handlers using PrefectHQ's fastmcp,
which is the framework Alpic natively supports.
"""

import json
import os
import asyncio

from fastmcp import FastMCP

from mcp_server_odoo.config import get_config
from mcp_server_odoo.odoo_connection import OdooConnection
from mcp_server_odoo.access_control import AccessController
from mcp_server_odoo.tools import OdooToolHandler

mcp = FastMCP(
    "odoo-mcp-server",
    instructions="MCP server for accessing and managing Odoo ERP data through the Model Context Protocol",
)

# Odoo connection state — initialized on first use
_handler = None
_config = None


async def _get_handler():
    global _handler, _config
    if _handler is not None:
        return _handler

    _config = get_config()
    conn = OdooConnection(_config)
    conn.connect()
    conn.authenticate()
    ac = AccessController(_config, conn)

    # Create a dummy app for the tool handler (it just uses it for logging)
    from mcp.server.fastmcp import FastMCP as _OfficialFastMCP
    _dummy_app = _OfficialFastMCP("dummy")

    _handler = OdooToolHandler(_dummy_app, conn, ac, _config)
    return _handler


@mcp.tool()
async def search_records(
    model: str,
    domain: str = None,
    fields: str = None,
    limit: int = None,
    offset: int = 0,
    order: str = None,
) -> str:
    """Search for records in an Odoo model.

    Args:
        model: The Odoo model name (e.g., 'res.partner')
        domain: Odoo domain filter as JSON string (e.g., '[["is_company","=",true]]')
        fields: Comma-separated field names, or JSON array of field names
        limit: Maximum number of records to return
        offset: Number of records to skip
        order: Sort order (e.g., 'name asc, id desc')
    """
    h = await _get_handler()
    result = await h._handle_search_tool(model, domain, fields, limit, offset, order, ctx=None)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def get_record(model: str, record_id: int, fields: str = None) -> str:
    """Get a specific record by ID from an Odoo model.

    Args:
        model: The Odoo model name (e.g., 'res.partner')
        record_id: The ID of the record to retrieve
        fields: Comma-separated field names, or JSON array of field names
    """
    h = await _get_handler()
    result = await h._handle_get_record_tool(model, record_id, fields, ctx=None)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def list_models() -> str:
    """List all models available in the Odoo instance."""
    h = await _get_handler()
    result = await h._handle_list_models_tool(ctx=None)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def create_record(model: str, values: str) -> str:
    """Create a new record in an Odoo model.

    Args:
        model: The Odoo model name (e.g., 'res.partner')
        values: JSON object of field values (e.g., '{"name": "John", "email": "john@example.com"}')
    """
    h = await _get_handler()
    vals = json.loads(values) if isinstance(values, str) else values
    result = await h._handle_create_record_tool(model, vals, ctx=None)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def update_record(model: str, record_id: int, values: str) -> str:
    """Update an existing record in an Odoo model.

    Args:
        model: The Odoo model name (e.g., 'res.partner')
        record_id: The ID of the record to update
        values: JSON object of field values to update
    """
    h = await _get_handler()
    vals = json.loads(values) if isinstance(values, str) else values
    result = await h._handle_update_record_tool(model, record_id, vals, ctx=None)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def delete_record(model: str, record_id: int) -> str:
    """Delete a record from an Odoo model.

    Args:
        model: The Odoo model name (e.g., 'res.partner')
        record_id: The ID of the record to delete
    """
    h = await _get_handler()
    result = await h._handle_delete_record_tool(model, record_id, ctx=None)
    return json.dumps(result, indent=2, default=str)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
