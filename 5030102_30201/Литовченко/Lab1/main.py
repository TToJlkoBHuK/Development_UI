from enum import Enum
from typing import Optional, Iterator, List


class DirectionTypePanelDir(Enum):
    CHANNEL_NORTH = "ChannelNorth"
    CHANNEL_SOUTH = "ChannelSouth"
    CHANNEL_WEST = "ChannelWest"
    CHANNEL_EAST = "ChannelEast"
    DIAG_NW = "DiagNorthWest"
    DIAG_SE = "DiagSouthEast"


class CellTypePanel(Enum):
    FLOOR = 0x0
    PANEL = 0x1
    ACTIVE = 0x2
    SLUICE = 0x3
    WALL = 0x4
    BLOCK = 0x5
    FINISH = 0x6

    @classmethod
    def from_value(cls, value: int) -> 'CellTypePanel':
        base_value = value & 0x7
        for cell_type in cls:
            if cell_type.value == base_value:
                return cell_type
        return cls.FLOOR


class OperatorRobotCell:
    def __init__(self, x: int = 0, y: int = 0, cell_value: int = 0x0):
        self.x = x
        self.y = y
        self.has_robot = (cell_value & 0x8) != 0
        self.cell_type = CellTypePanel.from_value(cell_value)


class OperatorRobotMaze:
    def __init__(self, width: int = None, height: int = None, cells: List[List[int]] = None):
        self.width = width if width is not None else 0
        self.height = height if height is not None else 0
        self.cells = []

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

        for row_idx in range(self.height - 1, -1, -1):
            y = row_idx
            row = []
            for x in range(self.width):
                cell_value = cell_values[row_idx][x]
                cell = OperatorRobotCell(x, y, cell_value)
                row.append(cell)
            self.cells.append(row)

    def initialize_maze(self, cell_type: CellTypePanel = None):
        if cell_type is None:
            cell_type = CellTypePanel.FLOOR

        self.cells = []
        for list_y in range(self.height):
            y = self.height - 1 - list_y
            row = []
            for x in range(self.width):
                cell_value = cell_type.value
                cell = OperatorRobotCell(x, y, cell_value)
                row.append(cell)
            self.cells.append(row)

    def get_cell_by_coordinates(self, x: int, y: int) -> Optional[OperatorRobotCell]:
        if 0 <= x < self.width and 0 <= y < self.height:
            list_y = self.height - 1 - y
            return self.cells[list_y][x]
        return None

    def get_neighbor_cell(self, current_cell: OperatorRobotCell,
                          search_direction: DirectionTypePanelDir) -> Optional[OperatorRobotCell]:
        if not self.cells or not current_cell:
            return None

        x, y = current_cell.x, current_cell.y

        offsets = {
            DirectionTypePanelDir.CHANNEL_NORTH.value: (0, 1),
            DirectionTypePanelDir.CHANNEL_SOUTH.value: (0, -1),
            DirectionTypePanelDir.CHANNEL_WEST.value: (-1, 0),
            DirectionTypePanelDir.CHANNEL_EAST.value: (1, 0),
            DirectionTypePanelDir.DIAG_NW.value: (-1, 1),
            DirectionTypePanelDir.DIAG_SE.value: (1, -1),
        }

        dx, dy = offsets.get(search_direction.value, (0, 0))
        return self.get_cell_by_coordinates(x + dx, y + dy)

    def get_iterator(self) -> Iterator[OperatorRobotCell]:

        class SnakeIterator:
            def __init__(self, maze):
                self.maze = maze
                self.x = 0
                self.y = 0
                self.move_right = True
                self.done = False
                self.first = True

            def __iter__(self):
                return self

            def __next__(self):
                if self.done:
                    raise StopIteration

                if self.first:
                    self.first = False
                    cell = self.maze.get_cell_by_coordinates(self.x, self.y)
                    return cell

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

                cell = self.maze.get_cell_by_coordinates(self.x, self.y)
                return cell

        return SnakeIterator(self)


class OperatorRobot:

    def __init__(self, maze: OperatorRobotMaze = None):
        self.maze = maze
        self.current_cell = None

        if maze and maze.cells:
            for y in range(maze.height):
                for x in range(maze.width):
                    cell = maze.get_cell_by_coordinates(x, y)
                    if cell and cell.has_robot:
                        self.current_cell = cell
                        return

    def _move_to_cell(self, new_cell: Optional[OperatorRobotCell]) -> Optional[OperatorRobotCell]:
        if new_cell and new_cell.cell_type not in [CellTypePanel.WALL, CellTypePanel.BLOCK]:
            if self.current_cell:
                self.current_cell.has_robot = False
            self.current_cell = new_cell
            new_cell.has_robot = True
            return new_cell
        return None

    def channel_forward(self) -> Optional[OperatorRobotCell]:
        if self.maze and self.current_cell:
            new_cell = self.maze.get_neighbor_cell(
                self.current_cell, DirectionTypePanelDir.CHANNEL_NORTH
            )
            return self._move_to_cell(new_cell)
        return None

    def channel_backward(self) -> Optional[OperatorRobotCell]:
        if self.maze and self.current_cell:
            new_cell = self.maze.get_neighbor_cell(
                self.current_cell, DirectionTypePanelDir.CHANNEL_SOUTH
            )
            return self._move_to_cell(new_cell)
        return None

    def channel_left(self) -> Optional[OperatorRobotCell]:
        if self.maze and self.current_cell:
            new_cell = self.maze.get_neighbor_cell(
                self.current_cell, DirectionTypePanelDir.CHANNEL_WEST
            )
            return self._move_to_cell(new_cell)
        return None

    def channel_right(self) -> Optional[OperatorRobotCell]:
        if self.maze and self.current_cell:
            new_cell = self.maze.get_neighbor_cell(
                self.current_cell, DirectionTypePanelDir.CHANNEL_EAST
            )
            return self._move_to_cell(new_cell)
        return None

    def lift_diag(self) -> Optional[OperatorRobotCell]:
        if self.maze and self.current_cell:
            new_cell = self.maze.get_neighbor_cell(
                self.current_cell, DirectionTypePanelDir.DIAG_NW
            )
            return self._move_to_cell(new_cell)
        return None

    def descend_diag(self) -> Optional[OperatorRobotCell]:
        if self.maze and self.current_cell:
            new_cell = self.maze.get_neighbor_cell(
                self.current_cell, DirectionTypePanelDir.DIAG_SE
            )
            return self._move_to_cell(new_cell)
        return None

    def panel(self):
        if self.current_cell and self.current_cell.cell_type == CellTypePanel.PANEL:
            self.current_cell.cell_type = CellTypePanel.ACTIVE

    def floor(self):
        if self.current_cell and self.current_cell.cell_type == CellTypePanel.FLOOR:
            self.current_cell.cell_type = CellTypePanel.PANEL
