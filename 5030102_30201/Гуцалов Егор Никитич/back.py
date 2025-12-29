from flask import Flask, request, jsonify
from flask_cors import CORS
from enum import Enum, auto
from typing import Optional, List, Iterator
import threading
import time
import json
import os
from werkzeug.utils import secure_filename
import copy

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['UPLOAD_FOLDER'] = '/tmp'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class AppState:
    def __init__(self):
        self.workshop = None
        self.robot = None
        self.initial_state = None
        self.status = "idle"
        self.message = "Ожидание загрузки карты"
        self.lock = threading.Lock()
        self.iterator = None
        self.solving_thread = None
        self.should_stop = False
        self.current_step = 0
        self.total_steps = 0

app_state = AppState()

class WorkshopCellType(Enum):
    Canvas = 1
    Sketch = 2
    Ready = 3
    Tool = 4
    Void = 5
    Finish = 6
    Collection = 7

    def to_json(self):
        return self.name

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
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "cell_type": self.cell_type.to_json(),
            "has_robot": self.has_robot
        }

    def copy(self):
        return WorkshopCell(self.cell_type, self.has_robot, self.x, self.y)

class Workshop:
    def __init__(self, width: int, height: int, cells: Optional[List[List[WorkshopCell]]] = None):
        self.width = width
        self.height = height
        if cells is None:
            self.cells = [[WorkshopCell(x=x, y=y) for x in range(width)] for y in range(height)]
        else:
            self.cells = cells

    def to_dict(self):
        cells_data = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(self.cells[y][x].to_dict())
            cells_data.append(row)
        
        return {
            "width": self.width,
            "height": self.height,
            "cells": cells_data
        }

    def copy(self):
        new_cells = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(self.cells[y][x].copy())
            new_cells.append(row)
        return Workshop(self.width, self.height, new_cells)

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
        self.returned_cells = 0  

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
        self.returned_cells += 1
        return current_cell
    
    def get_total_cells(self):
        return self.width * self.height
    
    def get_current_position(self):
        return self.current_x, self.current_y, self.moving_right, self.finished

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

    def execute_task_step(self, visual_callback=None):
        """
        Выполняет один шаг задачи, возвращает True если задача продолжается,
        False если задача завершена (достигнут финиш или все ячейки обработаны)
        """
        if app_state.iterator is None:
            app_state.iterator = self.workshop.get_snake_iterator()
            app_state.total_steps = app_state.iterator.get_total_cells()
        
        try:
            cell = next(app_state.iterator)
            app_state.current_step += 1
            
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
                    app_state.iterator = None  
                    return False  
            
            if visual_callback:
                visual_callback()
            
            return True 
            
        except StopIteration:
            app_state.iterator = None
            return False

def save_initial_state():
    if not app_state.workshop:
        return
    
    cells_data = []
    for y in range(app_state.workshop.height):
        row_data = []
        for x in range(app_state.workshop.width):
            cell = app_state.workshop.cells[y][x]
            row_data.append({
                'type': cell.cell_type,
                'robot': cell.has_robot
            })
        cells_data.append(row_data)
    
    app_state.initial_state = {
        'width': app_state.workshop.width,
        'height': app_state.workshop.height,
        'cells': cells_data
    }

def reset_workshop_from_initial():
    if not app_state.initial_state:
        return False
    
    width = app_state.initial_state['width']
    height = app_state.initial_state['height']
    cells_data = app_state.initial_state['cells']
    
    app_state.workshop = Workshop(width, height)
    for y in range(height):
        for x in range(width):
            cell_data = cells_data[y][x]
            app_state.workshop.cells[y][x].cell_type = cell_data['type']
            app_state.workshop.cells[y][x].has_robot = cell_data['robot']
            app_state.workshop.cells[y][x].x = x
            app_state.workshop.cells[y][x].y = y
    
    app_state.robot = DesignerRobot(app_state.workshop)
    return True

@app.route('/api/state', methods=['GET'])
def get_state():
    with app_state.lock:
        if app_state.workshop is None:
            return jsonify({
                "status": "idle",
                "message": "Карта не загружена",
                "workshop": None,
                "current_step": 0,
                "total_steps": 0
            })
        
        return jsonify({
            "status": app_state.status,
            "message": app_state.message,
            "workshop": app_state.workshop.to_dict() if app_state.workshop else None,
            "current_step": app_state.current_step,
            "total_steps": app_state.total_steps
        })

@app.route('/api/load_map', methods=['POST'])
def load_map():
    if 'file' not in request.files:
        return jsonify({"error": "Файл не найден"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Пустое имя файла"}), 400
    
    if not file.filename.endswith('.txt'):
        return jsonify({"error": "Неверный формат файла. Требуется .txt"}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        if not lines:
            return jsonify({"error": "Файл пустой"}), 400
        
        width = len(lines[0].split())
        height = len(lines)
        
        for i, line in enumerate(lines[1:], 1):
            if len(line.split()) != width:
                return jsonify({"error": f"Несоответствие размеров в строке {i+1}"}), 400
        
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
        
        workshop = Workshop(width, height)
        workshop.initialize_workshop(WorkshopCellType.Ready)
        snake_iter = workshop.get_snake_iterator()
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
        
        with app_state.lock:
            app_state.workshop = workshop
            app_state.robot = DesignerRobot(app_state.workshop)
            app_state.status = "idle"
            app_state.message = f"Карта загружена: {width}x{height}"
            app_state.current_step = 0
            app_state.total_steps = 0
            app_state.iterator = None  
            save_initial_state()
        
        return jsonify({
            "success": True,
            "message": f"Карта загружена: {width}x{height}",
            "workshop": workshop.to_dict()
        })
    
    except Exception as e:
        return jsonify({"error": f"Ошибка загрузки карты: {str(e)}"}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/api/solve', methods=['POST'])
def solve_maze():
    with app_state.lock:
        if app_state.workshop is None or app_state.robot is None:
            return jsonify({"error": "Сначала загрузите карту"}), 400
        
        if app_state.status == "solving":
            return jsonify({"error": "Робот уже выполняет задачу"}), 400
    
    def run_solution():
        with app_state.lock:
            temp_iterator = app_state.workshop.get_snake_iterator()
            app_state.total_steps = temp_iterator.get_total_cells()
            app_state.current_step = 0
            app_state.status = "solving"
            app_state.message = "Решение задачи..."
            app_state.should_stop = False
            app_state.iterator = None  
        
        try:
            while not app_state.should_stop:
                with app_state.lock:
                    if app_state.should_stop:
                        break
                
                should_continue = app_state.robot.execute_task_step(visual_callback=lambda: time.sleep(0.1))
                
                with app_state.lock:
                    if not should_continue or app_state.should_stop:
                        if not app_state.should_stop:
                            app_state.status = "idle"
                            app_state.message = "Задача успешно решена!"
                        break
                
                time.sleep(0.2)
                
        except Exception as e:
            with app_state.lock:
                app_state.status = "error"
                app_state.message = f"Ошибка при решении: {str(e)}"
                app_state.iterator = None
        
        if app_state.should_stop:
            with app_state.lock:
                app_state.status = "idle"
                app_state.message = "Решение остановлено пользователем"
                app_state.iterator = None
    
    if app_state.solving_thread and app_state.solving_thread.is_alive():
        app_state.should_stop = True
        app_state.solving_thread.join(timeout=1.0)
    
    app_state.solving_thread = threading.Thread(target=run_solution, daemon=True)
    app_state.solving_thread.start()
    
    return jsonify({
        "success": True, 
        "message": "Запущено решение задачи",
        "total_steps": app_state.total_steps
    })

@app.route('/api/stop', methods=['POST'])
def stop_solving():
    with app_state.lock:
        if app_state.status == "solving":
            app_state.should_stop = True
            app_state.status = "idle"
            app_state.message = "Решение остановлено пользователем"
            app_state.iterator = None
            return jsonify({"success": True, "message": "Решение остановлено"})
        return jsonify({"error": "Робот не выполняет задачу"}), 400

@app.route('/api/reset', methods=['POST'])
def reset_maze():
    if not app_state.initial_state:
        return jsonify({"error": "Нет сохраненного состояния для сброса"}), 400
    
    if not reset_workshop_from_initial():
        return jsonify({"error": "Ошибка сброса состояния"}), 500
    
    with app_state.lock:
        app_state.status = "idle"
        app_state.message = "Лабиринт сброшен к начальному состоянию"
        app_state.current_step = 0
        app_state.total_steps = 0
        app_state.iterator = None
    
    return jsonify({
        "success": True,
        "message": "Лабиринт сброшен",
        "workshop": app_state.workshop.to_dict()
    })

@app.route('/api/legend', methods=['GET'])
def get_legend():
    return jsonify({
        "cell_colors": {
            "Canvas": '#FFE082',    
            "Sketch": '#FFB300',    
            "Ready": '#4CAF50',     
            "Tool": '#9E9E9E',      
            "Void": '#212121',      
            "Finish": '#9C27B0',    
            "Collection": '#2196F3', 
        },
        "robot_color": '#E53935'
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Server is running on port 8080"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)