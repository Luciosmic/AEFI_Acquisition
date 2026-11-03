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

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:  # imported at call time: ~1 s of import cost kept out of the startup critical path
    from mcp.server.fastmcp import FastMCP

from application.services.scan_application_service.scan_application_service import (
    ScanApplicationService,
)

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_LIMIT = 1000

# event_type, since, limit -> events (oldest first), as plain dicts
RecentEventsProvider = Callable[[Optional[str], Optional[datetime], int], List[Dict[str, Any]]]
# level, logger_prefix, limit -> log lines (oldest first), as plain dicts
RecentLogsProvider = Callable[[str, Optional[str], int], List[Dict[str, Any]]]
ScanConfigProvider = Callable[[], Optional[Any]]  # ScanConfigSnapshotDTO | None


def _clamp_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_LIMIT))


def _parse_since(since: Optional[str]) -> Optional[datetime]:
    if not since:
        return None
    parsed = datetime.fromisoformat(since)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def build_observability_mcp_server(
    scan_service: ScanApplicationService,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    recent_events_provider: Optional[RecentEventsProvider] = None,
    recent_logs_provider: Optional[RecentLogsProvider] = None,
    scan_config_provider: Optional[ScanConfigProvider] = None,
) -> FastMCP:
    """Build the read-only observability MCP server.

    `get_scan_status` is always registered (backed by
    `ScanApplicationService.get_status()`). The other tools are registered
    only when their provider is given. No new service instance is created
    and no hardware port is touched here.
    """
    from mcp.server.fastmcp import FastMCP  # in the MCP thread, not at module import

    mcp = FastMCP("aefi-observability", host=host, port=port)

    @mcp.tool()
    def get_scan_status() -> dict:
        """Return the current scan status (ScanStatusDTO) as JSON."""
        return asdict(scan_service.get_status())

    if recent_events_provider is not None:
        @mcp.tool()
        def get_recent_events(
            event_type: Optional[str] = None, since: Optional[str] = None, limit: int = 50
        ) -> List[Dict[str, Any]]:
            """Recent domain events, oldest first.

            event_type: bus topic = lowercase class name (e.g. "scanstarted").
            since: ISO 8601 timestamp (naive = UTC). limit: 1..1000.
            High-frequency types (aefivoltagesampleacquired, positionupdated) are not kept.
            """
            return recent_events_provider(event_type, _parse_since(since), _clamp_limit(limit))

    if recent_logs_provider is not None:
        @mcp.tool()
        def get_recent_logs(
            level: str = "INFO", logger_prefix: Optional[str] = None, limit: int = 200
        ) -> List[Dict[str, Any]]:
            """Recent application log lines at or above `level`, oldest first.

            logger_prefix: keep loggers whose name starts with it (e.g. "application.services.scan").
            limit: 1..1000. Messages are truncated and may contain local file paths.
            """
            return recent_logs_provider(level, logger_prefix, _clamp_limit(limit))

    if scan_config_provider is not None:
        @mcp.tool()
        def get_scan_config() -> Optional[dict]:
            """Configuration of the scan in progress or last started (ScanConfigSnapshotDTO).

            Returns null when no scan has been started in this session.
            `scan_kind` ("step" | "line") tells the shape of `geometry`.
            `differential_settle_delay_ms` is the configured value, not interpreted.
            """
            snapshot = scan_config_provider()
            return asdict(snapshot) if snapshot is not None else None

    return mcp


def run_observability_mcp_server(
    scan_service: ScanApplicationService,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    **providers: Any,
) -> None:
    """Run the observability MCP server. Blocking — call from a daemon thread."""
    mcp = build_observability_mcp_server(scan_service, host=host, port=port, **providers)
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
