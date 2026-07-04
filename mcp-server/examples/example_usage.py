#!/usr/bin/env python3
"""Example: talk to the OpenTryOn MCP server programmatically with the
FastMCP client, without going through Claude Desktop / Cursor.

Run from the ``mcp-server`` directory:

    python examples/example_usage.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from fastmcp import Client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main() -> None:
    # Connecting with the server module path spawns `server.py` as a
    # subprocess over stdio -- the same way Claude Desktop/Cursor do it.
    server_path = Path(__file__).resolve().parent.parent / "server.py"

    async with Client(str(server_path)) as client:
        # 1. Discover what's available and what's configured.
        status = await client.call_tool("opentryon_status", {})
        print("=== opentryon_status ===")
        print(status.data)

        tools = await client.list_tools()
        print(f"\n{len(tools)} tools available, e.g.:")
        for t in tools[:5]:
            print(f"  - {t.name}: {t.description.splitlines()[0]}")

        # 2. Preview a call with dry_run=True (no API credits spent).
        print("\n=== vton_flux_vto (dry_run) ===")
        result = await client.call_tool(
            "vton_flux_vto",
            {
                "person": "https://example.com/model.jpg",
                "garment": "https://example.com/garment.jpg",
                "dry_run": True,
            },
        )
        print(json.dumps(result.data, indent=2))

        # 3. A real call (requires MOONSHOT_API_KEY in the repo's .env).
        print("\n=== understand_kimi_k2_6 (dry_run) ===")
        result = await client.call_tool(
            "understand_kimi_k2_6",
            {
                "image": "https://example.com/outfit.jpg",
                "prompt": "Describe this outfit in detail.",
                "dry_run": True,
            },
        )
        print(json.dumps(result.data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
