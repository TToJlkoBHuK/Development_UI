import enum
from typing import Iterator, Optional, List

# ================= ENUMS =================
class CellType(enum.Enum):
    RASCOP = "Раскоп"
    ARTEFACT = "Артефакт"
    PESOC = "Песок"
    KLADKA = "Кладка"
    BARRIER = "Барьер"
    FINISH = "Финиш"
    RUINS = "Руины"

class Direction(enum.Enum):
    STEP_RASCOP = "ШагРаскоп"
    STEP_BACK = "ШагНазад"
    STEP_LEFT = "ШагВлево"
    STEP_RIGHT = "ШагВправо"
    DIAG_ARCH_V = "ДиагАрхВ"
    DIAG_ARCH_N = "ДиагАрхН"

# ================= CLASSES =================

class RobotCell:
    def __init__(self, cell_type: CellType, x: int = 0, y: int = 0):
        self.cell_type: CellType = cell_type
        self.has_robot: bool = False
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Cell({self.x},{self.y}):{self.cell_type.name}"

class RobotLabyrinth:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # Инициализируем 2D массив.
        self.cells: List[List[RobotCell]] = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(RobotCell(CellType.RUINS, x, y))
            self.cells.append(row)

    def initialize_labyrinth(self, default_type: CellType) -> None:
        """
        Инициализация лабиринта дефолтным типом.
        """
        for row in self.cells:
            for cell in row:
                cell.cell_type = default_type
                cell.has_robot = False

    def get_neighbor_cell(self, current_cell: RobotCell, direction_value: str) -> Optional[RobotCell]:
        """
        Метод: ПолучитьСоседнююЯчейку.
        Рассчитывает координаты соседа.
        """
        x, y = current_cell.x, current_cell.y
        dx, dy = 0, 0
        
        if direction_value == Direction.STEP_RIGHT.value:
            dx = 1
        elif direction_value == Direction.STEP_LEFT.value:
            dx = -1
        #Подняться = Влево-Вверх (-1, 1)
        elif direction_value == Direction.DIAG_ARCH_V.value:
            dx = -1
            dy = 1 
        #ШагНазад = Вниз (0, -1)
        elif direction_value == Direction.STEP_BACK.value:
            dy = -1 
        #Спуститься = Вправо-Вниз (1, -1)
        elif direction_value == Direction.DIAG_ARCH_N.value:
            dx = 1
            dy = -1 
        #ШагРаскоп = Вперед/Вверх (0, 1)
        elif direction_value == Direction.STEP_RASCOP.value:
            dy = 1

        nx, ny = x + dx, y + dy

        # Проверка границ
        if 0 <= nx < self.width and 0 <= ny < self.height:
            return self.cells[ny][nx]
        return None

    def get_iterator(self) -> Iterator[RobotCell]:
        return SnakeIterator(self)

class SnakeIterator:
    """
    Итератор для обхода лабиринта змейкой.
    """
    def __init__(self, maze: RobotLabyrinth):
        self.maze = maze
        self.x = 0
        self.y = 0
        self.moving_right = True
        self.finished = False

    def __iter__(self):
        return self

    def __next__(self) -> RobotCell:
        if self.finished:
            raise StopIteration
        
        if self.y >= self.maze.height:
             self.finished = True
             raise StopIteration

        cell = self.maze.cells[self.y][self.x]

        if self.moving_right:
            if self.x < self.maze.width - 1:
                self.x += 1
            else:
                if self.y < self.maze.height - 1:
                    self.y += 1
                    self.moving_right = False
                else:
                    self.finished = True
        else:
            if self.x > 0:
                self.x -= 1
            else:
                if self.y < self.maze.height - 1:
                    self.y += 1
                    self.moving_right = True
                else:
                    self.finished = True
        
        return cell

class RobotArcheolog:
    def __init__(self, labyrinth: RobotLabyrinth):
        self.labyrinth = labyrinth
        self.current_cell: Optional[RobotCell] = self._find_robot()
        
        # Fallback: Если робот не найден, ставим в (0,0)
        if self.current_cell is None:
            if self.labyrinth.height > 0 and self.labyrinth.width > 0:
                start = self.labyrinth.cells[0][0]
                start.has_robot = True
                self.current_cell = start

    def _find_robot(self) -> Optional[RobotCell]:
        for row in self.labyrinth.cells:
            for cell in row:
                if cell.has_robot:
                    return cell
        return None

    def _move_robot(self, direction_value: str) -> Optional[RobotCell]:
        if not self.current_cell:
            return None
        
        target = self.labyrinth.get_neighbor_cell(self.current_cell, direction_value)
        
        if target is None:
            return None
            
        if target.cell_type in (CellType.KLADKA, CellType.BARRIER):
            return None
            
        self.current_cell.has_robot = False
        target.has_robot = True
        self.current_cell = target
        
        return target

    def podkopat(self) -> Optional[RobotCell]:
        return self._move_robot(Direction.STEP_RASCOP.value)

    def otstupit(self) -> Optional[RobotCell]:
        return self._move_robot(Direction.STEP_BACK.value)

    def smestitsia_vlevo(self) -> Optional[RobotCell]:
        return self._move_robot(Direction.STEP_LEFT.value)

    def smestitsia_vpravo(self) -> Optional[RobotCell]:
        return self._move_robot(Direction.STEP_RIGHT.value)

    def podniatsia(self) -> Optional[RobotCell]:
        return self._move_robot(Direction.DIAG_ARCH_V.value)

    def spustitsia(self) -> Optional[RobotCell]:
        return self._move_robot(Direction.DIAG_ARCH_N.value)

    def dig(self) -> None:
        if self.current_cell and self.current_cell.cell_type == CellType.RASCOP:
            self.current_cell.cell_type = CellType.ARTEFACT

    def clear_sand(self) -> None:
        if self.current_cell and self.current_cell.cell_type == CellType.PESOC:
            self.current_cell.cell_type = CellType.RASCOP
    
    def process_current_cell(self) -> None:
        if not self.current_cell:
            return
        while self.current_cell.cell_type == CellType.PESOC:
            self.clear_sand()
        if self.current_cell.cell_type == CellType.RASCOP:
            self.dig()

    def run_mission(self):
        pass
