import tkinter as tk
from tkinter import ttk
from enum import Enum, auto
from typing import Optional, Iterator, List
import threading
import time

# --- Классы из main.py ---
class WorkshopCellType(Enum):
    Floor = auto()
    Detail = auto()
    Repaired = auto()
    Tool = auto()
    Obstacle = auto()
    Oil = auto()
    Finish = auto()

class WorkDirection(Enum):
    Forward = auto()
    Backward = auto()
    Left = auto()
    Right = auto()
    DiagUp = auto()
    DiagDown = auto()

class WorkshopCell:
    def __init__(self, cell_type: WorkshopCellType, has_robot: bool = False, x: int = 0, y: int = 0):
        self.cell_type = cell_type
        self.has_robot = has_robot
        self.x = x
        self.y = y
        self.visited = False

class Workshop:
    def __init__(self, width: int = 8, height: int = 6):
        self.width = width
        self.height = height
        self.cells = [[WorkshopCell(WorkshopCellType.Floor, False, x, y) 
                      for y in range(height)] for x in range(width)]
        self.setup_default()
    
    def setup_default(self):
        """Настройка по умолчанию"""
        for x in range(self.width):
            for y in range(self.height):
                self.cells[x][y] = WorkshopCell(WorkshopCellType.Floor, False, x, y)
        
        # Старт
        self.cells[0][0].cell_type = WorkshopCellType.Floor
        self.cells[0][0].has_robot = True
        
        # Детали
        self.cells[2][2].cell_type = WorkshopCellType.Detail
        self.cells[5][3].cell_type = WorkshopCellType.Detail
        
        # Препятствия
        self.cells[3][2].cell_type = WorkshopCellType.Obstacle
        self.cells[4][4].cell_type = WorkshopCellType.Obstacle
        
        # Финиш
        self.cells[7][5].cell_type = WorkshopCellType.Finish
    
    def get_adjacent_cell(self, current_cell: WorkshopCell, direction_value: int) -> Optional[WorkshopCell]:
        direction = WorkDirection(direction_value)
        dx, dy = 0, 0
        
        if direction == WorkDirection.Forward:  # Вперед
            dy = 1
        elif direction == WorkDirection.Backward:  # Назад
            dy = -1
        elif direction == WorkDirection.Left:  # Влево
            dx = -1
        elif direction == WorkDirection.Right:  # Вправо
            dx = 1
        elif direction == WorkDirection.DiagUp:  # Диаг вверх
            dx = -1
            dy = 1
        elif direction == WorkDirection.DiagDown:  # Диаг вниз
            dx = 1
            dy = -1
        
        nx = current_cell.x + dx
        ny = current_cell.y + dy
        
        if 0 <= nx < self.width and 0 <= ny < self.height:
            return self.cells[nx][ny]
        return None

class RobotMechanic:
    def __init__(self, workshop: Workshop):
        self.workshop = workshop
        self.current_cell = self._find_robot_cell()
        self.auto_running = False
    
    def _find_robot_cell(self) -> WorkshopCell:
        for x in range(self.workshop.width):
            for y in range(self.workshop.height):
                if self.workshop.cells[x][y].has_robot:
                    return self.workshop.cells[x][y]
        return self.workshop.cells[0][0]
    
    def move(self, direction: WorkDirection) -> bool:
        next_cell = self.workshop.get_adjacent_cell(self.current_cell, direction.value)
        if next_cell is None:
            return False
        if next_cell.cell_type in (WorkshopCellType.Obstacle, WorkshopCellType.Oil):
            return False
        
        self.current_cell.has_robot = False
        next_cell.has_robot = True
        next_cell.visited = True
        self.current_cell = next_cell
        
        if next_cell.cell_type == WorkshopCellType.Detail:
            next_cell.cell_type = WorkshopCellType.Repaired
        
        return True
    
    def repair(self):
        if self.current_cell.cell_type == WorkshopCellType.Detail:
            self.current_cell.cell_type = WorkshopCellType.Repaired
            return True
        return False
    
    def execute_task(self):
        """Умный автоматический обход"""
        if self.auto_running:
            return
            
        self.auto_running = True
        
        def run_task():
            # Находим детали
            details = []
            for x in range(self.workshop.width):
                for y in range(self.workshop.height):
                    if self.workshop.cells[x][y].cell_type == WorkshopCellType.Detail:
                        details.append((x, y))
            
            # Находим финиш
            finish = None
            for x in range(self.workshop.width):
                for y in range(self.workshop.height):
                    if self.workshop.cells[x][y].cell_type == WorkshopCellType.Finish:
                        finish = (x, y)
                        break
                if finish:
                    break
            
            if not finish:
                self.auto_running = False
                return
            
            # Обход в ширину для поиска путей
            def bfs(start, targets):
                from collections import deque
                
                queue = deque([(start[0], start[1], [])])
                visited = set()
                
                while queue:
                    x, y, path = queue.popleft()
                    
                    if (x, y) in visited:
                        continue
                    visited.add((x, y))
                    
                    new_path = path + [(x, y)]
                    
                    if (x, y) in targets:
                        return new_path[1:]  # Исключаем стартовую позицию
                    
                    # Проверяем соседей
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (1, -1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.workshop.width and 0 <= ny < self.workshop.height:
                            cell = self.workshop.cells[nx][ny]
                            if cell.cell_type not in (WorkshopCellType.Obstacle, WorkshopCellType.Oil):
                                if (nx, ny) not in visited:
                                    queue.append((nx, ny, new_path))
                
                return None
            
            current_pos = (self.current_cell.x, self.current_cell.y)
            
            # Посещаем все детали
            for target in details:
                path = bfs(current_pos, [target])
                if path:
                    for x, y in path:
                        # Обновляем в основном потоке
                        tk.Tk.after(root, 0, lambda x=x, y=y: move_to_cell(x, y))
                        time.sleep(0.3)
                    
                    current_pos = target
                    if self.current_cell.cell_type == WorkshopCellType.Detail:
                        tk.Tk.after(root, 0, lambda: repair_cell())
                        time.sleep(0.5)
            
            # Идем к финишу
            if finish:
                path = bfs(current_pos, [finish])
                if path:
                    for x, y in path:
                        tk.Tk.after(root, 0, lambda x=x, y=y: move_to_cell(x, y))
                        time.sleep(0.3)
            
            tk.Tk.after(root, 0, lambda: set_status("Автоматический обход завершен"))
            self.auto_running = False
        
        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

# --- Tkinter GUI ---
root = tk.Tk()
root.title("Робот-Механик")
root.geometry("600x500")

# Переменные
workshop = Workshop()
robot = RobotMechanic(workshop)
selected_cell_type = WorkshopCellType.Floor
colors = {
    WorkshopCellType.Floor: "white",
    WorkshopCellType.Detail: "lightblue",
    WorkshopCellType.Repaired: "lightgreen",
    WorkshopCellType.Tool: "yellow",
    WorkshopCellType.Obstacle: "gray",
    WorkshopCellType.Oil: "brown",
    WorkshopCellType.Finish: "pink"
}

# Функции
def update_display():
    canvas.delete("all")
    
    cell_size = 40
    margin = 50
    
    for x in range(workshop.width):
        for y in range(workshop.height):
            cell = workshop.cells[x][y]
            
            # Координаты
            x1 = margin + x * cell_size
            y1 = margin + y * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            # Цвет фона
            if cell.visited:
                bg = "#e0e0e0"
            else:
                bg = colors.get(cell.cell_type, "white")
            
            canvas.create_rectangle(x1, y1, x2, y2, fill=bg, outline="black")
            
            # Робот
            if cell.has_robot:
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                radius = cell_size // 4
                canvas.create_oval(center_x - radius, center_y - radius,
                                 center_x + radius, center_y + radius,
                                 fill="red", outline="darkred")
    
    # Координатная сетка
    for x in range(workshop.width):
        x_pos = margin + x * cell_size + cell_size // 2
        canvas.create_text(x_pos, margin - 10, text=str(x))
    
    for y in range(workshop.height):
        y_pos = margin + y * cell_size + cell_size // 2
        canvas.create_text(margin - 10, y_pos, text=str(y))

def on_canvas_click(event):
    cell_size = 40
    margin = 50
    
    x = (event.x - margin) // cell_size
    y = (event.y - margin) // cell_size
    
    if 0 <= x < workshop.width and 0 <= y < workshop.height:
        cell = workshop.cells[x][y]
        
        # Не изменяем клетку с роботом
        if cell.has_robot:
            set_status("Нельзя изменить клетку с роботом")
            return
        
        # Изменяем тип клетки
        cell.cell_type = selected_cell_type
        update_display()
        set_status(f"Клетка ({x},{y}) изменена на {selected_cell_type.name}")

def move_robot(direction: WorkDirection):
    if robot.move(direction):
        update_display()
        set_status(f"Робот перемещен")
    else:
        set_status(f"Невозможно переместиться")

def repair_cell():
    if robot.repair():
        update_display()
        set_status("Деталь отремонтирована")
    else:
        set_status("Здесь нет детали")

def move_to_cell(x, y):
    cell = workshop.cells[x][y]
    if cell.cell_type not in (WorkshopCellType.Obstacle, WorkshopCellType.Oil):
        robot.current_cell.has_robot = False
        cell.has_robot = True
        cell.visited = True
        robot.current_cell = cell
        
        if cell.cell_type == WorkshopCellType.Detail:
            cell.cell_type = WorkshopCellType.Repaired
        
        update_display()

def set_status(text):
    status_label.config(text=text)

def start_auto():
    set_status("Запущен автоматический обход...")
    robot.execute_task()

# Интерфейс
canvas = tk.Canvas(root, width=400, height=300, bg="white")
canvas.pack(pady=10)
canvas.bind("<Button-1>", on_canvas_click)

# Панель управления
control_frame = tk.Frame(root)
control_frame.pack(pady=5)

# Кнопки ручного управления
move_frame = tk.Frame(control_frame)
move_frame.pack(side=tk.LEFT, padx=10)

tk.Button(move_frame, text="↑", width=3, command=lambda: move_robot(WorkDirection.Forward)).grid(row=0, column=1)
tk.Button(move_frame, text="↓", width=3, command=lambda: move_robot(WorkDirection.Backward)).grid(row=2, column=1)
tk.Button(move_frame, text="←", width=3, command=lambda: move_robot(WorkDirection.Left)).grid(row=1, column=0)
tk.Button(move_frame, text="→", width=3, command=lambda: move_robot(WorkDirection.Right)).grid(row=1, column=2)
tk.Button(move_frame, text="↖", width=3, command=lambda: move_robot(WorkDirection.DiagUp)).grid(row=0, column=0)
tk.Button(move_frame, text="↘", width=3, command=lambda: move_robot(WorkDirection.DiagDown)).grid(row=2, column=2)
tk.Button(move_frame, text="🔧", width=3, command=repair_cell).grid(row=1, column=1)

# Выбор типа клетки
type_frame = tk.Frame(control_frame)
type_frame.pack(side=tk.LEFT, padx=10)

tk.Label(type_frame, text="Тип клетки:").pack()
type_var = tk.StringVar(value="Floor")
type_menu = ttk.Combobox(type_frame, textvariable=type_var, 
                        values=["Floor", "Detail", "Repaired", "Tool", "Obstacle", "Oil", "Finish"],
                        state="readonly", width=10)
type_menu.pack()

def on_type_select(event):
    global selected_cell_type
    selected_cell_type = WorkshopCellType[type_var.get()]

type_menu.bind("<<ComboboxSelected>>", on_type_select)

# Кнопка автоматического обхода
auto_frame = tk.Frame(control_frame)
auto_frame.pack(side=tk.LEFT, padx=10)

tk.Button(auto_frame, text="🤖 Автоматический обход", command=start_auto, width=20).pack()

# Статус
status_label = tk.Label(root, text="Готов", font=("Arial", 10))
status_label.pack(pady=5)

# Информация
info_frame = tk.Frame(root)
info_frame.pack()

tk.Label(info_frame, text="Управление:").grid(row=0, column=0, sticky="w")
tk.Label(info_frame, text="• ЛКМ: изменить тип клетки").grid(row=1, column=0, sticky="w")
tk.Label(info_frame, text="• Кнопки: управление роботом").grid(row=2, column=0, sticky="w")

# Инициализация
update_display()

root.mainloop()
