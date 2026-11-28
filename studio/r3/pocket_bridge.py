"""Pocket Link v1 board adapter. Standard Python and MicroPython compatible.

Supply a blocking binary USB stream and a board object implementing the callbacks
in DEVICE-LINK-r3.md. Call serve_one after a request is available. The board
owns the actual display, game clock and physical keys.
"""
import json

PROTOCOL = "LAB-Pocket-Link/1"
MAX_HEADER = 8192
MAX_SOURCE = 48 * 1024


def _header(reader):
    buf = bytearray()
    while len(buf) <= MAX_HEADER:
        c = reader.read(1)
        if not c:
            if buf:
                raise OSError("Disconnected during header")
            return None
        if c == b"\n":
            return json.loads(buf.decode("utf-8"))
        buf.extend(c)
    raise ValueError("Header exceeds limit")


def _body(reader, count):
    data = bytearray()
    while len(data) < count:
        chunk = reader.read(min(4096, count - len(data)))
        if not chunk:
            raise OSError("Disconnected during body")
        data.extend(chunk)
    return data


def _write(writer, payload):
    data = memoryview(payload)
    while len(data):
        n = writer.write(data[:4096])
        if not n:
            raise OSError("Disconnected during write")
        data = data[n:]


class PocketBridge:
    def __init__(self, board):
        self.board = board
        self.info = None

    def serve_one(self, reader, writer):
        """Handle one complete request. Returns False at clean EOF."""
        req = _header(reader)
        if req is None:
            return False
        if not isinstance(req, dict) or type(req.get("id")) is not int:
            raise ValueError("Invalid request header")
        cmd = req.get("cmd")
        n = req.get("bytes", 0)
        # Unbounded or unexpected bodies make the stream impossible to resync.
        if type(n) is not int or n < 0 or n > MAX_SOURCE or (n and cmd != "load"):
            raise ValueError("Invalid request body length")
        data = _body(reader, n) if n else b""
        reply = {"id": req["id"], "ok": True}
        outgoing = b""
        try:
            if cmd == "hello":
                if req.get("protocol") != PROTOCOL:
                    raise ValueError("Unsupported protocol")
                info = dict(self.board.identity())
                info["protocol"] = PROTOCOL
                self.info = info
                reply["info"] = info
            elif not self.info:
                raise ValueError("Request hello first")
            else:
                caps = self.info["capabilities"]
                if cmd == "frame" and "mirror" in caps:
                    telemetry, encoding, outgoing = self.board.frame()
                    for field in ("tick", "running", "title", "score", "keys", "status"):
                        if field in telemetry:
                            reply[field] = telemetry[field]
                    reply["encoding"] = encoding
                    reply["bytes"] = len(outgoing)
                elif cmd in ("play", "pause", "reset") and "control" in caps:
                    self.board.control(cmd)
                elif cmd == "buttons" and "input" in caps:
                    self.board.buttons(req["keys"])
                elif cmd == "tap" and "input" in caps:
                    self.board.tap(req["key"])
                elif cmd == "load" and "load" in caps:
                    if not n:
                        raise ValueError("Empty source")
                    self.board.load(data.decode("utf-8"), req["title"])
                else:
                    raise ValueError("Unsupported command or capability")
        except (ValueError, KeyError, TypeError, RuntimeError, OSError) as exc:
            reply = {"id": req["id"], "ok": False, "error": str(exc)[:280] or "Board rejected command"}
            outgoing = b""
        _write(writer, (json.dumps(reply) + "\n").encode("utf-8"))
        if outgoing:
            _write(writer, outgoing)
        if hasattr(writer, "flush"):
            writer.flush()
        return True
