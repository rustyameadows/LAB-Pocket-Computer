"""Add physical panel previews to the existing Studio MCP contract."""
import base64
import json
import sys
from copy import deepcopy
from io import BytesIO
from PIL import Image
import lab_mcp
from .panels import PANELS, render_panel


class PanelServer:
    def __init__(self):
        self.server = lab_mcp.Server()

    def receive(self, request):
        params = request.get("params") if isinstance(request, dict) else None
        tool = params.get("name") if isinstance(params, dict) else None
        args = params.get("arguments") if isinstance(params, dict) else None
        method = request.get("method") if isinstance(request, dict) else None
        panel = None
        if method == "tools/call" and tool == "lab_playtest" and isinstance(args, dict) and "panel" in args:
            panel = args["panel"]
            if type(panel) is not int or panel not in PANELS:
                if not self.server.initialized or "id" not in request:
                    return self.server.receive(request)
                return {"jsonrpc": "2.0", "id": request["id"], "result": {"isError": True, "content": [
                    {"type": "text", "text": "Choose a physical panel width of 480 or 720."}]}}
            filtered = {key: value for key, value in args.items() if key != "panel"}
            request = {**request, "params": {**params, "arguments": filtered}}
        reply = self.server.receive(request)
        if not reply or "result" not in reply or reply["result"].get("isError"):
            return reply
        result = reply["result"]
        if method == "initialize":
            result["serverInfo"]["version"] = "0.3.0"
            result["instructions"] += " Pocket panels are 480×480 or 720×720; cartridges draw on a 160×160 logical canvas."
        elif method == "tools/list":
            result["tools"] = deepcopy(result["tools"])
            play = next(t for t in result["tools"] if t["name"] == "lab_playtest")
            play["description"] += " Pass panel=480 or 720 to return a physical-panel preview PNG."
            play["inputSchema"]["properties"]["panel"] = {"type": "integer", "enum": PANELS,
                                                          "description": "Physical square panel width in pixels."}
        elif method == "tools/call" and tool == "lab_info":
            desc = json.loads(result["content"][0]["text"])
            desc.update(logical_canvas=[160, 160], panel_sizes=[[size, size] for size in PANELS])
            result["content"][0] = lab_mcp.json_content(desc)
        elif method == "tools/call" and tool == "lab_playtest" and panel:
            state, frame = result["content"]
            with Image.open(BytesIO(base64.b64decode(frame["data"]))) as image:
                output = BytesIO()
                render_panel(image, panel).save(output, format="PNG")
            meta = json.loads(state["text"])
            meta.update(logical_canvas=[160, 160], panel_size=[panel, panel])
            result["content"] = [lab_mcp.json_content(meta), {**frame, "data": base64.b64encode(output.getvalue()).decode("ascii")}]
        return reply


def main():
    server = PanelServer()
    for line in sys.stdin.buffer:
        try:
            reply = server.receive(json.loads(line))
        except (ValueError, RecursionError, UnicodeError):
            reply = lab_mcp.error(None, -32700, "Invalid JSON.")
        if reply is not None:
            print(json.dumps(reply, ensure_ascii=True, separators=(",", ":")), flush=True)
