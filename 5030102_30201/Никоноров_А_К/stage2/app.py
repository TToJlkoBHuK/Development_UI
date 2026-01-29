import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Tuple
from collections import deque

app = FastAPI()

class CellType:
    ROAD = "Дорога"
    BED = "Грядка"
    FLOWERBED = "Клумба"
    SOIL = "Грунт"
    WATER = "Вода"
    WALL = "Стена"
    FINISH = "Финиш"

def get_initial_grid():
    grid = [["Дорога" for _ in range(7)] for _ in range(6)]
    grid[2][2], grid[1][3], grid[4][4] = [CellType.BED]*3
    grid[3][1], grid[3][2] = [CellType.WATER]*2
    grid[5][1], grid[0][5] = [CellType.SOIL]*2
    grid[2][4], grid[3][4] = [CellType.WALL]*2
    grid[5][6] = CellType.FINISH
    return grid

state = {
    "robot_pos": [0, 0],
    "grid": get_initial_grid(),
    "history": ["Система готова к работе"]
}

def is_passable(x, y, grid, allow_targets=False):
    if not (0 <= x < 6 and 0 <= y < 7): return False
    cell = grid[x][y]
    if cell in [CellType.WALL, CellType.WATER]: return False
    if cell == CellType.BED and not allow_targets: return False
    return True

@app.get("/")
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/state")
async def get_state():
    return state

@app.post("/move")
async def move_robot(delta: List[int]):
    rx, ry = state["robot_pos"]
    nx, ny = rx + delta[0], ry + delta[1]
    
    if is_passable(nx, ny, state["grid"], allow_targets=True):
        cell_before = state["grid"][nx][ny]
        action = ""
        if cell_before == CellType.BED:
            state["grid"][nx][ny] = CellType.FLOWERBED
            action = " (Грядка -> Клумба)"
        elif cell_before == CellType.SOIL:
            state["grid"][nx][ny] = CellType.WATER
            action = " (Грунт -> Вода)"
            
        state["robot_pos"] = [nx, ny]
        state["history"].append(f"Переход в ({nx},{ny}){action}")
        return {"status": "ok"}
    return {"status": "error", "msg": "Путь заблокирован"}

@app.get("/plan_auto")
async def plan_auto():
    start = tuple(state["robot_pos"])
    targets = []
    grid = state["grid"]
    
    for x in range(6):
        for y in range(7):
            if grid[x][y] in [CellType.BED, CellType.SOIL]:
                targets.append((x, y))
    
    finish = (5, 6)
    
    def bfs(s, t):
        q = deque([[s]])
        visited = {s}
        while q:
            path = q.popleft()
            curr = path[-1]
            if curr == t: return path
            for dx, dy in [(0,1), (0,-1), (-1,0), (1,0), (-1,1), (1,-1)]:
                neighbor = (curr[0]+dx, curr[1]+dy)
                if is_passable(neighbor[0], neighbor[1], grid) or neighbor == t:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        q.append(path + [neighbor])
        return []

    full_path = []
    curr_pos = start
    while targets:
        best_path = []
        chosen_t = None
        for t in targets:
            p = bfs(curr_pos, t)
            if p and (not best_path or len(p) < len(best_path)):
                best_path, chosen_t = p, t
        if not best_path: break
        full_path.extend(best_path[1:])
        curr_pos = chosen_t
        targets.remove(chosen_t)
    
    to_finish = bfs(curr_pos, finish)
    if to_finish: full_path.extend(to_finish[1:])
    
    return {"path": full_path}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)