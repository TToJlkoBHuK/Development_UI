import tkinter as tk
from tkinter import scrolledtext
from collections import deque
from enum import Enum
from typing import Optional, List, Tuple

class GardenCellType(Enum):
    Road = "Дорога"
    Flowerbed = "Клумба"
    Bed = "Грядка"
    Wall = "Стена"
    Water = "Вода"
    Soil = "Грунт"
    Finish = "Финиш"

class MoveDirection(Enum):
    Forward = (0, 1)
    Backward = (0, -1)
    Left = (-1, 0)
    Right = (1, 0)
    DiagSV = (-1, 1)
    DiagSZ = (1, -1)

class GardenCell:
    def __init__(self, cell_type: GardenCellType, x: int, y: int):
        self.cell_type = cell_type
        self.has_robot = False
        self.is_visited = False
        self.x = x
        self.y = y

class Garden:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[GardenCell(GardenCellType.Road, x, y)
                       for y in range(self.height)] for x in range(self.width)]

    def is_passable(self, x: int, y: int, allow_targets=False) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        ct = self.cells[x][y].cell_type
        if ct in [GardenCellType.Water, GardenCellType.Wall]:
            return False
        if ct == GardenCellType.Bed and not allow_targets:
            return False
        return True

class GardenRobot:
    def __init__(self, garden: Garden):
        self.garden = garden
        self.current_cell = self.garden.cells[0][0]
        self.current_cell.has_robot = True
        self.current_cell.is_visited = True

    def move_to(self, next_cell: GardenCell) -> str:
        self.current_cell.has_robot = False
        old_type = next_cell.cell_type
        self.current_cell = next_cell
        self.current_cell.has_robot = True
        self.current_cell.is_visited = True
        
        action_text = f"Переход в ({next_cell.x}, {next_cell.y})"
        
        if old_type == GardenCellType.Bed:
            self.current_cell.cell_type = GardenCellType.Flowerbed
            action_text += " -> Грядка стала Клумбой!"
        elif old_type == GardenCellType.Soil:
            self.current_cell.cell_type = GardenCellType.Water
            action_text += " -> Грунт залит Водой!"
        
        return action_text

class GardenGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Робот-Садовник")
        
        self.cols, self.rows = 6, 7
        self.cell_size = 65
        self.garden = Garden(self.cols, self.rows)
        self.robot = GardenRobot(self.garden)
        
        self.colors = {
            GardenCellType.Road: "white",
            GardenCellType.Flowerbed: "#DF17D9", 
            GardenCellType.Bed: "#9A4D0A",      
            GardenCellType.Wall: "#090909",     
            GardenCellType.Water: "#00BFFF",    
            GardenCellType.Soil: "#094F20",     
            GardenCellType.Finish: "#ED0E0E",
            "visited": "#928D8D"
        }

        self._setup_map()
        self._create_widgets()
        self.update_canvas()
        self.log_message("Система инициализирована. Робот в (0,0)")

    def _setup_map(self):
        self.garden.cells[2][2].cell_type = GardenCellType.Bed
        self.garden.cells[1][3].cell_type = GardenCellType.Bed
        self.garden.cells[4][4].cell_type = GardenCellType.Bed
        self.garden.cells[3][1].cell_type = GardenCellType.Water
        self.garden.cells[3][2].cell_type = GardenCellType.Water
        self.garden.cells[5][1].cell_type = GardenCellType.Soil
        self.garden.cells[0][5].cell_type = GardenCellType.Soil
        self.garden.cells[2][4].cell_type = GardenCellType.Wall
        self.garden.cells[3][4].cell_type = GardenCellType.Wall
        self.garden.cells[5][6].cell_type = GardenCellType.Finish

    def _create_widgets(self):
        main_container = tk.Frame(self.root, padx=10, pady=10)
        main_container.pack()

        left_frame = tk.Frame(main_container)
        left_frame.grid(row=0, column=0, sticky="n")

        self.canvas = tk.Canvas(left_frame, width=self.cols*self.cell_size, 
                                height=self.rows*self.cell_size, bg="white", 
                                highlightthickness=1, highlightbackground="black")
        self.canvas.pack()

        ctrl_panel = tk.Frame(left_frame, pady=10)
        ctrl_panel.pack(fill="x")

        joy_frame = tk.Frame(ctrl_panel)
        joy_frame.pack(side="left")

        btn_opt = {'width': 3, 'font': ('Arial', 10, 'bold')}
        tk.Button(joy_frame, text="↖", **btn_opt, command=lambda: self.manual_move(MoveDirection.DiagSV)).grid(row=0, column=0)
        tk.Button(joy_frame, text="↑", **btn_opt, command=lambda: self.manual_move(MoveDirection.Forward)).grid(row=0, column=1)
        tk.Button(joy_frame, text="↗", **btn_opt, state="disabled").grid(row=0, column=2)
        tk.Button(joy_frame, text="←", **btn_opt, command=lambda: self.manual_move(MoveDirection.Left)).grid(row=1, column=0)
        tk.Label(joy_frame, text="·", font=('Arial', 12)).grid(row=1, column=1)
        tk.Button(joy_frame, text="→", **btn_opt, command=lambda: self.manual_move(MoveDirection.Right)).grid(row=1, column=2)
        tk.Button(joy_frame, text="↙", **btn_opt, state="disabled").grid(row=2, column=0)
        tk.Button(joy_frame, text="↓", **btn_opt, command=lambda: self.manual_move(MoveDirection.Backward)).grid(row=2, column=1)
        tk.Button(joy_frame, text="↘", **btn_opt, command=lambda: self.manual_move(MoveDirection.DiagSZ)).grid(row=2, column=2)

        self.auto_btn = tk.Button(ctrl_panel, text="АВТОПРОХОД", bg="#4CAF50", fg="white",
                                  font=("Arial", 10, "bold"), command=self.run_smart_auto)
        self.auto_btn.pack(side="right", expand=True, fill="both", padx=(10, 0))

        right_frame = tk.Frame(main_container, padx=10)
        right_frame.grid(row=0, column=1, sticky="nsew")

        tk.Label(right_frame, text="ИСТОРИЯ ХОДОВ", font=("Arial", 10, "bold")).pack()
        self.history_log = scrolledtext.ScrolledText(right_frame, width=35, height=25, font=("Consolas", 9))
        self.history_log.pack(fill="both", expand=True)

        legend_frame = tk.LabelFrame(main_container, text="Легенда цветов", pady=5)
        legend_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        legend_items = [
            (GardenCellType.Road, "Дорога"),
            ("visited", "След робота"),
            (GardenCellType.Bed, "Грядка"),
            (GardenCellType.Flowerbed, "Клумба"),
            (GardenCellType.Soil, "Грунт"),
            (GardenCellType.Water, "Вода"),
            (GardenCellType.Wall, "Стена"),
            (GardenCellType.Finish, "Финиш")
        ]

        for i, (key, name) in enumerate(legend_items):
            f = tk.Frame(legend_frame)
            f.pack(side="left", padx=8)
            tk.Label(f, bg=self.colors[key], width=2, relief="sunken", bd=1).pack(side="left")
            tk.Label(f, text=name, font=("Arial", 8)).pack(side="left", padx=2)

    def log_message(self, msg):
        self.history_log.insert(tk.END, f"> {msg}\n")
        self.history_log.see(tk.END)

    def update_canvas(self):
        self.canvas.delete("all")
        for x in range(self.cols):
            for y in range(self.rows):
                cell = self.garden.cells[x][y]
                x1, y1 = x*self.cell_size, (self.rows-1-y)*self.cell_size
                x2, y2 = x1+self.cell_size, y1+self.cell_size
                
                color = self.colors[cell.cell_type]
                if cell.cell_type == GardenCellType.Road and cell.is_visited:
                    color = self.colors["visited"]

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#ddd")
                self.canvas.create_text(x1+15, y1+12, text=f"{x},{y}", font=("Arial", 6), fill="#999")
                
                if cell.has_robot:
                    self.canvas.create_oval(x1+12, y1+12, x2-12, y2-12, fill="red", outline="black", width=2)

    def manual_move(self, direction_enum):
        dx, dy = direction_enum.value
        nx, ny = self.robot.current_cell.x + dx, self.robot.current_cell.y + dy
        
        if self.garden.is_passable(nx, ny, allow_targets=True):
            res = self.robot.move_to(self.garden.cells[nx][ny])
            self.log_message(f"[Manual] {res}")
            self.update_canvas()
            if self.robot.current_cell.cell_type == GardenCellType.Finish:
                self.log_message("УСПЕХ: Финиш достигнут вручную!")
        else:
            self.log_message(f"ОШИБКА: Клетка ({nx},{ny}) заблокирована!")

    def find_path(self, start: Tuple[int, int], target: Tuple[int, int]) -> List[Tuple[int, int]]:
        queue = deque([[start]])
        visited = {start}
        while queue:
            path = queue.popleft()
            x, y = path[-1]
            if (x, y) == target: return path
            for d in MoveDirection:
                dx, dy = d.value
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if (nx, ny) not in visited:
                        if self.garden.is_passable(nx, ny) or (nx, ny) == target:
                            visited.add((nx, ny))
                            queue.append(path + [(nx, ny)])
        return []

    def run_smart_auto(self):
        self.auto_btn.config(state="disabled")
        self.log_message("ЗАПУСК АВТОПРОХОДА")
        
        targets = []
        for x in range(self.cols):
            for y in range(self.rows):
                if self.garden.cells[x][y].cell_type in [GardenCellType.Bed, GardenCellType.Soil]:
                    targets.append((x, y))
        
        finish_pos = next((x, y) for x in range(self.cols) for y in range(self.rows) 
                          if self.garden.cells[x][y].cell_type == GardenCellType.Finish)
        
        full_path = []
        curr = (self.robot.current_cell.x, self.robot.current_cell.y)
        temp_targets = list(targets)
        
        while temp_targets:
            best_p = []
            c_target = None
            for t in temp_targets:
                p = self.find_path(curr, t)
                if p and (not best_p or len(p) < len(best_p)):
                    best_p, c_target = p, t
            if not best_p: break
            full_path.extend(best_p[1:])
            curr = c_target
            temp_targets.remove(c_target)
            
        to_f = self.find_path(curr, finish_pos)
        if to_f: full_path.extend(to_f[1:])
        self._animate(full_path, 0)

    def _animate(self, path, idx):
        if idx < len(path):
            tx, ty = path[idx]
            res = self.robot.move_to(self.garden.cells[tx][ty])
            self.log_message(f"[Auto] {res}")
            self.update_canvas()
            self.root.after(300, lambda: self._animate(path, idx + 1))
        else:
            self.log_message("АВТОПРОХОД ЗАВЕРШЕН.")
            self.auto_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = GardenGUI(root)
    root.mainloop()