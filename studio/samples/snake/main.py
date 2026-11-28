# Switchback | Signal garden.
def init():
    state["snake"] = [(4,10),(5,10),(6,10),(6,9),(6,8),(7,8),(8,8)]
    state["dx"], state["dy"] = 1, 0
    state["wish_x"], state["wish_y"] = 1, 0
    state["food_x"], state["food_y"] = 11, 8
    state["score"], state["age"] = 0, 0
    state["status"] = "Playing"
    for k in [2,6,7,8]:
        led(k,"#abe174")
    led(10,"#ffc279")

def occupies(x,y):
    for sx,sy in state["snake"]:
        if sx == x and sy == y:
            return True
    return False

def place_food():
    # Begin at a seeded offset, then guarantee a free choice even on a full garden.
    start_cell = rand(0,255)
    occupied = {}
    for x,y in state["snake"]:
        occupied[y*16+x] = True
    for i in range(256):
        v = (i+start_cell)%256
        if not occupied.get(v, False):
            state["food_x"], state["food_y"] = v%16,v//16
            return
    state["status"] = "Garden full"

def update():
    if state["status"] != "Playing":
        if pressed("start") or pressed("a"):
            init()
        return
    for direction, dx, dy in [("up",0,-1), ("down",0,1), ("left",-1,0), ("right",1,0)]:
        if pressed(direction) and dx*state["dx"]+dy*state["dy"] != -1:
            state["wish_x"], state["wish_y"] = dx,dy
    state["age"] += 1
    if state["age"] < (3 if held("a") else 8):
        return
    state["age"] = 0
    state["dx"], state["dy"] = state["wish_x"],state["wish_y"]
    x,y = state["snake"][-1]
    x,y = x+state["dx"], y+state["dy"]
    eating = x == state["food_x"] and y == state["food_y"]
    if x < 0 or y < 0 or x > 15 or y > 15:
        state["status"] = "Game over"
        return
    if not eating:
        state["snake"].pop(0)
    if occupies(x,y):
        state["status"] = "Game over"
        return
    state["snake"].append((x,y))
    if eating:
        state["score"] += 1
        place_food()

def draw():
    clear("#14251e")
    text(10,7,"SWITCHBACK","#c9f98e",2)
    text(116,9,"PTS "+str(state["score"]),"#f4e8a2")
    rect(12,22,132,132,"#486d4a")
    rect(13,23,130,130,"#203b2a")
    for y in range(16):
        for x in range(16):
            pixel(17+8*x,27+8*y,"#3e5b3c")
    for x,y in state["snake"]:
        rect(15+8*x,25+8*y,7,7,"#88bc64")
        rect(16+8*x,26+8*y,4,2,"#c3e57a")
    x,y = state["snake"][-1]
    rect(15+8*x,25+8*y,7,7,"#e3fa9d")
    pixel(18+8*x+2*state["dx"]+state["dy"],28+8*y+2*state["dy"]+state["dx"],"#1c382c")
    x,y = 18+8*state["food_x"],28+8*state["food_y"]
    rect(x-1,y-3,3,7,"#ffc279")
    rect(x-3,y-1,7,3,"#ffc279")
    pixel(x,y,"#fff2ad")
    if state["status"] != "Playing":
        rect(29,71,98,30,"#152c22")
        text(40,77,state["status"],"#e4f5a2",2)
        text(43,91,"PRESS A TO RESTART","#c3e57a")
