from __future__ import annotations

import sys
from collections import deque
from enum import Enum
from typing import Deque, Dict, Iterator, List, Optional, Tuple, Union

from PySide6.QtCore import QTimer, Qt, QRectF
from PySide6.QtGui import QBrush, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)


class DirectionType(Enum):
    MEASURE_FORWARD = "MeasureForward"
    MEASURE_BACKWARD = "MeasureBackward"
    MEASURE_LEFT = "MeasureLeft"
    MEASURE_RIGHT = "MeasureRight"
    DIAG_MV = "DiagMV"
    DIAG_MN = "DiagMN"


class CellType(Enum):
    PLATFORM = 0x0
    SENSOR = 0x1
    MEASURED = 0x2
    STATION = 0x3
    BARRIER = 0x4
    FINISH = 0x5
    WINDOW = 0x6

    @classmethod
    def from_value(cls, value: int) -> "CellType":
        base_value = value & 0x7
        for t in cls:
            if t.value == base_value:
                return t
        return cls.PLATFORM


class RobotCell:
    def __init__(self, has_robot: bool = False, cell_type: CellType = CellType.PLATFORM):
        self.has_robot = has_robot
        self.cell_type = cell_type
        self.x = 0
        self.y = 0


class RobotMaze:
    def __init__(self, width: int = 0, length: int = 0):
        self.width = width
        self.length = length
        self.cells: List[List[RobotCell]] = []
        self._grid: List[List[RobotCell]] = []
        if width > 0 and length > 0:
            self.initialize_maze(CellType.PLATFORM)

    def initialize_maze(self, cell_type: CellType):
        self._grid = []
        for y in range(self.length):
            row: List[RobotCell] = []
            for x in range(self.width):
                c = RobotCell(has_robot=False, cell_type=cell_type)
                c.x = x
                c.y = y
                row.append(c)
            self._grid.append(row)
        self._sync_cells_view()

    def _sync_cells_view(self):
        self.cells = []
        for y in range(self.length - 1, -1, -1):
            self.cells.append(self._grid[y])

    def get_cell_by_coordinates(self, x: int, y: int) -> Optional[RobotCell]:
        if 0 <= x < self.width and 0 <= y < self.length:
            return self._grid[y][x]
        return None

    def get_neighbor_cell(self, current_cell: RobotCell, search_direction: Union[str, DirectionType]) -> Optional[RobotCell]:
        if not current_cell:
            return None

        direction_value = search_direction.value if isinstance(search_direction, DirectionType) else search_direction

        offsets = {
            DirectionType.MEASURE_FORWARD.value: (0, 1),
            DirectionType.MEASURE_BACKWARD.value: (0, -1),
            DirectionType.MEASURE_LEFT.value: (-1, 0),
            DirectionType.MEASURE_RIGHT.value: (1, 0),
            DirectionType.DIAG_MV.value: (-1, 1),
            DirectionType.DIAG_MN.value: (1, -1),
        }

        dx, dy = offsets.get(direction_value, (0, 0))
        return self.get_cell_by_coordinates(current_cell.x + dx, current_cell.y + dy)

    def get_iterator(self) -> Iterator[RobotCell]:
        class ZigzagIterator:
            def __init__(self, maze: RobotMaze):
                self.maze = maze
                self.x = 0
                self.y = 0
                self.move_right = True
                self.started = False
                self.finished = False

            def __iter__(self):
                return self

            def __next__(self) -> RobotCell:
                if self.finished or self.maze.width == 0 or self.maze.length == 0:
                    raise StopIteration

                if not self.started:
                    self.started = True
                    cell = self.maze.get_cell_by_coordinates(self.x, self.y)
                    if cell is None:
                        self.finished = True
                        raise StopIteration
                    return cell

                if self.move_right:
                    if self.x < self.maze.width - 1:
                        self.x += 1
                    else:
                        if self.y < self.maze.length - 1:
                            self.y += 1
                            self.move_right = False
                        else:
                            self.finished = True
                else:
                    if self.x > 0:
                        self.x -= 1
                    else:
                        if self.y < self.maze.length - 1:
                            self.y += 1
                            self.move_right = True
                        else:
                            self.finished = True

                if self.finished:
                    raise StopIteration

                cell = self.maze.get_cell_by_coordinates(self.x, self.y)
                if cell is None:
                    self.finished = True
                    raise StopIteration
                return cell

        return ZigzagIterator(self)


class RobotMeteorologist:
    def __init__(self, maze: RobotMaze):
        self.maze = maze
        self.current_cell: Optional[RobotCell] = None
        for y in range(self.maze.length):
            for x in range(self.maze.width):
                c = self.maze.get_cell_by_coordinates(x, y)
                if c and c.has_robot:
                    self.current_cell = c
                    return

    def _move_to_cell(self, new_cell: Optional[RobotCell]) -> Optional[RobotCell]:
        if new_cell and new_cell.cell_type not in (CellType.BARRIER, CellType.WINDOW):
            if self.current_cell:
                self.current_cell.has_robot = False
            self.current_cell = new_cell
            new_cell.has_robot = True
            return new_cell
        return None

    def go_measure_forward(self) -> Optional[RobotCell]:
        if self.current_cell:
            return self._move_to_cell(self.maze.get_neighbor_cell(self.current_cell, DirectionType.MEASURE_FORWARD.value))
        return None

    def go_measure_backward(self) -> Optional[RobotCell]:
        if self.current_cell:
            return self._move_to_cell(self.maze.get_neighbor_cell(self.current_cell, DirectionType.MEASURE_BACKWARD.value))
        return None

    def move_left(self) -> Optional[RobotCell]:
        if self.current_cell:
            return self._move_to_cell(self.maze.get_neighbor_cell(self.current_cell, DirectionType.MEASURE_LEFT.value))
        return None

    def move_right(self) -> Optional[RobotCell]:
        if self.current_cell:
            return self._move_to_cell(self.maze.get_neighbor_cell(self.current_cell, DirectionType.MEASURE_RIGHT.value))
        return None

    def go_up_diag(self) -> Optional[RobotCell]:
        if self.current_cell:
            return self._move_to_cell(self.maze.get_neighbor_cell(self.current_cell, DirectionType.DIAG_MV.value))
        return None

    def go_down_diag(self) -> Optional[RobotCell]:
        if self.current_cell:
            return self._move_to_cell(self.maze.get_neighbor_cell(self.current_cell, DirectionType.DIAG_MN.value))
        return None

    def platform(self) -> None:
        if self.current_cell and self.current_cell.cell_type == CellType.PLATFORM:
            self.current_cell.cell_type = CellType.MEASURED

    def sensor(self) -> None:
        if self.current_cell and self.current_cell.cell_type == CellType.SENSOR:
            self.current_cell.cell_type = CellType.PLATFORM


Coord = Tuple[int, int]


class MazeEditor:
    def __init__(self, maze: RobotMaze):
        self.maze = maze

    def clear_robot(self):
        for y in range(self.maze.length):
            for x in range(self.maze.width):
                c = self.maze.get_cell_by_coordinates(x, y)
                if c:
                    c.has_robot = False

    def place_robot(self, x: int, y: int):
        self.clear_robot()
        c = self.maze.get_cell_by_coordinates(x, y)
        if c and c.cell_type not in (CellType.BARRIER, CellType.WINDOW):
            c.has_robot = True

    def set_cell_type(self, x: int, y: int, t: CellType):
        c = self.maze.get_cell_by_coordinates(x, y)
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
        c = self.maze.get_cell_by_coordinates(x, y)
        if not c:
            return
        idx = order.index(c.cell_type) if c.cell_type in order else 0
        nxt = order[(idx + 1) % len(order)]
        self.set_cell_type(x, y, nxt)


class MazeInspector:
    def __init__(self, maze: RobotMaze):
        self.maze = maze

    def find_finish(self) -> Optional[Coord]:
        for y in range(self.maze.length):
            for x in range(self.maze.width):
                c = self.maze.get_cell_by_coordinates(x, y)
                if c and c.cell_type == CellType.FINISH:
                    return (x, y)
        return None

    def remaining_targets(self) -> List[Coord]:
        res: List[Coord] = []
        for y in range(self.maze.length):
            for x in range(self.maze.width):
                c = self.maze.get_cell_by_coordinates(x, y)
                if c and c.cell_type in (CellType.PLATFORM, CellType.SENSOR):
                    res.append((x, y))
        return res


class PathFinder:
    def __init__(self, maze: RobotMaze):
        self.maze = maze

    def _passable(self, c: Optional[RobotCell]) -> bool:
        return c is not None and c.cell_type not in (CellType.BARRIER, CellType.WINDOW)

    def find_path(self, start: Coord, goal: Coord) -> Optional[List[str]]:
        if start == goal:
            return []

        start_cell = self.maze.get_cell_by_coordinates(start[0], start[1])
        goal_cell = self.maze.get_cell_by_coordinates(goal[0], goal[1])
        if not self._passable(start_cell) or not self._passable(goal_cell):
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
            cur_cell = self.maze.get_cell_by_coordinates(x, y)
            if cur_cell is None:
                continue

            for d in dirs:
                nxt = self.maze.get_neighbor_cell(cur_cell, d)
                if not self._passable(nxt):
                    continue
                nc = (nxt.x, nxt.y)
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

    def step(self, direction_value: str) -> Optional[RobotCell]:
        if direction_value == DirectionType.MEASURE_FORWARD.value:
            return self.robot.go_measure_forward()
        if direction_value == DirectionType.MEASURE_BACKWARD.value:
            return self.robot.go_measure_backward()
        if direction_value == DirectionType.MEASURE_LEFT.value:
            return self.robot.move_left()
        if direction_value == DirectionType.MEASURE_RIGHT.value:
            return self.robot.move_right()
        if direction_value == DirectionType.DIAG_MV.value:
            return self.robot.go_up_diag()
        if direction_value == DirectionType.DIAG_MN.value:
            return self.robot.go_down_diag()
        return None

    def process_current(self) -> None:
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


class MazeView(QGraphicsView):
    def __init__(self, app: "MainWindow"):
        super().__init__()
        self.app = app

    def mousePressEvent(self, event):
        if self.app.running:
            return
        pos = self.mapToScene(event.position().toPoint())
        x, y = self.app.scene_to_world(pos.x(), pos.y())
        if x is None:
            return
        if event.button() == Qt.LeftButton:
            self.app.editor.cycle_cell_type(x, y)
            self.app.redraw()
        elif event.button() == Qt.RightButton:
            self.app.editor.place_robot(x, y)
            self.app.redraw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("РоботМетеоролог — этап 1 (Qt)")

        self.cell_size = 44
        self.margin = 12

        self.maze = RobotMaze(width=10, length=8)
        self.editor = MazeEditor(self.maze)
        self.maze.initialize_maze(CellType.PLATFORM)
        self.editor.set_cell_type(9, 7, CellType.FINISH)
        self.editor.place_robot(0, 0)

        self.robot: Optional[RobotMeteorologist] = None
        self.runtime: Optional[MissionRuntime] = None

        self.running = False
        self.steps = 0

        self.scene = QGraphicsScene()
        self.view = MazeView(self)
        self.view.setScene(self.scene)

        self.status = QLabel("ЛКМ: тип | ПКМ: робот | Run/Step")
        self.status.setAlignment(Qt.AlignLeft)

        btn_run = QPushButton("Run")
        btn_step = QPushButton("Step")
        btn_reset = QPushButton("Reset")
        btn_demo = QPushButton("Demo")

        btn_run.clicked.connect(self.on_run)
        btn_step.clicked.connect(self.on_step)
        btn_reset.clicked.connect(self.on_reset)
        btn_demo.clicked.connect(self.on_demo)

        top = QWidget()
        layout = QVBoxLayout(top)
        layout.addWidget(self.view)

        controls = QHBoxLayout()
        controls.addWidget(btn_run)
        controls.addWidget(btn_step)
        controls.addWidget(btn_reset)
        controls.addWidget(btn_demo)
        controls.addStretch(1)

        layout.addLayout(controls)
        layout.addWidget(self.status)

        self.setCentralWidget(top)
        self.resize(self.view_width() + 40, self.view_height() + 120)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

        self.redraw()

    def view_width(self) -> int:
        return self.margin * 2 + self.maze.width * self.cell_size

    def view_height(self) -> int:
        return self.margin * 2 + self.maze.length * self.cell_size

    def world_to_scene(self, x: int, y: int) -> Tuple[float, float]:
        sx = self.margin + x * self.cell_size
        sy = self.margin + (self.maze.length - 1 - y) * self.cell_size
        return float(sx), float(sy)

    def scene_to_world(self, sx: float, sy: float) -> Tuple[Optional[int], Optional[int]]:
        x = int((sx - self.margin) // self.cell_size)
        y = int((sy - self.margin) // self.cell_size)
        if 0 <= x < self.maze.width and 0 <= y < self.maze.length:
            wy = self.maze.length - 1 - y
            return x, wy
        return None, None

    def redraw(self):
        self.scene.clear()
        self.scene.setSceneRect(QRectF(0, 0, self.view_width(), self.view_height()))

        for y in range(self.maze.length - 1, -1, -1):
            for x in range(self.maze.width):
                c = self.maze.get_cell_by_coordinates(x, y)
                if not c:
                    continue

                sx, sy = self.world_to_scene(x, y)
                rect = QGraphicsRectItem(sx, sy, self.cell_size, self.cell_size)
                rect.setPen(QPen(Qt.black))
                rect.setBrush(QBrush(self.color_for_cell(c.cell_type)))
                self.scene.addItem(rect)

                lab = self.label_for_cell(c.cell_type)
                if lab:
                    t = QGraphicsTextItem(lab)
                    t.setDefaultTextColor(Qt.black)
                    f = QFont()
                    f.setPointSize(12)
                    f.setBold(True)
                    t.setFont(f)
                    t.setPos(sx + self.cell_size * 0.34, sy + self.cell_size * 0.22)
                    self.scene.addItem(t)

                if c.has_robot:
                    r = self.cell_size * 0.28
                    cx = sx + self.cell_size / 2
                    cy = sy + self.cell_size / 2
                    circ = QGraphicsEllipseItem(cx - r, cy - r, 2 * r, 2 * r)
                    circ.setBrush(QBrush(Qt.black))
                    circ.setPen(QPen(Qt.black))
                    self.scene.addItem(circ)

        self.update_status()

    def color_for_cell(self, t: CellType):
        if t == CellType.PLATFORM:
            return Qt.white
        if t == CellType.SENSOR:
            return Qt.yellow
        if t == CellType.MEASURED:
            return Qt.green
        if t == CellType.STATION:
            return Qt.cyan
        if t == CellType.BARRIER:
            return Qt.darkGray
        if t == CellType.WINDOW:
            return Qt.magenta
        if t == CellType.FINISH:
            return Qt.red
        return Qt.white

    def label_for_cell(self, t: CellType) -> str:
        if t == CellType.PLATFORM:
            return "П"
        if t == CellType.SENSOR:
            return "Д"
        if t == CellType.MEASURED:
            return "З"
        if t == CellType.STATION:
            return "С"
        if t == CellType.BARRIER:
            return "Б"
        if t == CellType.WINDOW:
            return "О"
        if t == CellType.FINISH:
            return "Ф"
        return ""

    def update_status(self):
        robot_cell = None
        for y in range(self.maze.length):
            for x in range(self.maze.width):
                c = self.maze.get_cell_by_coordinates(x, y)
                if c and c.has_robot:
                    robot_cell = c
                    break
            if robot_cell:
                break
        rem = MazeInspector(self.maze).remaining_targets()
        if robot_cell:
            self.status.setText(
                f"Робот: ({robot_cell.x},{robot_cell.y}) {robot_cell.cell_type.name} | Осталось П/Д: {len(rem)} | Шаги: {self.steps}"
            )
        else:
            self.status.setText(f"Робот не поставлен | Осталось П/Д: {len(rem)} | Шаги: {self.steps}")

    def prepare_runtime(self):
        self.robot = RobotMeteorologist(self.maze)
        self.runtime = MissionRuntime(self.maze, self.robot)
        self.steps = 0

    def on_run(self):
        if self.running:
            return
        try:
            self.prepare_runtime()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        self.running = True
        self.timer.start(60)

    def on_step(self):
        if self.running:
            return
        try:
            if self.runtime is None:
                self.prepare_runtime()
            self.runtime.step()
            self.steps += 1
            self.redraw()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def tick(self):
        if not self.running:
            return
        try:
            if self.runtime is None:
                self.prepare_runtime()
            self.runtime.step()
            self.steps += 1
            if self.runtime.done:
                self.running = False
                self.timer.stop()
            self.redraw()
        except Exception as e:
            self.running = False
            self.timer.stop()
            QMessageBox.critical(self, "Ошибка", str(e))
            self.redraw()

    def on_reset(self):
        if self.running:
            return
        self.maze.initialize_maze(CellType.PLATFORM)
        self.editor = MazeEditor(self.maze)
        self.editor.set_cell_type(self.maze.width - 1, self.maze.length - 1, CellType.FINISH)
        self.editor.place_robot(0, 0)
        self.runtime = None
        self.steps = 0
        self.running = False
        self.redraw()

    def on_demo(self):
        if self.running:
            return
        self.maze = RobotMaze(width=10, length=8)
        self.editor = MazeEditor(self.maze)
        self.maze.initialize_maze(CellType.PLATFORM)

        self.editor.place_robot(0, 0)
        self.editor.set_cell_type(9, 7, CellType.FINISH)

        for x in range(2, 10):
            self.editor.set_cell_type(x, 3, CellType.BARRIER)

        self.editor.set_cell_type(4, 4, CellType.WINDOW)
        self.editor.set_cell_type(5, 5, CellType.WINDOW)

        self.editor.set_cell_type(1, 0, CellType.SENSOR)
        self.editor.set_cell_type(3, 1, CellType.SENSOR)
        self.editor.set_cell_type(6, 2, CellType.SENSOR)
        self.editor.set_cell_type(8, 6, CellType.SENSOR)

        self.editor.set_cell_type(2, 5, CellType.STATION)
        self.editor.set_cell_type(7, 5, CellType.STATION)

        self.runtime = None
        self.steps = 0
        self.running = False
        self.redraw()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
