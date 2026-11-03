import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from application.services.scan_application_service.dtos.scan_dtos import ScanConfigSnapshotDTO
from infrastructure.mcp.observability_mcp_server import build_observability_mcp_server


def _scan_service():
    return SimpleNamespace(get_status=lambda: SimpleNamespace())


def _tool_names(mcp):
    return {t.name for t in asyncio.run(mcp.list_tools())}


def _call(mcp, name, args=None):
    return asyncio.run(mcp.call_tool(name, args or {}))


def test_without_providers_only_scan_status_is_registered():
    mcp = build_observability_mcp_server(_scan_service())
    assert _tool_names(mcp) == {"get_scan_status"}


def test_each_provider_registers_its_tool():
    mcp = build_observability_mcp_server(
        _scan_service(),
        recent_events_provider=lambda t, s, n: [],
        recent_logs_provider=lambda lvl, p, n: [],
        scan_config_provider=lambda: None,
    )
    assert _tool_names(mcp) == {"get_scan_status", "get_recent_events", "get_recent_logs", "get_scan_config"}


def test_get_recent_events_passes_parsed_since_and_clamped_limit():
    seen = {}

    def provider(event_type, since, limit):
        seen.update(event_type=event_type, since=since, limit=limit)
        return []

    mcp = build_observability_mcp_server(_scan_service(), recent_events_provider=provider)
    _call(mcp, "get_recent_events", {"event_type": "scanstarted", "since": "2026-10-13T10:00:00", "limit": 99999})

    assert seen["event_type"] == "scanstarted"
    assert seen["since"] == datetime(2026, 10, 13, 10, 0, tzinfo=timezone.utc)
    assert seen["limit"] == 1000


def test_get_recent_logs_forwards_filters():
    seen = {}

    def provider(level, prefix, limit):
        seen.update(level=level, prefix=prefix, limit=limit)
        return []

    mcp = build_observability_mcp_server(_scan_service(), recent_logs_provider=provider)
    _call(mcp, "get_recent_logs", {"level": "WARNING", "logger_prefix": "infrastructure"})

    assert seen == {"level": "WARNING", "prefix": "infrastructure", "limit": 200}


def test_get_scan_config_serializes_snapshot_or_none():
    snapshot = ScanConfigSnapshotDTO(
        scan_kind="line", scan_id="abc", fly_scan=False, stabilization_delay_ms=0,
        averaging_per_position=1, differential_mode=False, differential_settle_delay_ms=50.0,
        total_points=3, estimated_duration_s=None, geometry={"length_mm": 4.0},
    )
    current = {"value": snapshot}
    mcp = build_observability_mcp_server(_scan_service(), scan_config_provider=lambda: current["value"])

    _, structured = _call(mcp, "get_scan_config")
    result = structured["result"]  # FastMCP wraps a non-object return type under "result"
    assert result["scan_kind"] == "line"
    assert result["geometry"] == {"length_mm": 4.0}

    current["value"] = None
    _, structured = _call(mcp, "get_scan_config")
    assert structured == {"result": None}
