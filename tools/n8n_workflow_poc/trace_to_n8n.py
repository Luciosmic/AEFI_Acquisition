"""
Convert a DiagramFriendlyTest interaction trace (src/tool/diagram_friendly_test.py)
into an importable n8n workflow, laid out by DDD layer:
domain events on top, application orchestration in the middle, infrastructure
adapters/ports at the bottom.

Usage:
    uv run python tools/n8n_workflow_poc/trace_to_n8n.py <trace.json> <workflow.json>
"""
import json
import sys

LAYER_Y = {"domain": 40, "application": 340, "infrastructure": 640}
X_STEP = 260

# ponytail: static lookup, not a classifier — good enough while the trace only
# names a handful of actors. Extend the dict when new actors show up.
ACTOR_LAYER = {
    "Test": "application",
    "ScanApplicationService": "application",
    "Scan2DConfigDTO": "application",
    "EventBus": "infrastructure",
    "MotionPort": "infrastructure",
    "AcquisitionPort": "infrastructure",
}


def resolve_layer(interaction: dict) -> str:
    # A domain event riding the bus (data.event set) is shown at the domain
    # layer regardless of which infra actor carried it (EventBus).
    data = interaction.get("data") or {}
    if data.get("event"):
        return "domain"
    return ACTOR_LAYER.get(interaction["target"], ACTOR_LAYER.get(interaction["actor"], "application"))


def build_workflow(trace: dict, name: str) -> dict:
    interactions = [i for i in trace["interactions"] if i["action"] != "DIVIDER"]

    nodes = []
    pin_data = {}
    for idx, interaction in enumerate(interactions):
        layer = resolve_layer(interaction)
        label = f"{interaction['actor']} {interaction['action']} {interaction['target']}"
        node_name = f"{idx}. {label}"[:64]

        payload = {
            "actor": interaction["actor"],
            "action": interaction["action"],
            "target": interaction["target"],
            "message": interaction["message"],
        }
        if interaction.get("data"):
            payload["data"] = interaction["data"]
        if interaction.get("expect") is not None:
            payload["expect"] = interaction["expect"]
            payload["got"] = interaction["got"]

        nodes.append({
            "id": f"n{idx}",
            "name": node_name,
            "type": "n8n-nodes-base.noOp",
            "typeVersion": 1,
            "position": [idx * X_STEP, LAYER_Y[layer]],
            "notes": interaction["message"],
            "notesInFlow": True,
            "parameters": {},
        })
        # Pinned data: n8n shows this as the node's Output (and the next
        # node's Input) without needing to actually execute the workflow.
        pin_data[node_name] = [{"json": payload}]

    for layer, y in LAYER_Y.items():
        width = max(len(nodes) * X_STEP, X_STEP) + 200
        nodes.append({
            "id": f"band_{layer}",
            "name": f"layer: {layer}",
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": [-220, y - 60],
            "parameters": {"content": f"## {layer}", "height": 220, "width": width, "color": 4},
        })

    connections = {}
    for a, b in zip(nodes, nodes[1:len(interactions)]):
        connections[a["name"]] = {"main": [[{"node": b["name"], "type": "main", "index": 0}]]}

    return {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "pinData": pin_data,
        "active": False,
        "settings": {},
    }


def _self_check():
    """ponytail: smallest thing that fails if the mapping breaks."""
    fake_trace = {
        "interactions": [
            {"actor": "Test", "action": "CALL", "target": "ScanApplicationService", "message": "go", "data": None},
            {"actor": "EventBus", "action": "RECEIVE", "target": "Test", "message": "Received ScanStarted",
             "data": {"event": "ScanStarted"}},
            {"actor": "Test", "action": "ASSERT", "target": "MotionPort", "message": "check", "data": None},
        ]
    }
    wf = build_workflow(fake_trace, "self-check")
    real_nodes = [n for n in wf["nodes"] if not n["id"].startswith("band_")]
    assert len(real_nodes) == 3
    assert real_nodes[0]["position"][1] == LAYER_Y["application"]
    assert real_nodes[1]["position"][1] == LAYER_Y["domain"]  # event surfaces to domain layer
    assert real_nodes[2]["position"][1] == LAYER_Y["infrastructure"]
    assert len(wf["connections"]) == 2  # chain of 3 nodes = 2 edges
    assert wf["pinData"][real_nodes[1]["name"]][0]["json"]["data"]["event"] == "ScanStarted"
    print("self-check OK")


if __name__ == "__main__":
    _self_check()

    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(0)

    trace_path, out_path = sys.argv[1], sys.argv[2]
    with open(trace_path, encoding="utf-8") as f:
        trace = json.load(f)

    workflow = build_workflow(trace, name=trace.get("test_name", "trace"))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"Wrote {out_path} ({len(workflow['nodes'])} nodes)")
