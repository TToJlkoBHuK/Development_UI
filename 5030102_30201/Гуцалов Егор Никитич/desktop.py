import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import threading
import time
from enum import Enum, auto
from typing import Optional, List, Iterator

class WorkshopCellType(Enum):
    Canvas = 1
    Sketch = 2
    Ready = 3
    Tool = 4
    Void = 5
    Finish = 6
    Collection = 7

class BaseDirection(Enum):
    N = auto()
    S = auto()
    W = auto()
    E = auto()
    NW = auto()
    SE = auto()

class WorkDirection(Enum):
    DesignForward = auto()
    DesignBackward = auto()
    DesignLeft = auto()
    DesignRight = auto()
    DiagDW = auto()  
    DiagDN = auto()  

class SideDirection:
    def __init__(self, side: BaseDirection, direction: WorkDirection):
        self.side = side
        self.direction = direction

SIDE_DIRECTION_1 = SideDirection(BaseDirection.N, WorkDirection.DesignForward)
SIDE_DIRECTION_2 = SideDirection(BaseDirection.S, WorkDirection.DesignBackward)
SIDE_DIRECTION_3 = SideDirection(BaseDirection.W, WorkDirection.DesignLeft)
SIDE_DIRECTION_4 = SideDirection(BaseDirection.E, WorkDirection.DesignRight)
SIDE_DIRECTION_5 = SideDirection(BaseDirection.NW, WorkDirection.DiagDW)
SIDE_DIRECTION_6 = SideDirection(BaseDirection.SE, WorkDirection.DiagDN)

class MethodDirection:
    def __init__(self, method_id: str, direction_value: int):
        self.method_id = method_id
        self.direction_value = direction_value

METHOD_DIRECTION_1 = MethodDirection("ПодойтиКХолсту", WorkDirection.DesignForward.value)
METHOD_DIRECTION_2 = MethodDirection("Отойти", WorkDirection.DesignBackward.value)
METHOD_DIRECTION_3 = MethodDirection("СместитьсяВлево", WorkDirection.DesignLeft.value)
METHOD_DIRECTION_4 = MethodDirection("СместитьсяВправо", WorkDirection.DesignRight.value)
METHOD_DIRECTION_5 = MethodDirection("Подняться", WorkDirection.DiagDW.value)
METHOD_DIRECTION_6 = MethodDirection("Спуститься", WorkDirection.DiagDN.value)

class WorkshopCell:
    def __init__(self, cell_type: WorkshopCellType = WorkshopCellType.Canvas, has_robot: bool = False, x: int = 0, y: int = 0):
        self.cell_type = cell_type
        self.has_robot = has_robot
        self.x = x
        self.y = y

class Workshop:
    def __init__(self, width: int, height: int, cells: Optional[List[List[WorkshopCell]]] = None):
        self.width = width
        self.height = height
        if cells is None:
            self.cells = [[WorkshopCell(x=x, y=y) for x in range(width)] for y in range(height)]
        else:
            self.cells = cells

    def initialize_workshop(self, cell_type: WorkshopCellType):
        for y in range(self.height):
            for x in range(self.width):
                cell = self.cells[y][x]
                cell.x = x
                cell.y = y
                cell.cell_type = cell_type
                cell.has_robot = False

    def get_adjacent_cell(self, current_cell: WorkshopCell, direction_value: int) -> Optional[WorkshopCell]:
        direction = WorkDirection(direction_value)

        dx, dy = 0, 0
        if direction == WorkDirection.DesignForward:
            dy = 1  
        elif direction == WorkDirection.DesignBackward:
            dy = -1 
        elif direction == WorkDirection.DesignLeft:
            dx = -1 
        elif direction == WorkDirection.DesignRight:
            dx = 1  
        elif direction == WorkDirection.DiagDW:
            dx = -1
            dy = 1  
        elif direction == WorkDirection.DiagDN:
            dx = 1
            dy = -1  

        nx = current_cell.x + dx
        ny = current_cell.y + dy

        if 0 <= nx < self.width and 0 <= ny < self.height:
            return self.cells[ny][nx]
        return None

    def get_snake_iterator(self) -> Iterator[WorkshopCell]:
        return SnakeIterator(self)

class SnakeIterator:
    def __init__(self, workshop: Workshop):
        self.width = workshop.width
        self.height = workshop.height
        self.workshop = workshop
        self.current_x = 0
        self.current_y = 0  
        self.moving_right = True
        self.finished = False

    def __iter__(self):
        return self

    def __next__(self) -> WorkshopCell:
        if self.finished:
            raise StopIteration

        if self.current_y >= self.height:
            self.finished = True
            raise StopIteration

        cell = self.workshop.cells[self.current_y][self.current_x]
        if not cell:
            self.finished = True
            raise StopIteration

        next_x, next_y = self.current_x, self.current_y
        
        if self.moving_right:
            if self.current_x < self.width - 1:
                next_x = self.current_x + 1
            else:
                if self.current_y < self.height - 1:
                    next_y = self.current_y + 1
                    self.moving_right = False
                else:
                    self.finished = True
        else:
            if self.current_x > 0:
                next_x = self.current_x - 1
            else:
                if self.current_y < self.height - 1:
                    next_y = self.current_y + 1
                    self.moving_right = True
                else:
                    self.finished = True

        current_cell = cell
        self.current_x, self.current_y = next_x, next_y
        return current_cell

class DesignerRobot:
    def __init__(self, workshop: Workshop):
        self.workshop = workshop
        self.current_cell = self._find_robot_cell()

    def _find_robot_cell(self) -> WorkshopCell:
        for y in range(self.workshop.height):
            for x in range(self.workshop.width):
                cell = self.workshop.cells[y][x]
                if cell.has_robot:
                    return cell
        
        start_cell = self.workshop.cells[0][0]
        start_cell.has_robot = True
        return start_cell

    def move_to_canvas(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_1.direction_value)

    def move_away(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_2.direction_value)

    def move_left(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_3.direction_value)

    def move_right(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_4.direction_value)

    def move_up(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_5.direction_value)

    def move_down(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_6.direction_value)

    def apply_canvas(self):
        if self.current_cell.cell_type == WorkshopCellType.Canvas:
            self.current_cell.cell_type = WorkshopCellType.Sketch

    def apply_sketch(self):
        if self.current_cell.cell_type == WorkshopCellType.Sketch:
            self.current_cell.cell_type = WorkshopCellType.Ready

    def _move_by_direction_value(self, direction_value: int) -> Optional[WorkshopCell]:
        next_cell = self.workshop.get_adjacent_cell(self.current_cell, direction_value)
        if next_cell is None:
            return None
        if next_cell.cell_type in (WorkshopCellType.Tool, WorkshopCellType.Void):
            return None

        self.current_cell.has_robot = False
        next_cell.has_robot = True
        self.current_cell = next_cell
        return next_cell

    def execute_task(self, visual_callback=None):
        iterator = self.workshop.get_snake_iterator()
        for cell in iterator:
            if cell.cell_type not in (WorkshopCellType.Tool, WorkshopCellType.Void):
                if self.current_cell != cell:
                    self.current_cell.has_robot = False
                    cell.has_robot = True
                    self.current_cell = cell
            
            if self.current_cell == cell:
                if cell.cell_type == WorkshopCellType.Canvas:
                    self.apply_canvas()
                elif cell.cell_type == WorkshopCellType.Sketch:
                    self.apply_sketch()

                if cell.cell_type == WorkshopCellType.Finish:
                    if visual_callback:
                        visual_callback()
                    return
            
            if visual_callback:
                visual_callback()
                time.sleep(0.2)  

class RobotDesignerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Робот-Дизайнер")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        
        self.cell_colors = {
            WorkshopCellType.Canvas: '#FFE082',    
            WorkshopCellType.Sketch: '#FFB300',    
            WorkshopCellType.Ready: '#4CAF50',     
            WorkshopCellType.Tool: '#9E9E9E',      
            WorkshopCellType.Void: '#212121',      
            WorkshopCellType.Finish: '#9C27B0',    
            WorkshopCellType.Collection: '#2196F3', 
        }
        
        self.robot_color = '#E53935'  
        
        self.create_widgets()
        
        self.workshop = None
        self.robot = None
        self.cell_size = 50  
        
    def create_widgets(self):
        top_frame = tk.Frame(self.root, bg='#34495e', height=60)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_font = tkfont.Font(family='Arial', size=16, weight='bold')
        title_label = tk.Label(top_frame, text="Робот-Дизайнер", 
                              font=title_font, bg='#34495e', fg='white')
        title_label.pack(side=tk.LEFT, padx=10)
        
        button_frame = tk.Frame(top_frame, bg='#34495e')
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        load_btn = tk.Button(button_frame, text="Загрузить карту", 
                            command=self.load_map, bg='#3498db', fg='white',
                            font=('Arial', 10, 'bold'), relief=tk.RAISED,
                            bd=2, padx=10, pady=5)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        solve_btn = tk.Button(button_frame, text="РЕШИТЬ", 
                             command=self.solve_maze, bg='#2ecc71', fg='white',
                             font=('Arial', 10, 'bold'), relief=tk.RAISED,
                             bd=2, padx=15, pady=5)
        solve_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(button_frame, text="Сбросить", 
                             command=self.reset_maze, bg='#e74c3c', fg='white',
                             font=('Arial', 10, 'bold'), relief=tk.RAISED,
                             bd=2, padx=10, pady=5)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.canvas_frame = tk.Frame(main_frame, bg='#34495e', bd=2, relief=tk.SUNKEN)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='#1a2530', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        legend_frame = tk.Frame(main_frame, bg='#34495e', width=250, bd=2, relief=tk.SUNKEN)
        legend_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))
        
        legend_title = tk.Label(legend_frame, text="ЛЕГЕНДА", 
                               font=('Arial', 14, 'bold'), bg='#34495e', fg='white')
        legend_title.pack(pady=10)
        
        legend_items = [
            (WorkshopCellType.Canvas, "Холст (не обработан)"),
            (WorkshopCellType.Sketch, "Эскиз (частично обработан)"),
            (WorkshopCellType.Ready, "Готово (полностью обработано)"),
            (WorkshopCellType.Tool, "Инструмент (нельзя заходить)"),
            (WorkshopCellType.Void, "Пустота (нельзя заходить)"),
            (WorkshopCellType.Finish, "Финиш (точка завершения)"),
            (WorkshopCellType.Collection, "Коллекция (нейтральная ячейка)")
        ]
        
        for cell_type, description in legend_items:
            item_frame = tk.Frame(legend_frame, bg='#34495e')
            item_frame.pack(fill=tk.X, padx=10, pady=5)
            
            color_box = tk.Canvas(item_frame, width=20, height=20, 
                                 bg=self.cell_colors[cell_type], 
                                 highlightthickness=1, highlightbackground='white')
            color_box.pack(side=tk.LEFT)
            
            desc_label = tk.Label(item_frame, text=description, 
                                font=('Arial', 10), bg='#34495e', fg='white',
                                anchor=tk.W, justify=tk.LEFT)
            desc_label.pack(side=tk.LEFT, padx=5)
        
        robot_frame = tk.Frame(legend_frame, bg='#34495e')
        robot_frame.pack(fill=tk.X, padx=10, pady=10)
        
        robot_canvas = tk.Canvas(robot_frame, width=30, height=30, bg='#34495e', highlightthickness=0)
        robot_canvas.pack(side=tk.LEFT)
        
        robot_canvas.create_polygon(15, 5, 5, 25, 25, 25, fill=self.robot_color, outline='black')
        
        robot_label = tk.Label(robot_frame, text="Робот-Дизайнер", 
                             font=('Arial', 10, 'bold'), bg='#34495e', fg='white')
        robot_label.pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Загрузите карту для начала работы")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                             font=('Arial', 10), bg='#34495e', fg='white',
                             anchor=tk.W, padx=10)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_map(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл с картой",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            
            if not lines:
                messagebox.showerror("Ошибка", "Файл пустой")
                return
            
            width = len(lines[0].split())
            height = len(lines)
            
            for i, line in enumerate(lines[1:], 1):
                if len(line.split()) != width:
                    messagebox.showerror("Ошибка", f"Несоответствие размеров в строке {i+1}")
                    return
            
            matrix_input = []
            for line in lines:
                tokens = line.split()
                row = []
                for token in tokens:
                    token = token.strip()
                    if token.startswith(('0x', '0X')):
                        code = int(token, 16)
                    else:
                        code = int(token)
                    row.append(code)
                matrix_input.append(row)
            
            values_in_snake_order = []
            for y in range(height-1, -1, -1):  
                row_values = matrix_input[y]
                if (height-1-y) % 2 == 0:  
                    values_in_snake_order.extend(row_values)
                else:  
                    values_in_snake_order.extend(reversed(row_values))
            
            self.workshop = Workshop(width, height)
            self.workshop.initialize_workshop(WorkshopCellType.Ready) 
            snake_iter = self.workshop.get_snake_iterator()
            value_iter = iter(values_in_snake_order)
            
            for cell in snake_iter:
                try:
                    code = next(value_iter)
                except StopIteration:
                    break
                
                cell_type_value = (code & 0x7) + 1
                if cell_type_value > 7:
                    cell_type_value = 3 
                cell_type = WorkshopCellType(cell_type_value)
                
                has_robot = bool(code & 0x8)
                
                cell.cell_type = cell_type
                cell.has_robot = has_robot
            
            self.robot = DesignerRobot(self.workshop)
            self.status_var.set(f"Карта загружена: {width}x{height}")
            self.draw_maze()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить карту:\n{str(e)}")
            self.status_var.set("Ошибка загрузки карты")
    
    def draw_maze(self):
        if not self.workshop:
            return
        
        self.canvas.delete("all")
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width == 1 or canvas_height == 1: 
            canvas_width = 600
            canvas_height = 400
        
        cell_size_x = canvas_width // self.workshop.width
        cell_size_y = canvas_height // self.workshop.height
        self.cell_size = min(cell_size_x, cell_size_y, 60)  
        padding_x = (canvas_width - self.workshop.width * self.cell_size) // 2
        padding_y = (canvas_height - self.workshop.height * self.cell_size) // 2
        
        for y in range(self.workshop.height):
            for x in range(self.workshop.width):
                cell = self.workshop.cells[y][x]
                
                canvas_y = self.workshop.height - 1 - y
                
                x1 = padding_x + x * self.cell_size
                y1 = padding_y + canvas_y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                color = self.cell_colors.get(cell.cell_type, '#2c3e50')
                
                outline = 'yellow' if cell.has_robot else 'black'
                width = 2 if cell.has_robot else 1
                
                self.canvas.create_rectangle(x1, y1, x2, y2, 
                                           fill=color, outline=outline, width=width)
                
                text = cell.cell_type.name[0] 
                if cell.has_robot:
                    text += "R"
                
                if self.cell_size > 25:
                    text_color = 'white' if color in ['#212121', '#9C27B0'] else 'black'
                    self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                          text=text, fill=text_color,
                                          font=('Arial', max(8, self.cell_size // 5)))
                
                if cell.has_robot:
                    self.draw_robot(x1, y1, x2, y2)
        
        self.draw_grid(padding_x, padding_y)
        
        self.draw_axis_labels(padding_x, padding_y, canvas_width, canvas_height)
    
    def draw_robot(self, x1, y1, x2, y2):
        """Рисует треугольник, представляющий робота"""
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        size = self.cell_size // 3
        
        points = [
            (center_x, center_y - size),  
            (center_x - size, center_y + size),   
            (center_x + size, center_y + size)   
        ]
        
        self.canvas.create_polygon(points, fill=self.robot_color, 
                                  outline='black', width=1)
    
    def draw_grid(self, padding_x, padding_y):
        """Рисует координатную сетку"""
        for x in range(self.workshop.width + 1):
            x_pos = padding_x + x * self.cell_size
            self.canvas.create_line(x_pos, padding_y, 
                                  x_pos, padding_y + self.workshop.height * self.cell_size,
                                  fill='#555', dash=(2, 2))
        
        for y in range(self.workshop.height + 1):
            canvas_y = self.workshop.height - y
            y_pos = padding_y + canvas_y * self.cell_size
            self.canvas.create_line(padding_x, y_pos,
                                  padding_x + self.workshop.width * self.cell_size, y_pos,
                                  fill='#555', dash=(2, 2))
    
    def draw_axis_labels(self, padding_x, padding_y, canvas_width, canvas_height):
        """Добавляет подписи осей"""
        for x in range(self.workshop.width):
            x_pos = padding_x + x * self.cell_size + self.cell_size // 2
            y_pos = padding_y + self.workshop.height * self.cell_size + 10
            self.canvas.create_text(x_pos, y_pos, text=str(x), 
                                  fill='white', font=('Arial', 8))
        
        for y in range(self.workshop.height):
            canvas_y = self.workshop.height - 1 - y
            x_pos = padding_x - 10
            y_pos = padding_y + canvas_y * self.cell_size + self.cell_size // 2
            self.canvas.create_text(x_pos, y_pos, text=str(y),
                                  fill='white', font=('Arial', 8))
        
        self.canvas.create_text(padding_x + self.workshop.width * self.cell_size // 2,
                               padding_y + self.workshop.height * self.cell_size + 25,
                               text="Ось X", fill='white', font=('Arial', 10, 'bold'))
        
        self.canvas.create_text(padding_x - 40,
                               padding_y + self.workshop.height * self.cell_size // 2,
                               text="Ось Y", fill='white', font=('Arial', 10, 'bold'))
    
    def solve_maze(self):
        if not self.workshop or not self.robot:
            messagebox.showwarning("Внимание", "Сначала загрузите карту")
            return
        
        threading.Thread(target=self.run_solution, daemon=True).start()
    
    def run_solution(self):
        self.root.after(0, lambda: self.status_var.set("Решение задачи..."))
        
        try:
            self.save_initial_state()
            
            self.robot.execute_task(self.visual_callback)
            
            self.root.after(0, lambda: self.status_var.set("Задача решена!"))
            messagebox.showinfo("Успех", "Робот успешно выполнил задачу!")
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Ошибка при решении: {str(e)}"))
            messagebox.showerror("Ошибка", f"Не удалось решить задачу:\n{str(e)}")
    
    def visual_callback(self):
        """Callback для обновления визуализации после каждого шага"""
        self.root.after(0, self.draw_maze)
        self.root.update()
    
    def reset_maze(self):
        if hasattr(self, 'initial_state'):
            width, height, cells_data = self.initial_state
            
            self.workshop = Workshop(width, height)
            for y in range(height):
                for x in range(width):
                    cell_data = cells_data[y][x]
                    self.workshop.cells[y][x].cell_type = cell_data['type']
                    self.workshop.cells[y][x].has_robot = cell_data['robot']
                    self.workshop.cells[y][x].x = x
                    self.workshop.cells[y][x].y = y
            
            self.robot = DesignerRobot(self.workshop)
            self.draw_maze()
            self.status_var.set("Лабиринт сброшен к начальному состоянию")
        else:
            self.status_var.set("Нет сохраненного состояния для сброса")
    
    def save_initial_state(self):
        """Сохраняет начальное состояние лабиринта для возможности сброса"""
        if not self.workshop:
            return
        
        cells_data = []
        for y in range(self.workshop.height):
            row_data = []
            for x in range(self.workshop.width):
                cell = self.workshop.cells[y][x]
                row_data.append({
                    'type': cell.cell_type,
                    'robot': cell.has_robot
                })
            cells_data.append(row_data)
        
        self.initial_state = (self.workshop.width, self.workshop.height, cells_data)

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotDesignerGUI(root)
    root.mainloop()