#!/usr/bin/env python3
"""MCP server for switchyard - Feature Flag Control Plane Wrapper"""

import json
import os
from datetime import datetime
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("mcp-switchyard")

# Simulated data
FLAGS = {
    "new-ui": {
        "id": "new-ui",
        "key": "new-ui",
        "name": "New UI",
        "description": "Enable new UI",
        "project_id": "myapp",
        "flag_type": "boolean",
        "default_value": False,
        "targeting_rules": [
            {"attribute": "country", "operator": "in", "values": ["US", "CA"], "rollout": 100},
            {"attribute": "user_tier", "operator": "in", "values": ["premium"], "rollout": 100},
            {"attribute": "random", "operator": "percentage", "value": 10}
        ],
        "status": "active",
        "created_at": "2024-11-01T10:00:00",
        "updated_at": "2024-12-01T10:00:00"
    },
    "dark-mode": {
        "id": "dark-mode",
        "key": "dark-mode",
        "name": "Dark Mode",
        "description": "Enable dark mode",
        "project_id": "myapp",
        "flag_type": "boolean",
        "default_value": True,
        "targeting_rules": [],
        "status": "active",
        "created_at": "2024-10-15T10:00:00",
        "updated_at": "2024-11-01T10:00:00"
    },
    "new-api-v2": {
        "id": "new-api-v2",
        "key": "new-api-v2",
        "name": "New API v2",
        "description": "Rollout new API version",
        "project_id": "myapp",
        "flag_type": "string",
        "default_value": "v1",
        "targeting_rules": [
            {"attribute": "api_version", "operator": "in", "values": ["beta"], "rollout": 100}
        ],
        "status": "active",
        "created_at": "2024-11-15T10:00:00",
        "updated_at": "2024-12-01T10:00:00"
    }
}

ROLLOUTS = {
    "rollout-001": {
        "id": "rollout-001",
        "flag_id": "new-ui",
        "name": "New UI Gradual Rollout",
        "stages": [
            {"stage": 1, "percentage": 5, "duration_days": 7, "criteria": "error_rate < 0.1%"},
            {"stage": 2, "percentage": 25, "duration_days": 14, "criteria": "error_rate < 0.1%"},
            {"stage": 3, "percentage": 50, "duration_days": 14, "criteria": "error_rate < 0.1%"},
            {"stage": 4, "percentage": 100, "duration_days": 7, "criteria": "error_rate < 0.1%"}
        ],
        "current_stage": 2,
        "status": "active",
        "started_at": "2024-12-01T10:00:00",
        "completed_at": None
    }
}

app = Server("mcp-switchyard")

TOOLS = [
    Tool(
        name="list_flags",
        description="List feature flags for a project",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"}
            }
        }
    ),
    Tool(
        name="toggle_flag",
        description="Toggle a feature flag on/off",
        inputSchema={
            "type": "object",
            "properties": {
                "flag_id": {"type": "string", "description": "Flag ID"},
                "enabled": {"type": "boolean", "description": "Enable or disable the flag"}
            },
            "required": ["flag_id", "enabled"]
        }
    ),
    Tool(
        name="get_rollout_status",
        description="Get rollout status for a flag",
        inputSchema={
            "type": "object",
            "properties": {
                "flag_id": {"type": "string", "description": "Flag ID"}
            },
            "required": ["flag_id"]
        }
    ),
    Tool(
        name="get_strategy_report",
        description="Get feature flag strategy report",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"}
            }
        }
    )
]

app = Server("mcp-switchyard")

@app.list_tools()
async def list_tools():
    return TOOLS

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "list_flags":
        project_id = arguments.get("project_id")
        
        flags = []
        for fid, flag in FLAGS.items():
            if project_id is None or flag["project_id"] == project_id:
                flags.append(flag)
        
        result = {
            "status": "ok",
            "tool": "list_flags",
            "project_id": project_id,
            "count": len(flags),
            "flags": flags
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "toggle_flag":
        flag_id = arguments.get("flag_id")
        enabled = arguments.get("enabled")
        
        if flag_id not in FLAGS:
            return [TextContent(type="text", text=json.dumps({"error": f"Flag not found: {flag_id}"}))]
        
        FLAGS[flag_id]["status"] = "active" if enabled else "archived"
        FLAGS[flag_id]["updated_at"] = datetime.now().isoformat()
        
        result = {
            "status": "ok",
            "tool": "toggle_flag",
            "flag_id": flag_id,
            "enabled": enabled,
            "message": f"Flag {flag_id} {'enabled' if enabled else 'disabled'}"
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_rollout_status":
        flag_id = arguments.get("flag_id")
        
        rollout = None
        for rid, rollout in ROLLOUTS.items():
            if rollout["flag_id"] == flag_id:
                rollout = rollout
                break
        
        if not rollout:
            return [TextContent(type="text", text=json.dumps({"error": f"No rollout found for flag: {flag_id}"}))]
        
        current_stage = rollout["stages"][rollout["current_stage"] - 1] if rollout["current_stage"] > 0 else None
        
        result = {
            "status": "ok",
            "tool": "get_rollout_status",
            "flag_id": flag_id,
            "rollout": {
                "id": rollout["id"],
                "name": rollout["name"],
                "current_stage": rollout["current_stage"],
                "total_stages": len(rollout["stages"]),
                "status": rollout["status"],
                "current_stage_details": current_stage,
                "started_at": rollout["started_at"],
                "progress_percentage": round((rollout["current_stage"] / len(rollout["stages"])) * 100, 1)
            }
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    elif name == "get_strategy_report":
        project_id = arguments.get("project_id")
        
        flags = [f for f in FLAGS.values() if f["project_id"] == project_id] if project_id else list(FLAGS.values())
        
        total = len(flags)
        active = len([f for f in flags if f["status"] == "active"])
        archived = len([f for f in flags if f["status"] == "archived"])
        
        rollouts = [r for r in ROLLOUTS.values() if r["flag_id"] in [f["id"] for f in flags]]
        active_rollouts = len([r for r in rollouts if r["status"] == "active"])
        
        result = {
            "status": "ok",
            "tool": "get_strategy_report",
            "project_id": project_id,
            "summary": {
                "total_flags": total,
                "active": active,
                "archived": archived,
                "active_rollouts": sum(1 for r in ROLLOUTS.values() if r["status"] == "active" and r["flag_id"] in [f["id"] for f in flags]),
                "total_rollouts": len([r for r in ROLLOUTS.values() if r["flag_id"] in [f["id"] for f in flags]])
            },
            "flags": flags,
            "rollouts": list(ROLLOUTS.values())
        }
        return [TextContent(type="text", text=json.dumps(result))]
    
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def serve():
        reader, writer = await stdio_server()
        await app.run(reader, writer)
    
    asyncio.run(serve())