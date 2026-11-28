#!/usr/bin/python3
"""LAB Studio MCP server. Run as a stdio subprocess with /usr/bin/python3."""

import base64
from io import BytesIO
import json
import sqlite3
import sys

from studio_store import ACTIONS, MAX_SOURCE_BYTES, Store, StoreError, check_source_text

VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
MAX_PLAYTEST_FRAMES = 600


def obj(properties=None, required=()):
    schema = {"type": "object", "properties": properties or {}, "additionalProperties": False}
    if required:
        schema["required"] = list(required)
    return schema


def tool(name, description, schema, *, read_only=True, destructive=False):
    return {
        "name": name, "description": description, "inputSchema": schema,
        "annotations": {"readOnlyHint": read_only, "destructiveHint": destructive,
                        "openWorldHint": False},
    }


IDENTIFIER = {"type": "string", "description": "Project id from lab_list_projects or lab_create_project."}
TITLE = {"type": "string", "minLength": 1, "maxLength": 80}
DESCRIPTION = {"type": "string", "maxLength": 1000}
SOURCE = {"type": "string", "maxLength": MAX_SOURCE_BYTES, "description": "Complete editable main.py."}
CONTROLS = {"type": "object", "propertyNames": {"enum": sorted(ACTIONS)},
            "additionalProperties": {"type": "string", "maxLength": 160}}
BUTTONS = {"type": "array", "items": {"type": "string", "enum": sorted(ACTIONS)},
           "uniqueItems": True}
SEGMENT = obj({"frames": {"type": "integer", "minimum": 1, "maximum": MAX_PLAYTEST_FRAMES},
               "buttons": BUTTONS}, ["frames"])
TOOLS = {
    item["name"]: item for item in [
        tool("lab_info", "Get LAB v0 game API, sample templates, action names, and the Studio workflow.", obj()),
        tool("lab_list_projects", "List local Studio games with their revision and active selection.", obj()),
        tool("lab_read_project", "Read a game's complete editable main.py, revision, controls and title.",
             obj({"project_id": IDENTIFIER}, ["project_id"])),
        tool("lab_create_project", "Create and select a new cartridge. For an original or customized game, "
             "pass the complete authored source when creating it. Use lab_read_project on a sample ID "
             "to get starter code. Omitting source copies the template verbatim. Each call creates one project.",
             obj({"title": TITLE, "template": {"type": "string", "default": "falling-blocks"},
                  "description": DESCRIPTION, "source": SOURCE, "controls": CONTROLS}, ["title"]), read_only=False),
        tool("lab_update_project", "Replace main.py after a validation tick, optionally editing the game's "
             "title, description or controls. Supply the revision you read to avoid overwriting newer work.",
             obj({"project_id": IDENTIFIER, "expected_revision": {"type": "integer", "minimum": 1},
                  "source": SOURCE, "title": TITLE,
                  "description": DESCRIPTION, "controls": CONTROLS},
                 ["project_id", "source", "expected_revision"]), read_only=False, destructive=True),
        tool("lab_open_project", "Select a game in the local Studio workspace. An open Studio window "
             "observes this selection, with unsaved editor drafts protected.",
             obj({"project_id": IDENTIFIER}, ["project_id"]), read_only=False),
        tool("lab_playtest", "Preview exactly one saved project_id or unsaved source. Hold the named "
             "buttons for each segment, in order, up to 600 ticks total at 30 Hz. Use an empty buttons "
             "array to release. Returns game state and an actual 160×160 PNG. Independent of live GUI play.",
             obj({"project_id": IDENTIFIER, "source": SOURCE, "seed": {"type": "integer", "minimum": 0,
                  "maximum": 2147483647, "default": 1},
                  "steps": {"type": "array", "items": SEGMENT, "maxItems": 120}})),
        tool("lab_export_project", "Export a saved revision as a .lab ZIP with manifest.json and "
             "main.py for the Studio v0 format. Returns the local artifact path.",
             obj({"project_id": IDENTIFIER}, ["project_id"]), read_only=False),
    ]
}


def summary(project):
    return {key: value for key, value in project.items() if key != "source"}


def json_content(data):
    return {"type": "text", "text": json.dumps(data, ensure_ascii=False)}


def segments(steps):
    if not isinstance(steps, list) or len(steps) > 120:
        raise StoreError("steps must be an array of up to 120 input segments.")
    total = 0
    for item in steps:
        if not isinstance(item, dict) or set(item) - {"buttons", "frames"}:
            raise StoreError("Each segment must contain frames and may contain buttons.")
        frames = item.get("frames")
        if type(frames) is not int or frames < 1:
            raise StoreError("Segment frame count must be a positive integer.")
        total += frames
        if total > MAX_PLAYTEST_FRAMES:
            raise StoreError(f"A playtest supports up to {MAX_PLAYTEST_FRAMES} ticks.")
        buttons = item.get("buttons", [])
        if (not isinstance(buttons, list) or len(buttons) > len(ACTIONS)
                or any(not isinstance(button, str) or button not in ACTIONS for button in buttons)
                or len(set(buttons)) != len(buttons)):
            raise StoreError("Use unique button names from lab_info.actions.")
        yield frames, buttons


def playtest(store, project_id=None, seed=1, steps=None, source=None):
    from engine import Game
    if type(seed) is not int or not 0 <= seed <= 2147483647:
        raise StoreError("seed must be an integer between 0 and 2147483647.")
    script = list(segments([] if steps is None else steps))
    if (source is None) == (project_id is None):
        raise StoreError("Provide exactly one of project_id or source.")
    revision = None
    if project_id is not None:
        project = store.get_project(project_id)
        source, revision = project["source"], project["revision"]
    else:
        check_source_text(source)
    game = Game(source, seed=seed)
    for frames, buttons in script:
        for _ in range(frames):
            game.step(buttons)
    png = BytesIO()
    game.image().save(png, format="PNG")
    metadata = {"project_id": project_id, "revision": revision, "seed": seed,
                "frames": sum(frames for frames, _ in script), "state": game.inspect()}
    return [json_content(metadata),
            {"type": "image", "mimeType": "image/png", "data": base64.b64encode(png.getvalue()).decode("ascii")}]


def dispatch(store, name, args):
    schema = TOOLS[name]["inputSchema"]
    if not isinstance(args, dict):
        raise StoreError("Tool arguments must be an object.")
    missing = sorted(set(schema.get("required", [])) - set(args))
    extra = sorted(set(args) - set(schema["properties"]))
    if missing:
        raise StoreError("Missing required arguments: " + ", ".join(missing))
    if extra:
        raise StoreError("Unknown arguments: " + ", ".join(extra))
    for key, value in args.items():
        kind = schema["properties"][key]["type"]
        types = {"string": str, "integer": int, "array": list, "object": dict}
        if type(value) is not types[kind]:
            raise StoreError(f"{key} must have JSON type {kind}.")
    if name == "lab_info":
        from engine import API_DOC
        data = {
            "runtime": "lab-python-v0", "display": [160, 160], "ticks_per_second": 30,
            "api": API_DOC, "actions": sorted(ACTIONS), "templates": store.list_templates(),
            "workflow": ["lab_read_project", "lab_create_project", "lab_playtest",
                         "lab_open_project", "lab_export_project"],
            "new_game": "Read a starter using its template id, write the requested mechanics, and pass "
                        "the full source to lab_create_project. Optionally use lab_playtest(source=...) "
                        "to iterate privately before creating. Test the saved project by id.",
            "exports": "Portable Studio v0 preview packages. Hardware deployment requires compatible Pocket firmware.",
        }
    elif name == "lab_list_projects":
        data = {"active_id": store.get_active(), "projects": store.list_projects()}
    elif name == "lab_read_project":
        data = store.get_project(args["project_id"])
    elif name == "lab_create_project":
        data = summary(store.create_project(**args))
    elif name == "lab_update_project":
        data = summary(store.update_project(**args))
    elif name == "lab_open_project":
        store.set_active(args["project_id"])
        data = {"active_id": args["project_id"]}
    elif name == "lab_playtest":
        return playtest(store, **args)
    elif name == "lab_export_project":
        path = store.export_project(args["project_id"])
        data = {"project_id": args["project_id"], "path": str(path), "uri": path.as_uri()}
    return [json_content(data)]


def error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


class Server:
    def __init__(self):
        self.initialized = False
        self.store = None

    def receive(self, message):
        if (not isinstance(message, dict) or message.get("jsonrpc") != "2.0"
                or not isinstance(message.get("method"), str)):
            return error(None, -32600, "Invalid JSON-RPC request.")
        if "id" not in message:
            return None
        request_id = message["id"]
        if type(request_id) not in (int, str):
            return error(None, -32600, "Request id must be a string or integer.")
        method = message["method"]
        params = message.get("params", {})
        if not isinstance(params, dict):
            return error(request_id, -32602, "Parameters must be an object.")
        if method == "initialize":
            requested = params.get("protocolVersion")
            if not isinstance(requested, str):
                return error(request_id, -32602, "Missing protocolVersion.")
            self.initialized = True
            result = {
                "protocolVersion": requested if requested in VERSIONS else VERSIONS[0],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "lab-studio", "version": "0.1.0"},
                "instructions": "Use lab_info to discover the LAB Pocket game API and templates. "
                                "For a new game, read a starter, author the requested rules, then send the "
                                "finished source to lab_create_project in a single call. Playtest, open and export.",
            }
        elif method == "ping":
            result = {}
        elif not self.initialized:
            return error(request_id, -32002, "Initialize the MCP connection first.")
        elif method == "tools/list":
            result = {"tools": list(TOOLS.values())}
        elif method == "tools/call":
            name = params.get("name")
            if not isinstance(name, str) or name not in TOOLS:
                return error(request_id, -32602, "Unknown LAB tool. Call tools/list.")
            try:
                if self.store is None:
                    self.store = Store()
                result = {"content": dispatch(self.store, name, params.get("arguments", {}))}
            except (ValueError, OSError, sqlite3.Error, UnicodeError) as exc:
                result = {"isError": True, "content": [{"type": "text", "text": str(exc)}]}
            except Exception as exc:
                print(f"LAB tool {name} failed: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
                return error(request_id, -32603, "Internal LAB Studio error. See server stderr.")
        else:
            return error(request_id, -32601, "Method not found.")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main():
    server = Server()
    for line in sys.stdin.buffer:
        try:
            request = json.loads(line.decode("utf-8"))
            response = server.receive(request)
        except (ValueError, RecursionError):
            response = error(None, -32700, "Invalid JSON.")
        if response is not None:
            output = (json.dumps(response, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")
            sys.stdout.buffer.write(output)
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
