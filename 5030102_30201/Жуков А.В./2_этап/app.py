from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Deque, Dict, List, Optional, Tuple, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn


class DirectionType(Enum):
    MEASURE_FORWARD = "MeasureForward"
    MEASURE_BACKWARD = "MeasureBackward"
    MEASURE_LEFT = "MeasureLeft"
    MEASURE_RIGHT = "MeasureRight"
    DIAG_MV = "DiagMV"
    DIAG_MN = "DiagMN"


class CellType(Enum):
    PLATFORM = 0
    SENSOR = 1
    MEASURED = 2
    STATION = 3
    BARRIER = 4
    FINISH = 5
    WINDOW = 6


@dataclass
class RobotCell:
    x: int
    y: int
    has_robot: bool = False
    cell_type: CellType = CellType.PLATFORM


class RobotMaze:
    def __init__(self, width: int, length: int):
        self.width = width
        self.length = length
        self._grid: List[List[RobotCell]] = []
        self.initialize_maze(CellType.PLATFORM)

    def initialize_maze(self, cell_type: CellType):
        self._grid = []
        for y in range(self.length):
            row: List[RobotCell] = []
            for x in range(self.width):
                row.append(RobotCell(x=x, y=y, has_robot=False, cell_type=cell_type))
            self._grid.append(row)

    def get_cell(self, x: int, y: int) -> Optional[RobotCell]:
        if 0 <= x < self.width and 0 <= y < self.length:
            return self._grid[y][x]
        return None

    def get_neighbor(self, c: RobotCell, d: Union[str, DirectionType]) -> Optional[RobotCell]:
        dv = d.value if isinstance(d, DirectionType) else d
        offsets = {
            DirectionType.MEASURE_FORWARD.value: (0, 1),
            DirectionType.MEASURE_BACKWARD.value: (0, -1),
            DirectionType.MEASURE_LEFT.value: (-1, 0),
            DirectionType.MEASURE_RIGHT.value: (1, 0),
            DirectionType.DIAG_MV.value: (-1, 1),
            DirectionType.DIAG_MN.value: (1, -1),
        }
        dx, dy = offsets.get(dv, (0, 0))
        return self.get_cell(c.x + dx, c.y + dy)


class MazeEditor:
    def __init__(self, maze: RobotMaze):
        self.maze = maze

    def clear_robot(self):
        for y in range(self.maze.length):
            for x in range(self.maze.width):
                c = self.maze.get_cell(x, y)
                if c:
                    c.has_robot = False

    def place_robot(self, x: int, y: int):
        self.clear_robot()
        c = self.maze.get_cell(x, y)
        if c and c.cell_type not in (CellType.BARRIER, CellType.WINDOW):
            c.has_robot = True

    def set_cell_type(self, x: int, y: int, t: CellType):
        c = self.maze.get_cell(x, y)
        if c:
            c.cell_type = t
            if t in (CellType.BARRIER, CellType.WINDOW):
                c.has_robot = False

    def cycle_cell_type(self, x: int, y: int):
        order = [
            CellType.PLATFORM,
            CellType.SENSOR,
            CellType.MEASURED,
            CellType.STATION,
            CellType.BARRIER,
            CellType.WINDOW,
            CellType.FINISH,
        ]
        c = self.maze.get_cell(x, y)
        if not c:
            return
        idx = order.index(c.cell_type) if c.cell_type in order else 0
        self.set_cell_type(x, y, order[(idx + 1) % len(order)])


Coord = Tuple[int, int]


class MazeInspector:
    def __init__(self, maze: RobotMaze):
        self.maze = maze

    def find_finish(self) -> Optional[Coord]:
        for y in range(self.maze.length):
            for x in range(self.maze.width):
                c = self.maze.get_cell(x, y)
                if c and c.cell_type == CellType.FINISH:
                    return (x, y)
        return None

    def remaining_targets(self) -> List[Coord]:
        res: List[Coord] = []
        for y in range(self.maze.length):
            for x in range(self.maze.width):
                c = self.maze.get_cell(x, y)
                if c and c.cell_type in (CellType.PLATFORM, CellType.SENSOR):
                    res.append((x, y))
        return res


class RobotMeteorologist:
    def __init__(self, maze: RobotMaze):
        self.maze = maze
        self.current_cell: Optional[RobotCell] = None
        for y in range(self.maze.length):
            for x in range(self.maze.width):
                c = self.maze.get_cell(x, y)
                if c and c.has_robot:
                    self.current_cell = c
                    return

    def _move_to(self, nc: Optional[RobotCell]) -> Optional[RobotCell]:
        if nc and nc.cell_type not in (CellType.BARRIER, CellType.WINDOW):
            if self.current_cell:
                self.current_cell.has_robot = False
            self.current_cell = nc
            nc.has_robot = True
            return nc
        return None

    def go_measure_forward(self) -> Optional[RobotCell]:
        return self._move_to(self.maze.get_neighbor(self.current_cell, DirectionType.MEASURE_FORWARD.value)) if self.current_cell else None

    def go_measure_backward(self) -> Optional[RobotCell]:
        return self._move_to(self.maze.get_neighbor(self.current_cell, DirectionType.MEASURE_BACKWARD.value)) if self.current_cell else None

    def move_left(self) -> Optional[RobotCell]:
        return self._move_to(self.maze.get_neighbor(self.current_cell, DirectionType.MEASURE_LEFT.value)) if self.current_cell else None

    def move_right(self) -> Optional[RobotCell]:
        return self._move_to(self.maze.get_neighbor(self.current_cell, DirectionType.MEASURE_RIGHT.value)) if self.current_cell else None

    def go_up_diag(self) -> Optional[RobotCell]:
        return self._move_to(self.maze.get_neighbor(self.current_cell, DirectionType.DIAG_MV.value)) if self.current_cell else None

    def go_down_diag(self) -> Optional[RobotCell]:
        return self._move_to(self.maze.get_neighbor(self.current_cell, DirectionType.DIAG_MN.value)) if self.current_cell else None

    def platform(self):
        if self.current_cell and self.current_cell.cell_type == CellType.PLATFORM:
            self.current_cell.cell_type = CellType.MEASURED

    def sensor(self):
        if self.current_cell and self.current_cell.cell_type == CellType.SENSOR:
            self.current_cell.cell_type = CellType.PLATFORM


class PathFinder:
    def __init__(self, maze: RobotMaze):
        self.maze = maze

    def _passable(self, c: Optional[RobotCell]) -> bool:
        return c is not None and c.cell_type not in (CellType.BARRIER, CellType.WINDOW)

    def find_path(self, start: Coord, goal: Coord) -> Optional[List[str]]:
        if start == goal:
            return []

        s = self.maze.get_cell(*start)
        g = self.maze.get_cell(*goal)
        if not self._passable(s) or not self._passable(g):
            return None

        q: Deque[Coord] = deque([start])
        prev: Dict[Coord, Tuple[Coord, str]] = {}
        visited = {start}

        dirs = [
            DirectionType.MEASURE_RIGHT.value,
            DirectionType.MEASURE_FORWARD.value,
            DirectionType.MEASURE_LEFT.value,
            DirectionType.MEASURE_BACKWARD.value,
            DirectionType.DIAG_MV.value,
            DirectionType.DIAG_MN.value,
        ]

        while q:
            x, y = q.popleft()
            cur = self.maze.get_cell(x, y)
            if cur is None:
                continue

            for d in dirs:
                nb = self.maze.get_neighbor(cur, d)
                if not self._passable(nb):
                    continue
                nc = (nb.x, nb.y)
                if nc in visited:
                    continue
                visited.add(nc)
                prev[nc] = ((x, y), d)
                if nc == goal:
                    return self._reconstruct(prev, start, goal)
                q.append(nc)

        return None

    def _reconstruct(self, prev: Dict[Coord, Tuple[Coord, str]], start: Coord, goal: Coord) -> List[str]:
        steps: List[str] = []
        cur = goal
        while cur != start:
            p, d = prev[cur]
            steps.append(d)
            cur = p
        steps.reverse()
        return steps


class RobotDriver:
    def __init__(self, robot: RobotMeteorologist):
        self.robot = robot

    def step(self, d: str) -> Optional[RobotCell]:
        if d == DirectionType.MEASURE_FORWARD.value:
            return self.robot.go_measure_forward()
        if d == DirectionType.MEASURE_BACKWARD.value:
            return self.robot.go_measure_backward()
        if d == DirectionType.MEASURE_LEFT.value:
            return self.robot.move_left()
        if d == DirectionType.MEASURE_RIGHT.value:
            return self.robot.move_right()
        if d == DirectionType.DIAG_MV.value:
            return self.robot.go_up_diag()
        if d == DirectionType.DIAG_MN.value:
            return self.robot.go_down_diag()
        return None

    def process_current(self):
        c = self.robot.current_cell
        if c is None:
            return
        if c.cell_type == CellType.SENSOR:
            self.robot.sensor()
            self.robot.platform()
            return
        if c.cell_type == CellType.PLATFORM:
            self.robot.platform()


class MissionRuntime:
    def __init__(self, maze: RobotMaze, robot: RobotMeteorologist):
        self.maze = maze
        self.robot = robot
        self.inspector = MazeInspector(maze)
        self.finder = PathFinder(maze)
        self.driver = RobotDriver(robot)
        self.path: List[str] = []
        self.target: Optional[Coord] = None
        self.done = False
        self.finish: Optional[Coord] = self.inspector.find_finish()

    def step(self):
        if self.done:
            return
        if self.robot.current_cell is None:
            raise RuntimeError("Robot not placed")

        self.driver.process_current()

        remaining = self.inspector.remaining_targets()
        start = (self.robot.current_cell.x, self.robot.current_cell.y)

        if remaining:
            if self.target is None or self.target not in remaining or not self.path:
                self.target, self.path = self._pick_nearest_target(start, remaining)
                if self.target is None:
                    raise RuntimeError("Есть П/Д, но они недостижимы")
            if not self.path:
                self.driver.process_current()
                self.target = None
                return
            d = self.path.pop(0)
            moved = self.driver.step(d)
            if moved is None:
                self.path = []
                self.target = None
                raise RuntimeError("Move blocked")
            return

        if self.finish is None:
            raise RuntimeError("Finish not placed")

        if self.robot.current_cell.cell_type == CellType.FINISH:
            self.done = True
            return

        if self.target != self.finish or not self.path:
            self.target = self.finish
            self.path = self.finder.find_path(start, self.finish) or []
            if not self.path:
                raise RuntimeError("Finish unreachable")

        d = self.path.pop(0)
        moved = self.driver.step(d)
        if moved is None:
            self.path = []
            raise RuntimeError("Move blocked")

    def _pick_nearest_target(self, start: Coord, targets: List[Coord]) -> Tuple[Optional[Coord], List[str]]:
        best_t: Optional[Coord] = None
        best_p: Optional[List[str]] = None
        best_len: Optional[int] = None

        for t in targets:
            p = self.finder.find_path(start, t)
            if p is None:
                continue
            if best_len is None or len(p) < best_len:
                best_len = len(p)
                best_t = t
                best_p = p

        return best_t, (best_p or [])


def maze_to_dict(maze: RobotMaze) -> dict:
    grid = []
    robot = None
    for y in range(maze.length - 1, -1, -1):
        row = []
        for x in range(maze.width):
            c = maze.get_cell(x, y)
            row.append({"x": x, "y": y, "t": c.cell_type.name, "r": c.has_robot})
            if c.has_robot:
                robot = {"x": x, "y": y, "t": c.cell_type.name}
        grid.append(row)

    return {
        "width": maze.width,
        "length": maze.length,
        "grid": grid,
        "robot": robot,
    }


def build_demo_state() -> Tuple[RobotMaze, MazeEditor]:
    maze = RobotMaze(width=10, length=8)
    editor = MazeEditor(maze)
    maze.initialize_maze(CellType.PLATFORM)
    editor.place_robot(0, 0)
    editor.set_cell_type(9, 7, CellType.FINISH)
    for x in range(2, 10):
        editor.set_cell_type(x, 3, CellType.BARRIER)
    editor.set_cell_type(4, 4, CellType.WINDOW)
    editor.set_cell_type(5, 5, CellType.WINDOW)
    editor.set_cell_type(1, 0, CellType.SENSOR)
    editor.set_cell_type(3, 1, CellType.SENSOR)
    editor.set_cell_type(6, 2, CellType.SENSOR)
    editor.set_cell_type(8, 6, CellType.SENSOR)
    editor.set_cell_type(2, 5, CellType.STATION)
    editor.set_cell_type(7, 5, CellType.STATION)
    return maze, editor


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

MAZE, EDITOR = build_demo_state()
ROBOT = RobotMeteorologist(MAZE)
RUNTIME = MissionRuntime(MAZE, ROBOT)
STEPS = 0


def reset_runtime():
    global ROBOT, RUNTIME, STEPS
    ROBOT = RobotMeteorologist(MAZE)
    RUNTIME = MissionRuntime(MAZE, ROBOT)
    STEPS = 0


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/api/state")
def api_state():
    rem = MazeInspector(MAZE).remaining_targets()
    finish = MazeInspector(MAZE).find_finish()
    rc = ROBOT.current_cell
    return {
        "maze": maze_to_dict(MAZE),
        "steps": STEPS,
        "remaining": len(rem),
        "runningDone": RUNTIME.done,
        "finish": finish,
        "robotCell": {"x": rc.x, "y": rc.y, "t": rc.cell_type.name} if rc else None,
    }


@app.post("/api/demo")
def api_demo():
    global MAZE, EDITOR
    MAZE, EDITOR = build_demo_state()
    reset_runtime()
    return {"ok": True}


@app.post("/api/reset")
def api_reset():
    global MAZE, EDITOR
    MAZE = RobotMaze(width=10, length=8)
    EDITOR = MazeEditor(MAZE)
    MAZE.initialize_maze(CellType.PLATFORM)
    EDITOR.place_robot(0, 0)
    EDITOR.set_cell_type(9, 7, CellType.FINISH)
    reset_runtime()
    return {"ok": True}


@app.post("/api/step")
def api_step():
    global STEPS
    try:
        RUNTIME.step()
        STEPS += 1
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@app.post("/api/cycle")
def api_cycle(x: int, y: int):
    EDITOR.cycle_cell_type(x, y)
    reset_runtime()
    return {"ok": True}


@app.post("/api/place_robot")
def api_place_robot(x: int, y: int):
    EDITOR.place_robot(x, y)
    reset_runtime()
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
