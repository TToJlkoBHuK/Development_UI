import enum
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import Iterator, Optional, List
import time

class CellType(enum.Enum):
    RASCOP = "Раскоп"
    ARTEFACT = "Артефакт"
    PESOC = "Песок"
    KLADKA = "Кладка"
    BARRIER = "Барьер"
    FINISH = "Финиш"
    RUINS = "Руины"

class Direction(enum.Enum):
    STEP_RASCOP = "ШагРаскоп"     # Вверх (dy=1)
    STEP_BACK = "ШагНазад"        # Вниз (dy=-1)
    STEP_LEFT = "ШагВлево"        # Влево (dx=-1)
    STEP_RIGHT = "ШагВправо"      # Вправо (dx=1)
    DIAG_ARCH_V = "ДиагАрхВ"      # Влево-Вверх (dx=-1, dy=1)
    DIAG_ARCH_N = "ДиагАрхН"      # Вправо-Вниз (dx=1, dy=-1)

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
        self.cells: List[List[RobotCell]] = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(RobotCell(CellType.RUINS, x, y))
            self.cells.append(row)

    def get_neighbor_cell(self, current_cell: RobotCell, direction_value: str) -> Optional[RobotCell]:
        x, y = current_cell.x, current_cell.y
        dx, dy = 0, 0
        
        if direction_value == Direction.STEP_RIGHT.value:
            dx = 1
        elif direction_value == Direction.STEP_LEFT.value:
            dx = -1
        elif direction_value == Direction.DIAG_ARCH_V.value:
            # Влево-Вверх
            dx = -1
            dy = 1 
        elif direction_value == Direction.STEP_BACK.value:
            # Вниз
            dy = -1 
        elif direction_value == Direction.DIAG_ARCH_N.value:
            # Вправо-Вниз
            dx = 1
            dy = -1 
        elif direction_value == Direction.STEP_RASCOP.value:
            # Вверх
            dy = 1

        nx, ny = x + dx, y + dy

        if 0 <= nx < self.width and 0 <= ny < self.height:
            return self.cells[ny][nx]
        return None

class RobotArcheolog:
    def __init__(self, labyrinth: RobotLabyrinth):
        self.labyrinth = labyrinth
        self.current_cell: Optional[RobotCell] = None
        for row in self.labyrinth.cells:
            for cell in row:
                if cell.has_robot:
                    self.current_cell = cell
                    break
        if not self.current_cell:
            self.labyrinth.cells[0][0].has_robot = True
            self.current_cell = self.labyrinth.cells[0][0]

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

    def podkopat(self): return self._move_robot(Direction.STEP_RASCOP.value)
    def otstupit(self): return self._move_robot(Direction.STEP_BACK.value)
    def smestitsia_vlevo(self): return self._move_robot(Direction.STEP_LEFT.value)
    def smestitsia_vpravo(self): return self._move_robot(Direction.STEP_RIGHT.value)
    def podniatsia(self): return self._move_robot(Direction.DIAG_ARCH_V.value)
    def spustitsia(self): return self._move_robot(Direction.DIAG_ARCH_N.value)

    def dig(self):
        if self.current_cell and self.current_cell.cell_type == CellType.RASCOP:
            self.current_cell.cell_type = CellType.ARTEFACT
    def clear_sand(self):
        if self.current_cell and self.current_cell.cell_type == CellType.PESOC:
            self.current_cell.cell_type = CellType.RASCOP
    def process(self):
        while self.current_cell.cell_type == CellType.PESOC:
            self.clear_sand()
        if self.current_cell.cell_type == CellType.RASCOP:
            self.dig()

class ArcheologyApp:
    def __init__(self, root, width=4, height=3):
        self.root = root
        self.root.title("Робот-Археолог (Tkinter)")

        self.maze = RobotLabyrinth(width, height)
        self._setup_demo_map()
        self.robot = RobotArcheolog(self.maze)
        self.move_direction = "right"
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas_size = 60
        self.canvas_width = width * self.canvas_size
        self.canvas_height = height * self.canvas_size
        self.canvas = tk.Canvas(main_frame, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack(side=tk.LEFT, padx=10)

        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="⬆ Подкопать (Вверх)", command=lambda: self.manual_step("podkopat")).grid(row=0, column=1)
        tk.Button(btn_frame, text="⬅ Влево", command=lambda: self.manual_step("left")).grid(row=1, column=0)
        tk.Button(btn_frame, text="Действие", command=lambda: self.manual_step("process")).grid(row=1, column=1)
        tk.Button(btn_frame, text="Вправо ➡", command=lambda: self.manual_step("right")).grid(row=1, column=2)
        tk.Button(btn_frame, text="⬇ Назад", command=lambda: self.manual_step("back")).grid(row=2, column=1)
        
        tk.Label(control_frame, text="Диагонали:").pack(pady=(10,0))
        diag_frame = tk.Frame(control_frame)
        diag_frame.pack()
        tk.Button(diag_frame, text="↖ Подняться", command=lambda: self.manual_step("up_diag")).pack(side=tk.LEFT)
        tk.Button(diag_frame, text="↘ Спуститься", command=lambda: self.manual_step("down_diag")).pack(side=tk.LEFT)

        tk.Button(control_frame, text="▶ АВТО-ШАГ (Змейка)", bg="lightgreen", command=self.auto_step).pack(pady=20, fill=tk.X)

        self.log_area = scrolledtext.ScrolledText(control_frame, width=30, height=15)
        self.log_area.pack(pady=10)

        self.draw_grid()
        self.log("Система готова. Робот в (0,0)")

    def _setup_demo_map(self):
        # Y=2: [РУИНЫ,  ПЕСОК,  РУИНЫ,  ФИНИШ]
        # Y=1: [РАСКОП, РУИНЫ,  РАСКОП, ПЕСОК]
        # Y=0: [ПЕСОК,  РАСКОП, РУИНЫ,  ПЕСОК]
        flat_data = [
            CellType.RUINS, CellType.PESOC, CellType.RUINS, CellType.FINISH, # Y=2
            CellType.RASCOP, CellType.RUINS, CellType.RASCOP, CellType.PESOC, # Y=1
            CellType.PESOC, CellType.RASCOP, CellType.RUINS, CellType.PESOC   # Y=0
        ]

        rows = [flat_data[i:i+4] for i in range(0, len(flat_data), 4)]
        
        for y_idx, row_data in enumerate(rows):
            actual_y = (3 - 1) - y_idx # 2, 1, 0
            for x_idx, c_type in enumerate(row_data):
                self.maze.cells[actual_y][x_idx].cell_type = c_type

    def draw_grid(self):
        self.canvas.delete("all")
        h = self.maze.height
        w = self.maze.width
        sz = self.canvas_size

        for y in range(h):
            for x in range(w):
                cell = self.maze.cells[y][x]

                gui_y = (h - 1 - y) * sz
                gui_x = x * sz
                
                color = "white"
                if cell.cell_type == CellType.PESOC: color = "#F4A460"
                elif cell.cell_type == CellType.RASCOP: color = "#8B4513"
                elif cell.cell_type == CellType.ARTEFACT: color = "gold"
                elif cell.cell_type == CellType.RUINS: color = "gray"
                elif cell.cell_type == CellType.FINISH: color = "red"

                self.canvas.create_rectangle(gui_x, gui_y, gui_x+sz, gui_y+sz, fill=color, outline="black")
                self.canvas.create_text(gui_x+sz/2, gui_y+sz/2, text=f"{x},{y}", font=("Arial", 8))

                if cell.has_robot:
                    self.canvas.create_oval(gui_x+10, gui_y+10, gui_x+sz-10, gui_y+sz-10, fill="blue")

    def log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)

    def manual_step(self, action):
        res = None
        if action == "left": res = self.robot.smestitsia_vlevo()
        elif action == "right": res = self.robot.smestitsia_vpravo()
        elif action == "podkopat": res = self.robot.podkopat() # Вверх
        elif action == "back": res = self.robot.otstupit() # Вниз
        elif action == "up_diag": res = self.robot.podniatsia() # Влево-Вверх
        elif action == "down_diag": res = self.robot.spustitsia() # Вправо-Вниз
        elif action == "process": 
            self.robot.process()
            self.log(f"Обработка ячейки {self.robot.current_cell}")
            self.draw_grid()
            return

        if res:
            self.log(f"Переход в {res}")
            self.draw_grid()
        else:
            self.log("Движение невозможно!")

    def auto_step(self):
        r = self.robot
        current = r.current_cell
        if not current: return

        r.process()
        
        moved = False

        if self.move_direction == "right":
            if r.smestitsia_vpravo():
                self.log("Авто: Вправо")
                moved = True
            else:
                self.log("Авто: Стена справа, идем вверх")
                if r.podkopat():
                    self.move_direction = "left"
                    moved = True
                else:
                    self.log("Авто: Тупик или Финиш")
                    
        elif self.move_direction == "left":
            if r.smestitsia_vlevo():
                self.log("Авто: Влево")
                moved = True
            else:
                self.log("Авто: Стена слева, идем вверх")
                if r.podkopat():
                    self.move_direction = "right"
                    moved = True
                else:
                    self.log("Авто: Тупик или Финиш")

        self.draw_grid()

if __name__ == "__main__":
    root = tk.Tk()
    app = ArcheologyApp(root)
    root.mainloop()
