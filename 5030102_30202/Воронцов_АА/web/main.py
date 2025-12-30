from __future__ import annotations

from enum import Enum
from typing import List, Iterator, Optional


# =========================
# Enums
# =========================

class HydroNetCellType(Enum):
    Water = 0
    Shore = 1
    Sample = 2
    Network = 3
    Barrier = 4
    Finish = 5
    Channel = 6


class HydroMovementType(Enum):
    SwimForward = 0
    SwimBackward = 1
    MoveLeft = 2
    MoveRight = 3
    DiagUpLeft = 4
    DiagDownRight = 5


class BasicDirectionType(Enum):
    North = 0
    South = 1
    West = 2
    East = 3
    NorthWest = 4
    SouthEast = 5


# =========================
# Direction Mappings
# =========================

SIDE_TO_DIRECTION = {
    BasicDirectionType.North: HydroMovementType.SwimForward,
    BasicDirectionType.South: HydroMovementType.SwimBackward,
    BasicDirectionType.West: HydroMovementType.MoveLeft,
    BasicDirectionType.East: HydroMovementType.MoveRight,
    BasicDirectionType.NorthWest: HydroMovementType.DiagUpLeft,
    BasicDirectionType.SouthEast: HydroMovementType.DiagDownRight,
}

DIRECTION_TO_OFFSET = {
    HydroMovementType.SwimForward: (0, 1),
    HydroMovementType.SwimBackward: (0, -1),
    HydroMovementType.MoveLeft: (-1, 0),
    HydroMovementType.MoveRight: (1, 0),
    HydroMovementType.DiagUpLeft: (-1, 1),
    HydroMovementType.DiagDownRight: (1, -1),
}

# =========================
# Cell
# =========================

class HydroCell:
    def __init__(
        self,
        cell_type: Optional[HydroNetCellType] = None,
        is_robot_cell: bool = False,
        x: int = 0,
        y: int = 0,
    ) -> None:
        self.cell_type = cell_type
        self.is_robot_cell = is_robot_cell
        self.x = x
        self.y = y


# =========================
# Maze
# =========================

class HydroMaze:
    def __init__(
        self,
        width: int = 0,
        height: int = 0,
        cells: Optional[List[List[HydroCell]]] = None,
    ) -> None:
        self.width = width
        self.height = height
        self.cells = cells or []

    def _set_coordinates(self) -> None:
        for y, row in enumerate(self.cells):
            for x, cell in enumerate(row):
                cell.x = x
                cell.y = y

    def GetNeighborCell(
        self,
        current_cell: HydroCell,
        search_direction: HydroMovementType,
    ) -> Optional[HydroCell]:
        dx, dy = DIRECTION_TO_OFFSET[search_direction]
        nx = current_cell.x + dx
        ny = current_cell.y + dy

        if not (0 <= nx < self.width and 0 <= ny < self.height):
            return None

        neighbor = self.cells[ny][nx]
        if neighbor.cell_type in (
            HydroNetCellType.Barrier,
            HydroNetCellType.Channel,
        ):
            return None

        return neighbor

    def GetIterator(self) -> Iterator[HydroCell]:
        if not self.cells:
            return iter(())

        self._set_coordinates()

        x = 0
        y = 0
        direction = 1  # 1 = right, -1 = left

        while True:
            cell = self.cells[y][x]
            # Skip barriers and channels - don't yield them
            if cell.cell_type not in (
                HydroNetCellType.Barrier,
                HydroNetCellType.Channel,
            ):
                yield cell

            if direction == 1:
                if x == self.width - 1:
                    if y == self.height - 1:
                        break
                    y += 1
                    direction = -1
                else:
                    x += 1
            else:
                if x == 0:
                    if y == self.height - 1:
                        break
                    y += 1
                    direction = 1
                else:
                    x -= 1

    def GetIteratorFromBottomLeft(self) -> Iterator[HydroCell]:
        """
        Get an iterator starting from bottom-left corner moving to top-right
        Получить итератор, начиная с левого нижнего угла к правому верхнему
        """
        if not self.cells:
            return iter(())

        self._set_coordinates()

        x = 0
        y = self.height - 1
        direction = 1  # 1 = right, -1 = left

        while True:
            cell = self.cells[y][x]
            # Skip barriers and channels - don't yield them
            if cell.cell_type not in (
                HydroNetCellType.Barrier,
                HydroNetCellType.Channel,
            ):
                yield cell

            # Move right or left depending on direction
            if direction == 1:  # Moving right
                if x == self.width - 1:  # Reached right edge
                    if y == 0:  # Also at top
                        break
                    y -= 1  # Move up
                    direction = -1  # Change to moving left
                else:
                    x += 1  # Continue right
            else:  # Moving left
                if x == 0:  # Reached left edge
                    if y == 0:  # Also at top
                        break
                    y -= 1  # Move up
                    direction = 1  # Change to moving right
                else:
                    x -= 1  # Continue left

    def GetSmartIterator(self) -> Iterator[HydroCell]:
        """
        Get an iterator that avoids barriers and channels using BFS
        Получить итератор, который избегает преград и каналов, используя BFS
        """
        if not self.cells:
            return iter(())

        self._set_coordinates()

        visited = set()
        queue = [(0, 0)]
        visited.add((0, 0))

        while queue:
            x, y = queue.pop(0)
            cell = self.cells[y][x]
            yield cell

            # Try all 4 directions (up, down, left, right)
            for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Check bounds
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                
                # Skip if already visited
                if (nx, ny) in visited:
                    continue
                
                neighbor = self.cells[ny][nx]
                # Skip barriers and channels
                if neighbor.cell_type in (
                    HydroNetCellType.Barrier,
                    HydroNetCellType.Channel,
                ):
                    continue
                
                visited.add((nx, ny))
                queue.append((nx, ny))

    def InitializeMaze(
        self,
        cell_type: HydroNetCellType,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

        self.cells = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(HydroCell(cell_type, False, x, y))
            self.cells.append(row)


# =========================
# Robot
# =========================

class HydroRobot:
    def __init__(self, maze: Optional[HydroMaze] = None) -> None:
        self.maze = maze
        self._current_cell: Optional[HydroCell] = None

    @property
    def current_cell(self) -> Optional[HydroCell]:
        if self._current_cell is None and self.maze:
            for row in self.maze.cells:
                for cell in row:
                    if cell.is_robot_cell:
                        self._current_cell = cell
                        return cell
        return self._current_cell

    def _set_current_cell(
        self, cell: Optional[HydroCell]
    ) -> Optional[HydroCell]:
        if cell is None:
            return None
        if self._current_cell:
            self._current_cell.is_robot_cell = False
        self._current_cell = cell
        cell.is_robot_cell = True
        return cell

    def _move(self, direction: HydroMovementType) -> Optional[HydroCell]:
        if not self.maze or not self.current_cell:
            return None
        next_cell = self.maze.GetNeighborCell(
            self.current_cell, direction
        )
        return self._set_current_cell(next_cell)

    # Movement methods
    def SwimForward(self):
        return self._move(HydroMovementType.SwimForward)

    def MoveBackward(self):
        return self._move(HydroMovementType.SwimBackward)

    def MoveLeft(self):
        return self._move(HydroMovementType.MoveLeft)

    def MoveRight(self):
        return self._move(HydroMovementType.MoveRight)

    def MoveUp(self):
        return self._move(HydroMovementType.DiagUpLeft)

    def MoveDown(self):
        return self._move(HydroMovementType.DiagDownRight)

    # Specializations
    def Water(self) -> None:
        if self.current_cell and self.current_cell.cell_type == HydroNetCellType.Water:
            self.current_cell.cell_type = HydroNetCellType.Sample

    def Shore(self) -> None:
        if self.current_cell and self.current_cell.cell_type == HydroNetCellType.Shore:
            self.current_cell.cell_type = HydroNetCellType.Water