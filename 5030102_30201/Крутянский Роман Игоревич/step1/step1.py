import tkinter as tk
import time
from tkinter import messagebox
from enum import Enum, auto
from typing import Optional, Iterator

class WorkshopCellType(Enum):
    Floor = auto()
    Detail = auto()
    Repaired = auto()
    Tool = auto()
    Obstacle = auto()
    Oil = auto()
    Finish = auto()

class BaseDirection(Enum):
    N = auto()
    S = auto()
    W = auto()
    E = auto()
    NW = auto()
    SE = auto()

class WorkDirection(Enum):
    Forward = auto()
    Backward = auto()
    Left = auto()
    Right = auto()
    DiagUp = auto()
    DiagDown = auto()

class SideDirection:
    def __init__(self, side: BaseDirection, direction: WorkDirection):
        self.side = side
        self.direction = direction

SIDE_DIRECTION_1 = SideDirection(BaseDirection.N, WorkDirection.Forward)
SIDE_DIRECTION_2 = SideDirection(BaseDirection.S, WorkDirection.Backward)
SIDE_DIRECTION_3 = SideDirection(BaseDirection.W, WorkDirection.Left)
SIDE_DIRECTION_4 = SideDirection(BaseDirection.E, WorkDirection.Right)
SIDE_DIRECTION_5 = SideDirection(BaseDirection.NW, WorkDirection.DiagUp)
SIDE_DIRECTION_6 = SideDirection(BaseDirection.SE, WorkDirection.DiagDown)

class MethodDirection:
    def __init__(self, method_id: str, direction_value: int):
        self.method_id = method_id
        self.direction_value = direction_value

METHOD_DIRECTION_1 = MethodDirection("ЕхатьКРаботе", WorkDirection.Forward.value)
METHOD_DIRECTION_2 = MethodDirection("Отойти", WorkDirection.Backward.value)
METHOD_DIRECTION_3 = MethodDirection("СместитьВлево", WorkDirection.Left.value)
METHOD_DIRECTION_4 = MethodDirection("СместитьВправо", WorkDirection.Right.value)
METHOD_DIRECTION_5 = MethodDirection("ПоднятьсяДиаг", WorkDirection.DiagUp.value)
METHOD_DIRECTION_6 = MethodDirection("СпуститьсяДиаг", WorkDirection.DiagDown.value)

class WorkshopCell:
    def __init__(self, cell_type: WorkshopCellType, has_robot: bool = False, x: int = 0, y: int = 0):
        self.cell_type = cell_type
        self.has_robot = has_robot
        self.x = x
        self.y = y

class Workshop:
    def __init__(self, width: int, height: int,
                cells: Optional[list[list[WorkshopCell]]] = None):
        self.width = width
        self.height = height
        if cells is None:
            self.cells = [[WorkshopCell(WorkshopCellType.Floor, False, x, y) for y in range(self.height)] for x in range(self.width)]
        else:
            self.cells = cells

    def initialize_workshop(self, cell_type: WorkshopCellType):
        for x in range(self.width):
            for y in range(self.height):
                cell = self.cells[x][y]
                cell.x = x
                cell.y = y
                cell.cell_type = cell_type

    def get_adjacent_cell(self, current_cell: WorkshopCell, direction_value: int) -> Optional[WorkshopCell]:
        direction = WorkDirection(direction_value)

        dx, dy = 0, 0
        if direction == WorkDirection.Forward:
            dy = 1
        elif direction == WorkDirection.Backward:
            dy = -1
        elif direction == WorkDirection.Left:
            dx = -1
        elif direction == WorkDirection.Right:
            dx = 1
        elif direction == WorkDirection.DiagUp:
            dx = -1
            dy = 1
        elif direction == WorkDirection.DiagDown:
            dx = 1
            dy = -1

        nx = current_cell.x + dx
        ny = current_cell.y + dy

        if 0 <= nx < self.width and 0 <= ny < self.height:
            return self.cells[nx][ny]
        return None

    def get_snake_iterator(self) -> Iterator[WorkshopCell]:
        return SnakeIterator(self)

class SnakeIterator:
    def __init__(self, workshop: Workshop):
        self.width = workshop.width
        self.height = workshop.height
        self.workshop = workshop
        self.x = 0
        self.y = 0
        self.direction = "right"
        self.first = True

    def __iter__(self):
        return self

    def __next__(self) -> WorkshopCell:
        if self.first:
            self.first = False
            return self.workshop.cells[self.x][self.y]
        if self.direction == "right":
            if self.x + 1 < self.width:
                self.x += 1
            else:
                if self.y + 1 >= self.height:
                    raise StopIteration
                self.y += 1
                self.direction = "left"
        else:  # "left"
            if self.x - 1 >= 0:
                self.x -= 1
            else:
                if self.y + 1 >= self.height:
                    raise StopIteration
                self.y += 1
                self.direction = "right"
        return self.workshop.cells[self.x][self.y]

class RobotMechanic:
    def __init__(self, workshop: Workshop):
        self.workshop = workshop
        self.current_cell = self._find_robot_cell()

    def _find_robot_cell(self) -> WorkshopCell:
        for x in range(self.workshop.width):
            for y in range(self.workshop.height):
                cell = self.workshop.cells[x][y]
                if cell.has_robot:
                    return cell
        # Если робота нет, ставим в левый нижний угол (0,0) в координатах модели
        start_cell = self.workshop.cells[0][0]
        start_cell.has_robot = True
        return start_cell

    def move_forward(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_1.direction_value)

    def move_backward(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_2.direction_value)

    def move_left(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_3.direction_value)

    def move_right(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_4.direction_value)

    def move_diag_up(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_5.direction_value)

    def move_diag_down(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_6.direction_value)

    def repair_detail(self):
        if self.current_cell.cell_type == WorkshopCellType.Detail:
            self.current_cell.cell_type = WorkshopCellType.Repaired

    def _move_by_direction_value(self, direction_value: int) -> Optional[WorkshopCell]:
        next_cell = self.workshop.get_adjacent_cell(self.current_cell, direction_value)
        if next_cell is None:
            return None
        if next_cell.cell_type in (WorkshopCellType.Obstacle, WorkshopCellType.Oil):
            return None

        self.current_cell.has_robot = False
        next_cell.has_robot = True
        self.current_cell = next_cell
        return next_cell

    def execute_task(self):
        iterator = self.workshop.get_snake_iterator()
        for cell in iterator:
            self.current_cell.has_robot = False
            cell.has_robot = True
            self.current_cell = cell

            if cell.cell_type == WorkshopCellType.Detail:
                self.repair_detail()

            if cell.cell_type == WorkshopCellType.Finish:
                return


class WorkshopGUI:
    CELL_SIZE = 50
    COLORS = {
        WorkshopCellType.Floor: "#e0e0e0",
        WorkshopCellType.Detail: "#ffdd44",
        WorkshopCellType.Repaired: "#4caf50",
        WorkshopCellType.Tool: "#2196f3",
        WorkshopCellType.Obstacle: "#757575",
        WorkshopCellType.Oil: "#8d6e63",
        WorkshopCellType.Finish: "#ff9800"
    }
    ROBOT_COLOR = "#f44336"
    GRID_COLOR = "#616161"
    
    def __init__(self, workshop: Workshop, robot: RobotMechanic):
        self.workshop = workshop
        self.robot = robot
        self.root = tk.Tk()
        self.root.title("Робот-механик | Лабораторная работа")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.control_frame = tk.Frame(main_frame, padx=5, pady=5)
        self.control_frame.pack(fill=tk.X)
        
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas_width = workshop.width * self.CELL_SIZE + 20
        canvas_height = workshop.height * self.CELL_SIZE + 20
        self.canvas_frame = tk.Frame(content_frame, padx=5, pady=5)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            width=canvas_width, 
            height=canvas_height,
            bg="#f5f5f5",
            highlightthickness=1,
            highlightbackground="#bdbdbd"
        )
        self.canvas.pack()
        
        self.legend_frame = tk.Frame(content_frame, padx=5, pady=5, bg="#ffffff", relief=tk.GROOVE, bd=1)
        self.legend_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        
        self.status_frame = tk.Frame(main_frame, padx=5, pady=5)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        buttons = [
            ("Вперед", self.move_forward),
            ("Назад", self.move_backward),
            ("Влево", self.move_left),
            ("Вправо", self.move_right),
            ("Диаг. вверх", self.move_diag_up),
            ("Диаг. вниз", self.move_diag_down),
            ("Починить", self.repair),
            ("Выполнить задачу", self.execute_task)
        ]
        
        for text, command in buttons:
            btn = tk.Button(
                self.control_frame, 
                text=text, 
                command=command,
                font=("Arial", 9, "bold"),
                bg="#2196f3",
                fg="white",
                padx=8,
                pady=3
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        self.create_legend()
        
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе | Координаты робота: (0, 0)")
        self.status_label = tk.Label(
            self.status_frame,
            textvariable=self.status_var,
            font=("Arial", 10),
            fg="#212121",
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.draw_workshop()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_legend(self):
        """Создает компактную легенду справа от поля"""
        tk.Label(self.legend_frame, text="Легенда:", font=("Arial", 11, "bold"), bg="#ffffff").pack(anchor=tk.W, pady=(0, 5))
        
        legend_items = [
            (WorkshopCellType.Floor, "Пол", "#e0e0e0"),
            (WorkshopCellType.Detail, "Деталь (D)", "#ffdd44"),
            (WorkshopCellType.Repaired, "Отремонтировано", "#4caf50"),
            (WorkshopCellType.Tool, "Инструмент", "#2196f3"),
            (WorkshopCellType.Obstacle, "Препятствие", "#757575"),
            (WorkshopCellType.Oil, "Масляное пятно", "#8d6e63"),
            (WorkshopCellType.Finish, "Финиш (F)", "#ff9800"),
            (None, "Робот (R)", "#f44336")
        ]
        
        for cell_type, name, color in legend_items:
            item_frame = tk.Frame(self.legend_frame, bg="#ffffff")
            item_frame.pack(fill=tk.X, padx=2, pady=2)
            
            color_canvas = tk.Canvas(item_frame, width=20, height=20, bg=color, highlightthickness=1, highlightbackground="#9e9e9e")
            color_canvas.pack(side=tk.LEFT, padx=5)
            
            if cell_type is None:
                color_canvas.create_text(10, 10, text="R", font=("Arial", 8, "bold"), fill="white")
            elif cell_type == WorkshopCellType.Detail:
                color_canvas.create_text(10, 10, text="D", font=("Arial", 8, "bold"))
            elif cell_type == WorkshopCellType.Finish:
                color_canvas.create_text(10, 10, text="F", font=("Arial", 8, "bold"))
            elif cell_type == WorkshopCellType.Tool:
                color_canvas.create_text(10, 10, text="T", font=("Arial", 8, "bold"))
            
            tk.Label(item_frame, text=name, font=("Arial", 9), bg="#ffffff").pack(side=tk.LEFT, padx=5)
    
    def draw_workshop(self):
        self.canvas.delete("all")
        offset = 10
        
        for x in range(self.workshop.width + 1):
            self.canvas.create_line(
                offset + x * self.CELL_SIZE, offset,
                offset + x * self.CELL_SIZE, offset + self.workshop.height * self.CELL_SIZE,
                fill=self.GRID_COLOR, width=1
            )
        
        for y in range(self.workshop.height + 1):
            self.canvas.create_line(
                offset, offset + y * self.CELL_SIZE,
                offset + self.workshop.width * self.CELL_SIZE, offset + y * self.CELL_SIZE,
                fill=self.GRID_COLOR, width=1
            )
        
        for x in range(self.workshop.width):
            for y in range(self.workshop.height):
                cell = self.workshop.cells[x][y]
                model_y = self.workshop.height - 1 - y
                
                x1 = offset + x * self.CELL_SIZE
                y1 = offset + model_y * self.CELL_SIZE
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE
                
                fill_color = self.COLORS.get(cell.cell_type, "#ffffff")
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=fill_color,
                    outline="#9e9e9e",
                    width=1
                )
                
                if cell.cell_type in [WorkshopCellType.Detail, WorkshopCellType.Finish]:
                    text = "D" if cell.cell_type == WorkshopCellType.Detail else "F"
                    self.canvas.create_text(
                        (x1 + x2) // 2, (y1 + y2) // 2,
                        text=text,
                        font=("Arial", 14, "bold"),
                        fill="black"
                    )
                
                if cell.has_robot:
                    self.canvas.create_oval(
                        x1 + 8, y1 + 8, x2 - 8, y2 - 8,
                        fill=self.ROBOT_COLOR,
                        outline="#d32f2f",
                        width=2
                    )
                    self.canvas.create_text(
                        (x1 + x2) // 2, (y1 + y2) // 2,
                        text="R",
                        font=("Arial", 12, "bold"),
                        fill="white"
                    )
        
        self.update_status()
    
    def update_status(self):
        coords = f"({self.robot.current_cell.x}, {self.robot.current_cell.y})"
        cell_type = self.robot.current_cell.cell_type.name
        status = f"Текущая ячейка: {cell_type} | Координаты робота: {coords}"
        self.status_var.set(status)
    
    def move_forward(self):
        self._execute_move(self.robot.move_forward)
    
    def move_backward(self):
        self._execute_move(self.robot.move_backward)
    
    def move_left(self):
        self._execute_move(self.robot.move_left)
    
    def move_right(self):
        self._execute_move(self.robot.move_right)
    
    def move_diag_up(self):
        self._execute_move(self.robot.move_diag_up)
    
    def move_diag_down(self):
        self._execute_move(self.robot.move_diag_down)
    
    def repair(self):
        prev_type = self.robot.current_cell.cell_type
        self.robot.repair_detail()
        self.draw_workshop()
        
        if prev_type == WorkshopCellType.Detail:
            messagebox.showinfo("Успех", "Деталь успешно отремонтирована!")
        else:
            messagebox.showinfo("Информация", "Нечего ремонтировать в этой ячейке")
    
    def execute_task(self):
        self.robot.execute_task()
        self.draw_workshop()
        messagebox.showinfo("Задание выполнено", "Робот завершил обход по змейке!")
    
    def _execute_move(self, move_func):
        result = move_func()
        if result is None:
            messagebox.showwarning("Ошибка движения", "Невозможно переместиться в этом направлении!\nПроверьте наличие препятствий или границы поля")
        else:
            self.draw_workshop()
    
    def on_closing(self):
        if messagebox.askokcancel("Выход", "Завершить работу с лабораторной?"):
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    workshop = Workshop(7, 6)
    
    workshop.cells[0][0].has_robot = True
    workshop.cells[1][0].cell_type = WorkshopCellType.Detail
    workshop.cells[2][1].cell_type = WorkshopCellType.Detail
    workshop.cells[4][0].cell_type = WorkshopCellType.Obstacle
    workshop.cells[3][2].cell_type = WorkshopCellType.Oil
    workshop.cells[5][1].cell_type = WorkshopCellType.Tool
    workshop.cells[6][5].cell_type = WorkshopCellType.Finish
    
    workshop.cells[3][4].cell_type = WorkshopCellType.Detail
    workshop.cells[5][3].cell_type = WorkshopCellType.Detail
    
    robot = RobotMechanic(workshop)
    
    app = WorkshopGUI(workshop, robot)
    app.run()