"""Default bindings for the twenty numbered Pocket switches (row-major, 5 × 4)."""
BOARD = {
    2: "up", 4: "select", 5: "start",
    6: "left", 7: "down", 8: "right", 9: "b", 10: "a",
}
_PAIRS = tuple(("key%02d" % number, action) for number, action in BOARD.items())


def expand_buttons(buttons):
    """Expose both the physical switch and its bound action during a tick."""
    result = set(buttons)
    for number, action in _PAIRS:
        if number in result or action in result:
            result.add(number)
            result.add(action)
    return result
