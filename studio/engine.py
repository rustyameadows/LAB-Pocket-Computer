"""LAB Studio's deterministic desktop interpreter for portable Pocket game scripts."""
import ast
import math
import operator
from functools import lru_cache

from PIL import Image, ImageDraw

from pixel_font import GLYPHS
from pocket_keys import expand_buttons


API_DOC = """LAB game API v0. Canvas 160x160, origin top left. 30 fixed ticks/second.
Define init(), update(), draw(). Ordinary Python helper functions are supported. No imports.
Store persistent data in the shared state dictionary, e.g. state["x"] = 80 in init().
Use state["score"] (integer) and state["status"] (short text) for Studio's inspector.
tick is 0 for init/first draw and increases by one before each update/draw.
held("left") is true while held. pressed("a") is true on the first tick of a press.
Actions: left/right/up/down/a/b/start/select or physical key01 through key20.
rand(lo,hi) returns a seeded inclusive integer. led(1,"#ffc05a") sets key 1's light.
In draw(): clear(color), pixel(x,y,color), rect(x,y,width,height,color),
line(x1,y1,x2,y2,color), text(x,y,value,color,scale=1). Colors use #RGB or #RRGGBB.
Text is a 3x5-pixel uppercase font with 4-pixel advance; scale is an integer 1..8.
Use integer or float arithmetic, comparisons, if/elif/else, for/while, break/continue,
local variables, functions, tuples/lists/dicts, indexing and assignments. Supported
builtins: range, len, abs, int, min, max, round, str; list.append(value), list.pop(index),
dict.get(key,default). Assign to state entries rather than global variables. No slicing,
comprehensions, classes, imports or filesystem/network access. 48 KiB UTF-8 source,
65,000 evaluation operations per tick, 4,096 items per container, 16,384 stored values.
Game loop: init once, then update input + state followed by draw. Keep draw side-effect free.
Example:
def init():
    state["x"] = 80
    state["score"] = 0

def update():
    if held("left"):
        state["x"] = max(0, state["x"] - 2)

def draw():
    clear("#101524")
    rect(state["x"], 72, 8, 8, "#f6c85c")
"""
API_DOCS = API_DOC
WIDTH = HEIGHT = 160
FPS = 30
ACTIONS = frozenset(["left", "right", "up", "down", "a", "b", "start", "select"] +
                    [f"key{i:02d}" for i in range(1, 21)])
_MAX_ITEMS = 4096
_MAX_TEXT = 2048
_BUDGET = 65000


class GameError(ValueError):
    """An error the editor can display to a game author."""


class _Return(Exception):
    def __init__(self, value):
        self.value = value


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


@lru_cache(maxsize=256)
def _label(value, scale):
    mask = Image.new("L", (max(1, 4 * len(value) - 1), 5))
    pen = ImageDraw.Draw(mask)
    for i, letter in enumerate(value.upper()):
        rows = GLYPHS.get(letter, GLYPHS["?"])
        for y, row in enumerate(rows):
            for x in range(3):
                if int(row) & (4 >> x):
                    pen.point((4 * i + x, y), 255)
    return mask if scale == 1 else mask.resize(
        (mask.width * scale, 5 * scale), Image.Resampling.NEAREST)


def _int(value):
    if type(value) not in (int, bool, float):
        raise ValueError("expected a number")
    return int(value)


def _checked(value):
    if type(value) is int and value.bit_length() > 63:
        raise ValueError("integer exceeded 63 bits")
    if type(value) is float and (not math.isfinite(value) or abs(value) > 1e15):
        raise ValueError("number is outside supported range")
    if type(value) is str and len(value) > _MAX_TEXT:
        raise ValueError("string too long")
    return value


def _scalar(value):
    if type(value) not in (int, float, bool, str, type(None)):
        raise ValueError("expected a number, string, boolean or None")
    return value


def _number(value):
    if type(value) not in (int, float, bool):
        raise ValueError("expected a number")
    return value


def _key(value):
    if type(value) not in (str, int):
        raise ValueError("indices must be integers or strings")
    return value


_ALLOWED = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Assign, ast.AugAssign,
            ast.Expr, ast.If, ast.For, ast.While, ast.Return, ast.Break, ast.Continue,
            ast.Pass, ast.Name, ast.Load, ast.Store, ast.Constant, ast.List, ast.Tuple,
            ast.Dict, ast.Subscript, ast.Call, ast.Attribute, ast.BinOp, ast.BoolOp,
            ast.Compare, ast.UnaryOp, ast.IfExp, ast.Add, ast.Sub, ast.Mult, ast.Div,
            ast.FloorDiv, ast.Mod, ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or, ast.Eq,
            ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
_MATH = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
         ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
_CMP = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
        ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge}


class Game:
    """One deterministic game instance. No imports or evaluation of native Python code."""

    def __init__(self, source, seed=1):
        if type(source) is not str or len(source.encode("utf-8")) > 49152:
            raise GameError("game source must fit in 48 KiB")
        try:
            module = ast.parse(source, filename="main.py")
            nodes = list(ast.walk(module))
        except (SyntaxError, RecursionError, ValueError) as error:
            raise GameError(f"main.py:{getattr(error, 'lineno', 1)}: {error}") from None
        if len(nodes) > 8000:
            raise GameError("game source exceeds syntax tree limit")
        for node in nodes:
            if not isinstance(node, _ALLOWED):
                raise GameError(f"main.py:{getattr(node,'lineno',1)}: unsupported {type(node).__name__}")
            if isinstance(node, ast.Constant):
                if type(node.value) not in (int, float, bool, str, type(None)):
                    raise GameError(f"main.py:{node.lineno}: unsupported literal")
                try:
                    _checked(node.value)
                except ValueError as err:
                    raise GameError(f"main.py:{node.lineno}: {err}") from None
            if isinstance(node, ast.Dict) and None in node.keys:
                raise GameError(f"main.py:{node.lineno}: dictionary unpacking is unsupported")
            if isinstance(node, ast.Name) and node.id.startswith("_"):
                raise GameError(f"main.py:{node.lineno}: private names are unavailable")
            if isinstance(node, ast.Attribute) and node.attr not in ("append", "pop", "get"):
                raise GameError(f"main.py:{node.lineno}: unsupported method {node.attr}")
        self._functions = {}
        self._globals = {"state": {}, "tick": 0}
        self._rgb = Image.new("RGB", (WIDTH, HEIGHT), "#101524")
        self._pen = ImageDraw.Draw(self._rgb)
        self._rng = int(seed) & 0xffffffff
        self._tick = 0
        self._held = frozenset()
        self._pressed = frozenset()
        self._leds = {}
        self._line = 1
        self._depth = 0
        self._fuel = _BUDGET
        self._error = None
        self._phase = "load"
        self._builtins = {
            "range": self._range, "len": len, "abs": lambda n: abs(_number(n)),
            "int": _int, "round": lambda n: round(_number(n)), "str": lambda n: str(_scalar(n)),
            "min": lambda a, *v: min(_number(a), *map(_number, v)) if v else _number(a),
            "max": lambda a, *v: max(_number(a), *map(_number, v)) if v else _number(a),
            "rand": self._random, "held": lambda key: _key(key) in self._held,
            "pressed": lambda key: _key(key) in self._pressed, "led": self._led,
            "clear": self._clear, "rect": self._rect, "line": self._line_draw,
            "pixel": self._pixel, "text": self._text,
        }
        statements = []
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                args = node.args
                if (node.decorator_list or args.vararg or args.kwarg or args.kwonlyargs
                    or args.posonlyargs or args.defaults or node.returns or
                    any(a.annotation for a in args.args) or node.name.startswith("_")
                    or node.name in self._functions or node.name in self._builtins
                    or node.name in self._globals):
                    raise GameError(f"main.py:{node.lineno}: unsupported function signature or name")
                self._functions[node.name] = node
            elif isinstance(node, ast.Assign) or (
                    isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)):
                statements.append(node)
            else:
                raise GameError(f"main.py:{node.lineno}: put game behavior inside a function")
        for name in ("init", "update", "draw"):
            if name not in self._functions or self._functions[name].args.args:
                raise GameError(f"game must define {name}() with no arguments")
        self._guard(lambda: self._start(statements))

    def _start(self, statements):
        self._block(statements, self._globals)
        self._phase = "init"
        self._call("init", [])
        self._phase = "draw"
        self._call("draw", [])
        self._check_memory()

    def _guard(self, operation):
        self._fuel = _BUDGET
        try:
            return operation()
        except (ArithmeticError, ValueError, TypeError, IndexError, KeyError, RuntimeError,
                _Break, _Continue, _Return) as error:
            self._error = f"main.py:{self._line}: {str(error) or type(error).__name__}"
            raise GameError(self._error) from None

    def step(self, buttons=()):
        """Advance one fixed tick with the specified held actions (empty releases all)."""
        if self._error:
            raise GameError(self._error)
        if isinstance(buttons, str):
            buttons = [buttons]
        try:
            current = expand_buttons(buttons)
        except (ValueError, TypeError):
            raise GameError("buttons must be action names") from None
        if not current <= ACTIONS:
            raise GameError("unrecognized button; use an action or key01 through key20")
        self._pressed, self._held = current - self._held, current
        self._tick += 1
        self._globals["tick"] = self._tick
        def frame():
            self._phase = "update"
            self._call("update", [])
            self._phase = "draw"
            self._call("draw", [])
            self._check_memory()
        self._guard(frame)

    def image(self):
        """Return an independently owned RGB image of the most recently drawn frame."""
        return self._rgb.copy()

    def inspect(self):
        state = self._globals["state"]
        metrics = {str(k): v for k, v in state.items()
                   if type(v) in (int, float, bool, str) and len(str(v)) <= 120}
        return {"tick": self._tick, "score": metrics.get("score", 0),
                "status": metrics.get("status", "running"), "keys": dict(self._leds),
                "metrics": metrics, "error": self._error}

    def _check_memory(self):
        seen, active = set(), set()
        count = 0
        def visit(value, depth):
            nonlocal count
            count += 1
            if depth > 24 or count > 16384:
                raise ValueError("game state exceeds memory budget")
            if type(value) not in (dict, list, tuple, range):
                return
            ident = id(value)
            if ident in active:
                raise ValueError("cyclic game state is unsupported")
            if ident in seen:
                return
            active.add(ident)
            for child in value.values() if type(value) is dict else value:
                visit(child, depth + 1)
            active.remove(ident)
            seen.add(ident)
        visit(self._globals, 0)

    def _range(self, *args):
        value = range(*map(_int, args))
        if len(value) > _MAX_ITEMS:
            raise ValueError("range exceeds 4096 items")
        return value

    def _random(self, low, high):
        low, high = _int(low), _int(high)
        if high < low:
            raise ValueError("rand upper bound precedes lower bound")
        self._rng = (1664525 * self._rng + 1013904223) & 0xffffffff
        return low + self._rng % (high - low + 1)

    @staticmethod
    @lru_cache(maxsize=256)
    def _color(color):
        if (type(color) is not str or len(color) not in (4, 7) or color[0] != "#" or
                any(ch not in "0123456789ABCDEFabcdef" for ch in color[1:])):
            raise ValueError("expected a hex color such as #70ece1")
        return color

    def _led(self, key, color):
        if type(key) is int:
            key = f"key{key:02d}"
        if key not in ACTIONS or not key.startswith("key"):
            raise ValueError("LED key must be key01..key20 or 1..20")
        self._leds[key] = self._color(color)

    def _screen(self):
        if self._phase != "draw":
            raise ValueError("canvas commands belong in draw()")

    def _clear(self, color):
        self._screen()
        self._rgb.paste(self._color(color), (0, 0, WIDTH, HEIGHT))

    def _rect(self, x, y, w, h, color):
        self._screen()
        x, y, w, h = map(_int, (x, y, w, h))
        box = (max(x, 0), max(y, 0), min(x + w, WIDTH), min(y + h, HEIGHT))
        if box[0] < box[2] and box[1] < box[3]:
            self._rgb.paste(self._color(color), box)

    def _pixel(self, x, y, color):
        self._rect(x, y, 1, 1, color)

    def _line_draw(self, x, y, x2, y2, color):
        self._screen()
        points = tuple(max(-512, min(512, _int(n))) for n in (x, y, x2, y2))
        self._pen.line(points, fill=self._color(color))

    def _text(self, x, y, value, color, scale=1):
        self._screen()
        x, y, scale = _int(x), _int(y), _int(scale)
        value = str(_scalar(value))
        if len(value) > 80 or not 1 <= scale <= 8:
            raise ValueError("text supports up to 80 characters at scale 1..8")
        if x < WIDTH and y < HEIGHT and x + len(value)*4*scale >= 0 and y + 5*scale >= 0:
            mask = _label(value, scale)
            self._rgb.paste(self._color(color), (x, y, x+mask.width, y+mask.height), mask)

    def _visit(self, node):
        self._fuel -= 1
        self._line = node.lineno
        if self._fuel < 0:
            raise ValueError("tick budget exceeded; reduce loop or drawing work")

    def _block(self, nodes, env):
        for node in nodes:
            self._visit(node)
            if isinstance(node, ast.Assign):
                value = self._expr(node.value, env)
                for target in node.targets:
                    self._set(target, value, env)
            elif isinstance(node, ast.AugAssign):
                value = self._math(node.op, self._expr(node.target, env), self._expr(node.value, env))
                self._set(node.target, value, env)
            elif isinstance(node, ast.Expr):
                self._expr(node.value, env)
            elif isinstance(node, ast.If):
                self._block(node.body if self._expr(node.test, env) else node.orelse, env)
            elif isinstance(node, (ast.For, ast.While)):
                items = iter(self._expr(node.iter, env)) if isinstance(node, ast.For) else None
                while True:
                    self._visit(node)
                    if items is not None:
                        try:
                            item = next(items)
                        except StopIteration:
                            self._block(node.orelse, env)
                            break
                        self._set(node.target, item, env)
                    elif not self._expr(node.test, env):
                        self._block(node.orelse, env)
                        break
                    try:
                        self._block(node.body, env)
                    except _Continue:
                        continue
                    except _Break:
                        break
            elif isinstance(node, ast.Return):
                raise _Return(self._expr(node.value, env) if node.value else None)
            elif isinstance(node, ast.Break):
                raise _Break()
            elif isinstance(node, ast.Continue):
                raise _Continue()
            elif not isinstance(node, ast.Pass):
                raise ValueError("unsupported statement")

    def _set(self, target, value, env):
        if isinstance(target, ast.Name):
            if target.id in ("state", "tick") or target.id in self._functions or target.id in self._builtins:
                raise ValueError(f"{target.id} is reserved")
            env[target.id] = value
        elif isinstance(target, (ast.List, ast.Tuple)):
            if len(target.elts) != len(value):
                raise ValueError("unpacking length mismatch")
            for child, item in zip(target.elts, value):
                self._set(child, item, env)
        elif isinstance(target, ast.Subscript):
            parent, key = self._expr(target.value, env), _key(self._expr(target.slice, env))
            if type(parent) is dict and len(parent) >= _MAX_ITEMS and key not in parent:
                raise ValueError("dictionary is full")
            parent[key] = value
        else:
            raise ValueError("unsupported assignment target")

    def _math(self, op, left, right):
        if isinstance(op, ast.Add) and type(left) is str and type(right) is str:
            return _checked(left + right)
        return _checked(_MATH[type(op)](_number(left), _number(right)))

    def _expr(self, node, env):
        self._visit(node)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in env:
                return env[node.id]
            if node.id in self._globals:
                return self._globals[node.id]
            raise ValueError(f"unknown name {node.id}")
        if isinstance(node, (ast.List, ast.Tuple)):
            if len(node.elts) > _MAX_ITEMS:
                raise ValueError("too many items")
            result = [self._expr(child, env) for child in node.elts]
            return tuple(result) if isinstance(node, ast.Tuple) else result
        if isinstance(node, ast.Dict):
            if len(node.keys) > _MAX_ITEMS:
                raise ValueError("too many dictionary entries")
            return {_key(self._expr(k, env)): self._expr(v, env) for k,v in zip(node.keys,node.values)}
        if isinstance(node, ast.Subscript):
            return self._expr(node.value, env)[_key(self._expr(node.slice, env))]
        if isinstance(node, ast.IfExp):
            return self._expr(node.body if self._expr(node.test, env) else node.orelse, env)
        if isinstance(node, ast.BinOp):
            return self._math(node.op, self._expr(node.left, env), self._expr(node.right, env))
        if isinstance(node, ast.UnaryOp):
            v = self._expr(node.operand, env)
            if isinstance(node.op, ast.Not):
                return not v
            return _checked(-_number(v) if isinstance(node.op, ast.USub) else _number(v))
        if isinstance(node, ast.BoolOp):
            for operand in node.values:
                result = self._expr(operand, env)
                if isinstance(node.op, ast.And) and not result or isinstance(node.op, ast.Or) and result:
                    return result
            return result
        if isinstance(node, ast.Compare):
            left = _scalar(self._expr(node.left, env))
            for op, operand in zip(node.ops, node.comparators):
                right = _scalar(self._expr(operand, env))
                if not _CMP[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Call):
            args = [self._expr(v, env) for v in node.args]
            self._line = node.lineno
            if isinstance(node.func, ast.Name):
                return self._call(node.func.id, args)
            if isinstance(node.func, ast.Attribute):
                obj = self._expr(node.func.value, env)
                method = node.func.attr
                if type(obj) is list and method == "append" and len(args)==1:
                    if len(obj) >= _MAX_ITEMS:
                        raise ValueError("list is full")
                    obj.append(args[0])
                    return None
                if type(obj) is list and method == "pop" and len(args)<=1:
                    return obj.pop(*map(_int,args))
                if type(obj) is dict and method == "get" and len(args) in (1,2):
                    return obj.get(_key(args[0]), *args[1:])
            raise ValueError("unsupported call")
        raise ValueError("unsupported expression")

    def _call(self, name, args):
        if name in self._builtins:
            return _checked(self._builtins[name](*args))
        function = self._functions.get(name)
        if function is None:
            raise ValueError(f"unknown function {name}")
        if len(args) != len(function.args.args):
            raise ValueError(f"wrong argument count for {name}")
        if self._depth >= 24:
            raise ValueError("call depth exceeded")
        self._depth += 1
        try:
            self._block(function.body, {param.arg: val for param,val in zip(function.args.args,args)})
        except _Return as done:
            return done.value
        finally:
            self._depth -= 1
        return None
