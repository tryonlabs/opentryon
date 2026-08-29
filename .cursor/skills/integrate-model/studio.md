# TryOn Studio after a model lands in OpenTryOn

Studio must not import OpenTryOn Python, share its filesystem, or grow a second adapter stack. New models belong in `opentryon/tryon/cli/registry.py`; they appear here after **MCP restart**.

Repo: sibling `tryon-studio`. Contract: `tryon-studio/AGENTS.md`. Visual system: `tryon-studio/.cursor/rules/design-system.mdc`.

## What usually needs zero UI code

Capability screens (`CapabilityStudio` + `DynamicForm` + `OutputViewer`) build the model picker from live MCP (`list_opentryon_tools` → catalog). Do **not** fork a per-service playground or hardcode an allowlist.

After OpenTryOn registry + MCP restart:

1. Restart the MCP process (`http://127.0.0.1:8000/mcp`). Address-in-use → kill the old PID.
2. Studio Connect refresh or `/api/mcp/status?reconnect=1` (stale MCP session can 502).
3. Confirm the new id on the matching capability (Image / VTON / Understand / Video / BG Remove).

## When Studio *does* need a change

| Situation | What to touch |
|---|---|
| New provider **key** | OpenTryOn `mcp-server/config.py` catalog (label, docs URL, notes). Studio Connect search uses that payload. Optional: deep-link `/connect?key=THAT_KEY`. |
| Planner name collision | OpenTryOn `tryon/agents/planner/bind.py` (not a Studio router). Chat is `planner_agent` only. |
| Schema/UX edge | Prefer fixing registry `Arg`s (choices, dest, booleans) so `DynamicForm` is correct. Understand `video` stays a **URL** field. |
| Copy / IA | Keep nav: Agent · Capabilities · Connect. Do not add use-case screens to nav. |

Keys: Connect is a **passthrough**. `list_api_keys` / `set_api_keys` write `opentryon/.env`. Studio does not store secrets.

Media on the wire: `images_base64` / `video_base64`, not MCP-host paths. Client components must not import `src/lib/mcp/catalog.ts`; use `/api/mcp/catalog`.

## Visual / verification

Reuse existing capability chrome. Brand coral/navy from tryon-web; Studio surfaces stay compact inset fields, left-accent errors, warm stone / lifted dark panels.

If you change Studio UI, verify in the browser (capability picker, Connect key save, Agent chat naming the new model). Dry-run stays the form default.
