

from enum import Enum
from typing import Optional, Iterator, List

DEBUG = False

class DirectionType(Enum):
    FORWARD = "Forward"
    BACKWARD = "Backward"
    LEFT = "Left"
    RIGHT = "Right"
    DIAG_UP_LEFT = "DiagUpLeft"
    DIAG_DOWN_LEFT = "DiagDownLeft"


class CellType(Enum):
    PATH = 0x0
    ORE = 0x1
    PROCESSED = 0x2
    SHAFT = 0x3
    DANGEROUS = 0x4
    FINISH = 0x5
    MINE = 0x6

    @classmethod
    def from_value(cls, value: int) -> 'CellType':
        base_value = value & 0x7
        for ct in cls:
            if ct.value == base_value:
                return ct
        return cls.PATH


class RobotCell:
    def __init__(self, x: int = 0, y: int = 0, cell_value: int = 0x0):
        self.x = x
        self.y = y
        self.has_robot = (cell_value & 0x8) != 0
        self.cell_type = CellType.from_value(cell_value)

    def set_type(self, new_type: CellType):
        self.cell_type = new_type

    def mark_robot(self, flag: bool):
        self.has_robot = bool(flag)

    def get_value(self) -> int:
        return self.cell_type.value | (0x8 if self.has_robot else 0)

    def __repr__(self):
        return f"RobotCell(x={self.x},y={self.y},type={self.cell_type},robot={self.has_robot})"


class RobotMaze:
    def __init__(self, width: int = None, height: int = None, cells: List[List[int]] = None):
        self.width = width if width is not None else 0
        self.height = height if height is not None else 0
        self.cells: List[List[RobotCell]] = []
        self._processing_iterator = None

        if cells is not None:
            self.load_from_values(cells)
        elif width is not None and height is not None:
            self.initialize_maze()

    def load_from_values(self, cell_values: List[List[int]]):
        if not cell_values:
            self.height = 0
            self.width = 0
            self.cells = []
            return

        self.height = len(cell_values)
        self.width = len(cell_values[0]) if self.height > 0 else 0

        self.cells = []
        for y in range(self.height - 1, -1, -1):
            row = []
            for x in range(self.width):
                cv = cell_values[y][x]
                row.append(RobotCell(x, y, cv))
            self.cells.append(row)

        # self._processing_iterator = self.get_processing_iterator !!!!!!!!!!!!!!!!!!!!!!!!!!!

    def get_processing_iterator(self):

        class ProcessingIterator:
            def __init__(self, maze):
                self.maze = maze
                self.x = 0
                self.y = 0
                self.move_right = True
                self.started = False
                self.done = False

            def __iter__(self):
                return self

            def __next__(self):
                if self.done:
                    raise StopIteration

                if not self.started:
                    self.started = True
                    return self.maze.get_cell_by_coordinates(self.x, self.y)

                if self.move_right:
                    if self.x < self.maze.width - 1:
                        self.x += 1
                    else:
                        if self.y < self.maze.height - 1:
                            self.y += 1
                            self.move_right = False
                        else:
                            self.done = True
                else:
                    if self.x > 0:
                        self.x -= 1
                    else:
                        if self.y < self.maze.height - 1:
                            self.y += 1
                            self.move_right = True
                        else:
                            self.done = True

                if self.done:
                    raise StopIteration

                return self.maze.get_cell_by_coordinates(self.x, self.y)

        return ProcessingIterator(self)

    def get_next_processing_cell(self):
        if self._processing_iterator is None:
            self._processing_iterator = self.get_processing_iterator()

        try:
            return next(self._processing_iterator)
        except StopIteration:
            return None

    def initialize_maze(self, cell_type: CellType = None):
        if cell_type is None:
            cell_type = CellType.PATH
        self.cells = []
        for y in range(self.height - 1, -1, -1):
            row = [RobotCell(x, y, cell_type.value) for x in range(self.width)]
            self.cells.append(row)

    def get_cell_by_coordinates(self, x: int, y: int) -> Optional[RobotCell]:
        if 0 <= x < self.width and 0 <= y < self.height:
            row_idx = self.height - 1 - y
            return self.cells[row_idx][x]
        return None

    def to_values(self) -> List[List[int]]:
        out = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                cell = self.get_cell_by_coordinates(x, y)
                row.append(cell.get_value() if cell else 0)
            out.append(row)
        return out

    def get_neighbor_cell(self, current_cell: RobotCell, search_direction_value: str) -> Optional[RobotCell]:
        if not current_cell:
            return None

        x, y = current_cell.x, current_cell.y

        offsets = {
            DirectionType.FORWARD.value: (0, 1),
            DirectionType.BACKWARD.value: (0, -1),
            DirectionType.LEFT.value: (-1, 0),
            DirectionType.RIGHT.value: (1, 0),
            DirectionType.DIAG_UP_LEFT.value: (-1, 1),
            DirectionType.DIAG_DOWN_LEFT.value: (1, -1),
        }

        dx, dy = offsets.get(search_direction_value, (0, 0))
        tx, ty = x + dx, y + dy

        return self.get_cell_by_coordinates(tx, ty)

    def get_iterator(self):
        return self.get_processing_iterator()


class RobotMiner:
    def __init__(self, maze: RobotMaze = None):
        self.maze = maze
        self.current_cell: Optional[RobotCell] = None

        if maze:
            for y in range(maze.height):
                for x in range(maze.width):
                    cell = maze.get_cell_by_coordinates(x, y)
                    if cell and cell.has_robot:
                        self.current_cell = cell
                        if DEBUG:
                            print(f"[__init__] Found robot at ({x},{y}) -> {cell}")
                        return

            if DEBUG:
                print("[__init__] No robot found in maze")

    def _move_to_cell(self, new_cell: Optional[RobotCell]) -> Optional[RobotCell]:
        if new_cell is None:
            return None

        if new_cell.cell_type in (CellType.SHAFT, CellType.DANGEROUS):
            return None

        if new_cell.has_robot and new_cell != self.current_cell:
            return None

        if self.current_cell:
            self.current_cell.mark_robot(False)

        self.current_cell = new_cell
        new_cell.mark_robot(True)

        return new_cell

    def go_forward(self) -> Optional[RobotCell]:
        if self.maze and self.current_cell:
            neighbor = self.maze.get_neighbor_cell(self.current_cell, DirectionType.FORWARD.value)
            return self._move_to_cell(neighbor)
        return None

    def go_backward(self) -> Optional[RobotCell]:
        if self.maze and self.current_cell:
            neighbor = self.maze.get_neighbor_cell(self.current_cell, DirectionType.BACKWARD.value)
            return self._move_to_cell(neighbor)
        return None

    def move_left(self) -> Optional[RobotCell]:
        if self.maze and self.current_cell:
            neighbor = self.maze.get_neighbor_cell(self.current_cell, DirectionType.LEFT.value)
            return self._move_to_cell(neighbor)
        return None

    def move_right(self) -> Optional[RobotCell]:
        if self.maze and self.current_cell:
            neighbor = self.maze.get_neighbor_cell(self.current_cell, DirectionType.RIGHT.value)
            return self._move_to_cell(neighbor)
        return None

    def move_up_left(self) -> Optional[RobotCell]:
        if self.maze and self.current_cell:
            neighbor = self.maze.get_neighbor_cell(self.current_cell, DirectionType.DIAG_UP_LEFT.value)
            return self._move_to_cell(neighbor)
        return None

    def move_down_left(self) -> Optional[RobotCell]:
        if self.maze and self.current_cell:
            neighbor = self.maze.get_neighbor_cell(self.current_cell, DirectionType.DIAG_DOWN_LEFT.value)
            return self._move_to_cell(neighbor)
        return None

    def process_ore(self):
        if self.current_cell and self.current_cell.cell_type == CellType.ORE:
            if DEBUG:
                print(f"[process_ore] at ({self.current_cell.x},{self.current_cell.y}) ORE -> PROCESSED")
            self.current_cell.set_type(CellType.PROCESSED)

    def process_path(self):
        if self.current_cell and self.current_cell.cell_type == CellType.PATH:
            if DEBUG:
                print(f"[process_path] at ({self.current_cell.x},{self.current_cell.y}) PATH -> ORE")
            self.current_cell.set_type(CellType.ORE)
