"""LAB Pocket Link v1 host transport. All I/O methods are synchronous."""
import fcntl
import io
import json
import os
from pathlib import Path
import re
import select
import socket
import struct
import subprocess
import sys
import termios
import time
import tty
from dataclasses import dataclass

from PIL import Image

PROTOCOL = "LAB-Pocket-Link/1"
PROFILE_SIZES = (480, 720)
MAX_HEADER = 8192
MAX_SOURCE = 48 * 1024
BAUD = 921600
BUTTONS = frozenset(["a", "b", "up", "down", "left", "right", "start", "select"] +
                    [f"key{i:02}" for i in range(1, 21)])
COLOR = re.compile(r"^#(?:[a-fA-F0-9]{3}|[a-fA-F0-9]{6})$")


class DeviceError(RuntimeError):
    """An unavailable endpoint, invalid response or rejected command."""


@dataclass(frozen=True)
class Endpoint:
    id: str
    name: str
    kind: str
    detail: str


@dataclass(frozen=True)
class Frame:
    image: Image.Image
    tick: int
    running: bool
    title: str
    score: int | float
    keys: dict
    status: str


def discover(dev=Path("/dev")):
    """List candidates without opening a port or toggling modem lines."""
    dev = Path(dev)
    endpoints = [Endpoint(f"virtual:{n}", f"Virtual Pocket · {n} × {n}", "virtual",
                          "Local peer with its own display and game runtime")
                 for n in PROFILE_SIZES]
    candidates = sorted((dev / "serial/by-id").glob("*"))
    candidates.extend(sorted(dev.glob("ttyACM*")) + sorted(dev.glob("ttyUSB*")))
    seen = set()
    for path in candidates:
        try:
            real = path.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if real in seen:
            continue
        seen.add(real)
        label = path.name.replace("usb-", "", 1) if path.is_symlink() else path.name
        endpoints.append(Endpoint(str(path), label, "usb", str(real)))
    return endpoints


def _uint(value, limit):
    return type(value) is int and 0 <= value <= limit


def _word(value, limit=160):
    return isinstance(value, str) and 0 < len(value) <= limit and value.isprintable()


class DeviceLink:
    """One serial or virtual session. Use on a single worker and close after errors."""
    def __init__(self, endpoint, fd, timeout, *, child=None, serial_settings=None):
        self.endpoint = endpoint
        self.fd = fd
        self.child = child
        self.serial_settings = serial_settings
        self.timeout = timeout
        self.seq = 0
        self.pending = bytearray()
        self.keys_held = False
        self.info = {}

    @classmethod
    def open(cls, endpoint, timeout=3.0):
        if endpoint.kind == "virtual":
            if endpoint.id not in {f"virtual:{n}" for n in PROFILE_SIZES}:
                raise DeviceError("Unknown Virtual Pocket profile.")
            path = Path(__file__).with_name("virtual_pocket.py")
            try:
                parent, peer = socket.socketpair()
                with parent, peer:
                    child = subprocess.Popen(
                        [sys.executable, "-B", "-u", str(path), "--stdio", "--size", endpoint.id.split(":")[1]],
                        stdin=peer, stdout=peer, stderr=subprocess.DEVNULL, close_fds=True)
                    fd = parent.detach()
            except OSError as exc:
                raise DeviceError(f"Could not start Virtual Pocket: {exc}") from exc
            link = cls(endpoint, fd, timeout, child=child)
        elif endpoint.kind == "usb":
            fd = None
            old = None
            try:
                fd = os.open(endpoint.id, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                old = termios.tcgetattr(fd)
                tty.setraw(fd, termios.TCSANOW)
                attr = termios.tcgetattr(fd)
                attr[2] = (attr[2] | termios.CLOCAL | termios.CREAD) & ~termios.HUPCL
                attr[4] = attr[5] = termios.B921600
                termios.tcsetattr(fd, termios.TCSANOW, attr)
                termios.tcflush(fd, termios.TCIFLUSH)
            except (OSError, termios.error) as exc:
                if fd is not None:
                    try:
                        if old is not None:
                            termios.tcsetattr(fd, termios.TCSANOW, old)
                    except (OSError, termios.error):
                        pass
                    finally:
                        os.close(fd)
                raise DeviceError(f"Could not open selected serial port {endpoint.id}: {exc}") from exc
            link = cls(endpoint, fd, timeout, serial_settings=old)
        else:
            raise DeviceError("Unsupported device connection.")
        try:
            os.set_blocking(link.fd, False)
            reply, _ = link._exchange("hello", {"protocol": PROTOCOL})
            info = reply.get("info")
            if not isinstance(info, dict) or info.get("protocol") != PROTOCOL:
                raise DeviceError("The selected endpoint does not speak LAB Pocket Link v1.")
            width, height = info.get("width"), info.get("height")
            if not _uint(width, 720) or width not in PROFILE_SIZES or type(height) is not int or width != height:
                raise DeviceError("The endpoint must advertise a 480 × 480 or 720 × 720 panel.")
            caps = info.get("capabilities")
            if (not isinstance(caps, list) or len(caps) > 32 or not all(_word(s, 32) for s in caps)
                    or not all(_word(info.get(k)) for k in ("name", "model", "firmware"))):
                raise DeviceError("The endpoint returned incomplete identity or capabilities.")
            for key in ("logical_width", "logical_height"):
                value = info.get(key, width)
                if not _uint(value, width) or not value:
                    raise DeviceError("The endpoint returned an invalid logical resolution.")
                info[key] = value
            link.info = info
            return link
        except Exception:
            link.close()
            raise

    def _wait(self, writing, deadline):
        remaining = min(deadline - time.monotonic(), self.timeout)
        if remaining <= 0:
            raise DeviceError("Pocket Link timed out.")
        readable, writable, _ = select.select(
            [] if writing else [self.fd], [self.fd] if writing else [], [], remaining)
        if not (readable or writable):
            raise DeviceError("Pocket Link timed out. Check the connection and device bridge.")

    def _write(self, data, deadline):
        view = memoryview(data)
        while view:
            self._wait(True, deadline)
            try:
                count = os.write(self.fd, view)
            except BlockingIOError:
                continue
            if not count:
                raise DeviceError("Pocket disconnected while sending.")
            view = view[count:]

    def _receive(self, deadline):
        while True:
            self._wait(False, deadline)
            try:
                data = os.read(self.fd, 65536)
            except BlockingIOError:
                continue
            if not data:
                raise DeviceError("Pocket disconnected.")
            self.pending.extend(data)
            return

    def _exchange(self, command, fields=None, body=b""):
        if self.fd is None:
            raise DeviceError("Pocket disconnected.")
        self.seq += 1
        header = {"id": self.seq, "cmd": command, **(fields or {})}
        if body:
            header["bytes"] = len(body)
        encoded = json.dumps(header, separators=(",", ":")).encode() + b"\n"
        deadline = time.monotonic() + self.timeout + len(body) / (BAUD / 12)
        try:
            self._write(encoded, deadline)
            if body:
                self._write(body, deadline)
            while b"\n" not in self.pending:
                if len(self.pending) >= MAX_HEADER:
                    raise DeviceError("Device response header is too large.")
                self._receive(deadline)
            end = self.pending.index(b"\n")
            if end > MAX_HEADER:
                raise DeviceError("Device response header is too large.")
            result = json.loads(bytes(self.pending[:end]).decode("utf-8"))
            del self.pending[:end + 1]
            if (not isinstance(result, dict) or type(result.get("id")) is not int
                    or result["id"] != self.seq or type(result.get("ok")) is not bool):
                raise DeviceError("Pocket Link response did not match its request.")
            count = result.get("bytes", 0)
            max_frame = 4 * self.info.get("width", 0) * self.info.get("height", 0)
            if not _uint(count, max_frame if command == "frame" and result["ok"] else 0):
                raise DeviceError("Pocket Link returned an invalid payload length.")
            deadline = time.monotonic() + self.timeout + count / (BAUD / 12)
            while len(self.pending) < count:
                self._receive(deadline)
            payload = bytes(self.pending[:count])
            del self.pending[:count]
        except (OSError, ValueError, RecursionError, DeviceError) as exc:
            self._release()
            if isinstance(exc, DeviceError):
                raise
            raise DeviceError(f"Pocket Link communication failed: {exc}") from exc
        if not result["ok"]:
            raise DeviceError(str(result.get("error", "The endpoint rejected the command."))[:300])
        return result, payload

    def _require(self, capability):
        if capability not in self.info.get("capabilities", []):
            raise DeviceError(f"This endpoint does not advertise {capability}.")

    def control(self, command):
        self._require("control")
        if command not in ("play", "pause", "reset"):
            raise DeviceError("Unknown transport control.")
        self._exchange(command)

    def buttons(self, buttons):
        self._require("input")
        if not isinstance(buttons, (tuple, list, set)) or not all(k in BUTTONS for k in buttons):
            raise DeviceError("Unknown Pocket key.")
        self._exchange("buttons", {"keys": sorted(set(buttons))})
        self.keys_held = bool(buttons)

    def tap(self, button):
        self._require("input")
        if button not in BUTTONS:
            raise DeviceError("Unknown Pocket key.")
        self._exchange("tap", {"key": button})

    def load(self, source, title):
        self._require("load")
        if not _word(title, 80) or not isinstance(source, str):
            raise DeviceError("Provide a game title and source.")
        data = source.encode("utf-8")
        if not 0 < len(data) <= MAX_SOURCE:
            raise DeviceError("Game source must fit in 48 KiB.")
        self._exchange("load", {"title": title}, data)

    def frame(self):
        self._require("mirror")
        meta, data = self._exchange("frame")
        size = (self.info["width"], self.info["height"])
        try:
            if (not _uint(meta.get("tick"), 2**63-1) or type(meta.get("running")) is not bool
                    or not _word(meta.get("title")) or not _word(meta.get("status", "Ready"))
                    or type(meta.get("score", 0)) not in (int, float)):
                raise ValueError("invalid frame telemetry")
            keys = meta.get("keys", {})
            if not isinstance(keys, dict) or len(keys) > 20 or not all(
                k in BUTTONS and isinstance(v, str) and COLOR.fullmatch(v) for k, v in keys.items()
            ):
                raise ValueError("invalid frame LEDs")
            encoding = meta.get("encoding")
            if encoding == "png":
                with Image.open(io.BytesIO(data), formats=["PNG"]) as img:
                    if img.size != size:
                        raise ValueError("frame differs from the negotiated panel size")
                    image = img.convert("RGB")
            elif encoding in ("rgb565le", "rle565le"):
                raw = data if encoding == "rgb565le" else _expand_rle(data, size[0]*size[1])
                if len(raw) != size[0]*size[1]*2:
                    raise ValueError("wrong RGB565 framebuffer length")
                image = Image.frombytes("RGB", size, raw, "raw", "BGR;16")
            else:
                raise ValueError("unsupported framebuffer encoding")
            return Frame(image, meta["tick"], meta["running"], meta["title"], meta.get("score", 0),
                         keys, meta.get("status", "Ready"))
        except (ValueError, OSError, Image.DecompressionBombError, SyntaxError, struct.error) as exc:
            self._release()
            raise DeviceError(f"Invalid device frame: {exc}") from exc

    def close(self):
        if self.fd is not None and self.keys_held:
            try:
                self.buttons([])
            except DeviceError:
                pass
        self._release()

    def _release(self):
        self.keys_held = False
        fd, self.fd = self.fd, None
        if fd is not None:
            if self.serial_settings is not None:
                try:
                    termios.tcsetattr(fd, termios.TCSANOW, self.serial_settings)
                except (OSError, termios.error):
                    pass
            os.close(fd)
        if self.child is not None:
            try:
                self.child.wait(timeout=.5)
            except subprocess.TimeoutExpired:
                self.child.terminate()
                try:
                    self.child.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    self.child.kill()
                    self.child.wait()
            self.child = None


def _expand_rle(payload, pixels):
    result = bytearray()
    for length, color in struct.iter_unpack("<H2s", payload):
        if not length or len(result) + length*2 > pixels*2:
            raise ValueError("invalid RGB565 run length")
        result.extend(color * length)
    return result
