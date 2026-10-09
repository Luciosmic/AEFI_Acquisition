"""
Observability MCP Server

Responsibility
---------------
Exposes a read-only MCP (Model Context Protocol) surface over the
already-constructed application services, so an LLM client (e.g. Claude)
can observe the running AEFI Acquisition app in parallel with the PySide6
UI — without instantiating a second set of services and without duplicating
state.

Rationale
---------
The UI and an LLM client must be able to coexist without either one owning
a competing copy of application state. The services built once in
`main.py`'s composition root are passed in here by closure and queried
directly; this module never constructs its own `ScanApplicationService` or
talks to hardware ports itself.

This first scaffold is intentionally read-only (query methods only, no
command/mutation tools): giving an LLM write access to hardware motion or
acquisition without human supervision is a separate decision, not bundled
into this one.

Design
------
Built on the official `mcp` Python SDK's `FastMCP`, transport
`streamable-http` (not `stdio`): the UI's `QApplication` event loop owns
the main thread and must keep running independently of any MCP client's
connection lifecycle. `run_observability_mcp_server` is a blocking call —
the caller (see `src/main.py`) starts it in a daemon `threading.Thread`,
bound to localhost only.
"""

import logging
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP

from application.services.scan_application_service.scan_application_service import (
    ScanApplicationService,
)

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def build_observability_mcp_server(
    scan_service: ScanApplicationService,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> FastMCP:
    """Build the read-only observability MCP server.

    Registers one tool, `get_scan_status`, backed directly by the existing
    `ScanApplicationService.get_status()` query. No new service instance is
    created and no hardware port is touched here.
    """
    mcp = FastMCP("aefi-observability", host=host, port=port)

    @mcp.tool()
    def get_scan_status() -> dict:
        """Return the current scan status (ScanStatusDTO) as JSON."""
        return asdict(scan_service.get_status())

    return mcp


def run_observability_mcp_server(
    scan_service: ScanApplicationService,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Run the observability MCP server. Blocking — call from a daemon thread."""
    mcp = build_observability_mcp_server(scan_service, host=host, port=port)
    logger.info(
        "Observability MCP server: starting (read-only) on http://%s:%s%s",
        host, port, mcp.settings.streamable_http_path,
    )
    try:
        mcp.run(transport="streamable-http")
    except BaseException:  # SystemExit (e.g. uvicorn bind failure) is silent in a thread
        logger.exception("Observability MCP server: thread died on %s:%s", host, port)
        raise
    logger.warning("Observability MCP server: run() returned on %s:%s (stopped)", host, port)
