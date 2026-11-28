# Prism Break | A three-life paddle game.
PALETTE = ["#f3688b","#fa9877","#f9ce70","#85ccad","#79b6e6","#a897df"]

def serve():
    state["status"] = "Ready"
    state["x"], state["y"] = state["paddle"]+10, 136
    state["vx"], state["vy"] = 1.6, -2.1

def init():
    state["paddle"], state["score"], state["lives"] = 69,0,3
    state["bricks"] = []
    for i in range(54):
        state["bricks"].append(1)
    serve()
    led(6,"#8ac7ff")
    led(8,"#8ac7ff")
    led(10,"#f49a82")

def update():
    if state["status"] == "Game over" or state["status"] == "Cleared":
        if pressed("a") or pressed("start"):
            init()
        return
    speed = int(held("right")) - int(held("left"))
    state["paddle"] = min(130,max(6,state["paddle"]+4*speed))
    if state["status"] == "Ready":
        state["x"] = state["paddle"]+10
        if pressed("a") or pressed("start"):
            state["status"] = "Playing"
        return
    nx,ny = state["x"]+state["vx"],state["y"]+state["vy"]
    if nx < 6 or nx > 153:
        state["vx"] = -state["vx"]
        nx = min(153,max(6,nx))
    if ny < 20:
        state["vy"] = abs(state["vy"])
        ny = 20
    if 24 <= ny < 78 and 8 <= nx < 152:
        col,row = int((nx-8)//16),int((ny-24)//9)
        index = row*9+col
        if state["bricks"][index] and (nx-8)%16 < 15 and (ny-24)%9 < 8:
            state["bricks"][index] = 0
            state["score"] += 10
            state["vy"] = -state["vy"]
            if state["score"] == 540:
                state["status"] = "Cleared"
    if state["vy"] > 0 and state["y"] < 141 and ny >= 141:
        if state["paddle"]-2 <= nx <= state["paddle"]+24:
            state["vy"] = -abs(state["vy"])
            state["vx"] = (nx - state["paddle"]-11)*0.20
            if abs(state["vx"]) < 0.6:
                state["vx"] = 0.6
            ny = 140
    if ny > 158:
        state["lives"] -= 1
        if state["lives"] == 0:
            state["status"] = "Game over"
        else:
            serve()
        return
    state["x"],state["y"] = nx,ny

def draw():
    clear("#151628")
    text(7,6,"PRISM","#f8e6c6",2)
    text(50,6,"BREAK","#fc997d",2)
    text(114,8,"PTS "+str(state["score"]),"#e6caa8")
    line(4,19,155,19,"#60546a")
    for row in range(6):
        for col in range(9):
            if state["bricks"][row*9+col]:
                x,y = 8+16*col,24+9*row
                rect(x,y,15,7,PALETTE[row])
                line(x+1,y+1,x+11,y+1,"#ffe0be")
                pixel(x+14,y+6,"#4f4566")
    for i in range(16):
        pixel(8+i*9, 99+(i*13)%30, "#4b435d")
    p = state["paddle"]
    rect(p,142,23,4,"#e5cadc")
    rect(p+3,141,17,2,"#fff3d8")
    rect(p,143,3,3,"#ff9184")
    rect(p+20,143,3,3,"#ff9184")
    x,y = int(state["x"]),int(state["y"])
    rect(x-1,y-2,3,5,"#ffe5a4")
    rect(x-2,y-1,5,3,"#ffe5a4")
    for i in range(state["lives"]):
        rect(8+i*6,153,4,2,"#f5af9b")
    if state["status"] == "Ready":
        text(53,111,"A TO LAUNCH","#fff1cc")
    if state["status"] == "Game over" or state["status"] == "Cleared":
        rect(25,86,110,28,"#2a2032")
        text(35,91,state["status"],"#ffc692",2)
        text(41,105,"A TO RESTART","#fae6c4")
