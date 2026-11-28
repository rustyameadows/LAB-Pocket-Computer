# Pocket Link v1

LAB Studio sends commands to the selected USB CDC endpoint. **Refresh** enumerates Linux serial device names and stable USB symlinks without opening them. **Connect** opens that one port, sets raw 921600 baud, 8 data bits, no parity and one stop bit, then requests the endpoint's identity. A board with a normal REPL or bootloader needs a Pocket Link service for this handshake. Choose **Virtual Pocket** to run an independent local endpoint for either panel size. Its game clock, framebuffer and key state live in a separate process.

## Frames and controls

Each request begins with a UTF-8 JSON object followed by LF. Replies echo the integer `id` and set `ok` to true or false. A `bytes` field specifies the number of binary bytes following the LF. The response body ends after exactly that count. One request is outstanding per session. The header limit is 8192 bytes.

| Command | Request fields | Reply |
| --- | --- | --- |
| `hello` | `protocol` = `LAB-Pocket-Link/1` | `info` object with protocol, name, model, firmware, physical width and height, logical_width and logical_height, and capabilities |
| `frame` | none | tick, running, title, score, status, keys, encoding and bytes, followed by the panel image |
| `play`, `pause`, `reset` | none | Acknowledgement. Reset returns the virtual cartridge to its opening frame and pauses. |
| `buttons` | `keys` array | Set the currently held keys. An empty array releases them. |
| `tap` | `key` | Inject press and release. The virtual peer advances two ticks, including while paused. |
| `load` | title, bytes, then UTF-8 source | Validate and select a cartridge in RAM. The virtual peer starts it paused. Source limit is 48 KiB. |

Example handshake and reply, each on one line:

```json
{"id":1,"cmd":"hello","protocol":"LAB-Pocket-Link/1"}
{"id":1,"ok":true,"info":{"protocol":"LAB-Pocket-Link/1","name":"Pocket 40","model":"LAB Pocket","firmware":"dev-1","width":720,"height":720,"logical_width":160,"logical_height":160,"capabilities":["mirror","control","input"]}}
```

Supported capability names are `mirror`, `control`, `input` and `load`. The board advertises the operations it implements. An operation failure returns a message such as `{"id":2,"ok":false,"error":"No cartridge selected"}` with no body. Input IDs are `key01` through `key20` or the named actions `up`, `down`, `left`, `right`, `a`, `b`, `start`, `select`. Each entry in the frame's `keys` object maps a lit switch to an RGB hex color.

Supported panel dimensions are 480 × 480 and 720 × 720. A frame is the **entire physical panel in row-major order**, including any native-resolution interface. The v0 game canvas is 160 × 160. The Virtual Pocket scales it before transmission at 3× or 4.5× using nearest-neighbor sampling. An application which renders natively can advertise its own logical dimensions. The host validates each image against the reported panel.

Formats:

- `png` carries one PNG image.
- `rgb565le` carries two little-endian bytes per pixel, with five red, six green and five blue bits.
- `rle565le` carries repeated pairs of unsigned little-endian 16-bit values, run length followed by RGB565 color. A run may span scanlines and counts from 1 to 65535. The expansion must fill the panel exactly.

The host pulls one frame per request. Raw 720 × 720 consumes 1,036,800 bytes per frame, so a UART bridge at 921600 baud can take over 11 seconds per raw frame. PNG, run-length encoding, or native USB CDC throughput determines the practical refresh rate. Each transfer has an idle deadline and a size-based total deadline. A malformed frame or vanished device ends the session and frees the port.

## Board integration

Copy `pocket_bridge.py` to the board and instantiate `PocketBridge(board)`. On a binary USB endpoint, call `bridge.serve_one(reader, writer)` after a request becomes readable. The native driver or firmware supplies blocking binary read/write streams, panel geometry and the board callbacks. Keep the game/display task running independently, or service requests inside an existing update loop. On cable removal, reset the bridge session and release injected keys in the board's input driver.

- `board.identity()` returns the `info` fields other than `protocol`.
- `board.frame()` returns `(telemetry, encoding, payload)`. Capture the active panel buffer, or encode the same frame passed to the display. For an RGB565 framebuffer with little-endian words, a `memoryview` of the existing buffer can be the payload. Hold that frame stable until the write completes. Telemetry includes integer tick, boolean running, cartridge title, score, gameplay status and light colors.
- `board.control(command)`, `board.buttons(keys)` and `board.tap(key)` act on the board's runtime. Physical keys and injected keys can be combined before the game update.
- `board.load(source, title)` validates a trusted cartridge against the target runtime and selects it. Advertise `load` when the firmware has a suitable RAM loader.

This release provides the service parser, host driver and a working reference peer. The Pocket board package must bind the callbacks to its specific USB, panel, and keypad drivers. The repository currently supplies the 160-pixel game renderer and physical panel designs.

## Serial fixture

For development with another serial client, run:

```sh
/usr/bin/python3 r3/virtual_pocket.py --pty --size 720
```

The peer prints one slave TTY path and serves the first client that connects. `--stdio` exposes the equivalent stream over standard input and output. The in-app virtual connection manages that process automatically. The test suite opens actual Linux pseudo-terminals to exercise the USB driver, binary framebuffer formats, timeouts and exclusive access.
