# Stackfall | A seven-piece falling-block game for the LAB Pocket.
# The opening stack has a four-cell gap. Hard drop the first bar to clear it.
COLORS = ["#5cdddf", "#ffcc63", "#c793f7", "#79d68c", "#f47d8b", "#739cf5", "#ff9b64"]
SHAPES = [
    [(0, 1), (1, 1), (2, 1), (3, 1)],
    [(0, 0), (1, 0), (0, 1), (1, 1)],
    [(1, 0), (0, 1), (1, 1), (2, 1)],
    [(1, 0), (2, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(2, 0), (0, 1), (1, 1), (2, 1)]
]

def shuffled_bag(first):
    bag = []
    for n in range(first, 7):
        bag.append(n)
    for i in range(len(bag) - 1, 0, -1):
        j = rand(0, i)
        bag[i], bag[j] = bag[j], bag[i]
    return bag

def take():
    if len(state["bag"]) == 0:
        state["bag"] = shuffled_bag(0)
    return state["bag"].pop()

def init():
    state["board"] = []
    for i in range(200):
        state["board"].append(-1)
    for row, xs, tint in [(19, [0,1,2,7,8,9], 3), (18, [0,1,7,8,9], 6),
                           (17, [0,8,9], 2), (16, [9], 0)]:
        for x in xs:
            state["board"][row*10+x] = (tint + x//2) % 7
    state["score"] = 0
    state["lines"] = 0
    state["locks"] = 0
    state["status"] = "Playing"
    state["bag"] = shuffled_bag(1)
    state["next"] = 0
    spawn()
    for k in [2,6,7,8,10]:
        led(k, "#5cdddf")
    led(9, "#ffcc63")
    led(5, "#354254")

def shape(kind, turns):
    result = []
    for x, y in SHAPES[kind]:
        if kind != 1:
            for turn in range(turns % 4):
                x, y = (3 if kind == 0 else 2) - y, x
        result.append((x,y))
    return result

def fits(x, y, tiles):
    for dx, dy in tiles:
        xx, yy = x + dx, y + dy
        if xx < 0 or xx > 9 or yy < 0 or yy > 19:
            return False
        if state["board"][yy * 10 + xx] >= 0:
            return False
    return True

def spawn():
    state["piece"] = state["next"]
    state["next"] = take()
    state["turn"] = 0
    state["tiles"] = shape(state["piece"], 0)
    state["x"], state["y"] = 3, 0
    state["age"], state["travel"] = 0, 0
    if not fits(3, 0, state["tiles"]):
        state["status"] = "Game over"

def lock():
    for dx,dy in state["tiles"]:
        index = (state["y"]+dy)*10 + state["x"]+dx
        state["board"][index] = state["piece"]
    remaining = []
    cleared = 0
    for y in range(20):
        filled = True
        for x in range(10):
            if state["board"][y*10+x] < 0:
                filled = False
        if filled:
            cleared += 1
        else:
            for x in range(10):
                remaining.append(state["board"][y*10+x])
    board = []
    for i in range(cleared*10):
        board.append(-1)
    for cell in remaining:
        board.append(cell)
    state["board"] = board
    state["lines"] += cleared
    state["score"] += [0,100,300,500,800][cleared]
    state["locks"] += 1
    spawn()

def drop_one():
    if fits(state["x"], state["y"]+1, state["tiles"]):
        state["y"] += 1
        return True
    lock()
    return False

def update():
    if state["status"] == "Game over":
        if pressed("start") or pressed("a"):
            init()
        return
    dx = int(held("right")) - int(held("left"))
    if dx:
        state["travel"] += 1
        if (pressed("left") or pressed("right") or
                (state["travel"] > 6 and state["travel"] % 2 == 0)):
            if fits(state["x"]+dx, state["y"], state["tiles"]):
                state["x"] += dx
    else:
        state["travel"] = 0
    if pressed("up") or pressed("a"):
        turn = (state["turn"] + 1) % 4
        tiles = shape(state["piece"], turn)
        for kick in [0, -1, 1, -2, 2]:
            if fits(state["x"]+kick, state["y"], tiles):
                state["tiles"], state["turn"] = tiles, turn
                state["x"] += kick
                break
    if pressed("b"):
        while fits(state["x"], state["y"]+1, state["tiles"]):
            state["y"] += 1
            state["score"] += 2
        lock()
        return
    state["age"] += 1
    speed = max(3, 25 - state["lines"]//3)
    if state["age"] >= speed or (held("down") and state["age"] >= 2):
        state["age"] = 0
        drop_one()

def brick(px, py, color, size):
    rect(px, py, size-1, size-1, color)
    line(px, py, px+size-3, py, "#fff1d7")
    pixel(px+size-2, py+size-2, "#39445c")

def draw():
    clear("#161c2d")
    # The board is 10 by 20. One pixel between cells keeps every tile legible.
    rect(5, 8, 74, 144, "#54617a")
    rect(6, 9, 72, 142, "#0c1324")
    for col in range(11):
        line(7+col*7, 10, 7+col*7, 149, "#1e2a40")
    for row in range(21):
        line(7, 10+row*7, 76, 10+row*7, "#1e2a40")
    for i in range(200):
        tile = state["board"][i]
        if tile >= 0:
            brick(8+i%10*7, 11+i//10*7, COLORS[tile], 7)
    color = COLORS[state["piece"]]
    ghost = state["y"]
    while fits(state["x"], ghost+1, state["tiles"]):
        ghost += 1
    for dx,dy in state["tiles"]:
        px = 8+(state["x"]+dx)*7
        py = 11+(ghost+dy)*7
        line(px,py+5,px+5,py+5, "#63829a")
        pixel(px,py+3,"#63829a")
        brick(px,11+(state["y"]+dy)*7,color,7)
    text(89,12,"STACK","#f2ecd8",2)
    text(89,25,"FALL","#f2c65d",2)
    line(89,42,151,42,"#4c566d")
    text(89,50,"NEXT","#95a6bb")
    rect(89,60,62,25,"#232e45")
    for dx,dy in SHAPES[state["next"]]:
        brick(107+dx*6,66+dy*6,COLORS[state["next"]],6)
    text(89,96,"SCORE","#95a6bb")
    text(89,106,state["score"],"#faf0cd",2)
    text(89,128,"LINES","#95a6bb")
    text(89,138,state["lines"],"#65d8d5",2)
    if state["status"] == "Game over":
        rect(8,62,68,29,"#283348")
        text(15,68,"GAME OVER","#ffd16c")
        text(15,78,"A TO RESTART","#e8eff5")
