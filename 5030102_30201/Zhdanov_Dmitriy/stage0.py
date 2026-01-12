from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Iterator, Tuple
from collections import deque

class CellType(Enum):
    EMPTY = "empty"
    TEST_TUBE = "test_tube"
    ANALYZED = "analyzed"
    REAGENT = "reagent"
    BARRIER = "barrier"
    TRASH = "trash"
    FINISH = "finish"

class LabDirection(Enum):
    FORWARD = "forward"           # North
    BACKWARD = "backward"         # South
    LEFT = "left"                 # West
    RIGHT = "right"               # East
    UP_CORNER = "up_corner"       # NW
    DOWN_CORNER = "down_corner"   # SE

DIRECTION_DELTAS = {
    LabDirection.FORWARD.value: (0, 1),
    LabDirection.BACKWARD.value: (0, -1),
    LabDirection.LEFT.value: (-1, 0),
    LabDirection.RIGHT.value: (1, 0),
    LabDirection.UP_CORNER.value: (-1, 1),
    LabDirection.DOWN_CORNER.value: (1, -1),
}

@dataclass
class RobotCell:
    is_robot: bool
    cell_type: CellType
    x: int = 0
    y: int = 0

    def __repr__(self) -> str:
        return f"<Cell ({self.x},{self.y}) {self.cell_type.name}{' [R]' if self.is_robot else ''}>"

class LabyrinthRobot:
    def __init__(self, width: int, height: int,
                 cells: Optional[List[List[RobotCell]]] = None):
        self.width = width
        self.height = height
        if cells is None:
            self.cells: List[List[RobotCell]] = [
                [RobotCell(False, CellType.EMPTY, x, y) for x in range(width)]
                for y in range(height)
            ]
        else:
            self.cells = cells
            for y, row in enumerate(self.cells):
                for x, cell in enumerate(row):
                    cell.x = x
                    cell.y = y

    def get_neighbor_cell(self, current_cell: RobotCell, direction_value: str) -> Optional[RobotCell]:
        dx, dy = DIRECTION_DELTAS[direction_value]
        nx, ny = current_cell.x + dx, current_cell.y + dy
        if 0 <= nx < self.width and 0 <= ny < self.height:
            return self.cells[ny][nx]
        return None

    def get_iterator(self) -> Iterator[RobotCell]:
        return SnakeIteratorLab(self)

    def initialize_labyrinth(self, default_cell_type: CellType) -> None:
        for row in self.cells:
            for cell in row:
                cell.cell_type = default_cell_type
                cell.is_robot = False

    def all_cells(self) -> List[RobotCell]:
        return [cell for row in self.cells for cell in row]

class SnakeIteratorLab:
    def __init__(self, maze: LabyrinthRobot):
        self.maze = maze
        self.x = 0
        self.y = 0
        self.moving_right = True
        self._finished = False

    def __iter__(self) -> "SnakeIteratorLab":
        return self

    def __next__(self) -> RobotCell:
        if self._finished:
            raise StopIteration

        cell = self.maze.cells[self.y][self.x]

        if self.moving_right:
            if self.x < self.maze.width - 1:
                self.x += 1
            else:
                if self.y == self.maze.height - 1:
                    self._finished = True
                else:
                    self.y += 1
                    self.moving_right = False
        else:
            if self.x > 0:
                self.x -= 1
            else:
                if self.y == self.maze.height - 1:
                    self._finished = True
                else:
                    self.y += 1
                    self.moving_right = True

        return cell

class RobotLabAssistant:
    def __init__(self, labyrinth: LabyrinthRobot):
        self.labyrinth = labyrinth
        self.current_cell: RobotCell = self._find_robot_cell()

    def _find_robot_cell(self) -> RobotCell:
        for row in self.labyrinth.cells:
            for cell in row:
                if cell.is_robot:
                    return cell
        cell = self.labyrinth.cells[0][0]
        cell.is_robot = True
        return cell

    def _can_enter(self, cell: RobotCell) -> bool:
        return cell.cell_type not in {CellType.BARRIER, CellType.TRASH}

    def _step(self, direction: LabDirection) -> Optional[RobotCell]:
        neighbor = self.labyrinth.get_neighbor_cell(self.current_cell, direction.value)
        if neighbor is None or not self._can_enter(neighbor):
            return None
        self.current_cell.is_robot = False
        neighbor.is_robot = True
        self.current_cell = neighbor
        return neighbor

    def move_to_test_tube(self) -> Optional[RobotCell]:
        return self._step(LabDirection.FORWARD)

    def move_back_from_table(self) -> Optional[RobotCell]:
        return self._step(LabDirection.BACKWARD)

    def move_left(self) -> Optional[RobotCell]:
        return self._step(LabDirection.LEFT)

    def move_right(self) -> Optional[RobotCell]:
        return self._step(LabDirection.RIGHT)

    def move_up(self) -> Optional[RobotCell]:
        return self._step(LabDirection.UP_CORNER)

    def move_down(self) -> Optional[RobotCell]:
        return self._step(LabDirection.DOWN_CORNER)

    def handle_test_tube(self) -> None:
        if self.current_cell.cell_type == CellType.TEST_TUBE:
            self.current_cell.cell_type = CellType.ANALYZED

    def handle_empty(self) -> None:
        if self.current_cell.cell_type == CellType.EMPTY:
            self.current_cell.cell_type = CellType.TEST_TUBE

    def _find_path_to(self, target: RobotCell) -> Optional[List[LabDirection]]:
        start = (self.current_cell.x, self.current_cell.y)
        goal = (target.x, target.y)
        if start == goal:
            return []

        directions = list(LabDirection)
        visited = set()
        q = deque()
        q.append((start, []))
        visited.add(start)

        while q:
            (cx, cy), path = q.popleft()
            for d in directions:
                dx, dy = DIRECTION_DELTAS[d.value]
                nx, ny = cx + dx, cy + dy
                if not (0 <= nx < self.labyrinth.width and 0 <= ny < self.labyrinth.height):
                    continue
                cell = self.labyrinth.cells[ny][nx]
                if (nx, ny) != goal and not self._can_enter(cell):
                    continue
                pos = (nx, ny)
                if pos in visited:
                    continue
                new_path = path + [d]
                if pos == goal:
                    return new_path
                visited.add(pos)
                q.append((pos, new_path))
        return None

    def _follow_path(self, path: List[LabDirection]) -> bool:
        for d in path:
            moved = self._step(d)
            if moved is None:
                return False
        return True

    def _process_current_cell(self) -> None:
        if self.current_cell.cell_type == CellType.TEST_TUBE:
            self.handle_test_tube()
        elif self.current_cell.cell_type == CellType.EMPTY:
            self.handle_empty()

    def run_full_experiment(self) -> None:
        for cell in self.labyrinth.get_iterator():
            if cell.cell_type not in (CellType.TEST_TUBE, CellType.EMPTY):
                continue
            path = self._find_path_to(cell)
            if path is None:
                continue
            if not self._follow_path(path):
                continue
            self._process_current_cell()

        finish_cell: Optional[RobotCell] = None
        for c in self.labyrinth.all_cells():
            if c.cell_type == CellType.FINISH:
                finish_cell = c
                break
        if finish_cell is None:
            return
        path_to_finish = self._find_path_to(finish_cell)
        if path_to_finish:
            self._follow_path(path_to_finish)
