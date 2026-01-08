from flask import Flask, render_template_string, jsonify, request
from enum import Enum, auto
from typing import Optional, List, Tuple
import json

app = Flask(__name__)

# HTML шаблон
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Робот-Механик</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .maze {
            display: inline-block;
            border: 2px solid #333;
            margin: 20px 0;
        }
        .row {
            display: flex;
        }
        .cell {
            width: 40px;
            height: 40px;
            border: 1px solid #ddd;
            position: relative;
            cursor: pointer;
        }
        .cell:hover {
            opacity: 0.8;
        }
        .robot {
            position: absolute;
            top: 10px;
            left: 10px;
            width: 20px;
            height: 20px;
            background: red;
            border-radius: 50%;
            border: 2px solid darkred;
        }
        .controls {
            margin: 20px 0;
            text-align: center;
        }
        .btn {
            padding: 10px 15px;
            margin: 5px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            background: #4CAF50;
            color: white;
            font-weight: bold;
        }
        .btn:hover {
            background: #45a049;
        }
        .btn-auto {
            background: #2196F3;
        }
        .btn-auto:hover {
            background: #0b7dda;
        }
        .type-select {
            padding: 5px;
            margin: 10px;
        }
        .status {
            padding: 10px;
            background: #e8f4fd;
            border-radius: 3px;
            margin: 10px 0;
        }
        .legend {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }
        .legend-item {
            display: flex;
            align-items: center;
        }
        .color-box {
            width: 20px;
            height: 20px;
            margin-right: 5px;
            border: 1px solid #666;
        }
        .instructions {
            font-size: 12px;
            color: #666;
            margin-top: 20px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Робот-Механик</h1>
        
        <div class="status" id="status">Готов к работе</div>
        
        <div class="controls">
            <select class="type-select" id="cellType">
                <option value="Floor">Пол</option>
                <option value="Detail">Деталь</option>
                <option value="Tool">Инструмент</option>
                <option value="Obstacle">Препятствие</option>
                <option value="Oil">Масло</option>
                <option value="Finish">Финиш</option>
            </select>
            
            <button class="btn" onclick="repair()">🔧 Ремонт</button>
            <button class="btn btn-auto" onclick="startAuto()">🤖 Автообход</button>
        </div>
        
        <div id="maze"></div>
        
        <div class="controls">
            <div style="margin-bottom: 10px;">
                <button class="btn" onclick="move('Forward')">↑ Вперед</button>
            </div>
            <div>
                <button class="btn" onclick="move('Left')">← Влево</button>
                <button class="btn" onclick="move('Right')">→ Вправо</button>
            </div>
            <div style="margin-top: 10px;">
                <button class="btn" onclick="move('Backward')">↓ Назад</button>
            </div>
            <div style="margin-top: 10px;">
                <button class="btn" onclick="move('DiagUp')">↖ Диаг. вверх</button>
                <button class="btn" onclick="move('DiagDown')">↘ Диаг. вниз</button>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item"><div class="color-box" style="background:white"></div>Пол</div>
            <div class="legend-item"><div class="color-box" style="background:lightblue"></div>Деталь</div>
            <div class="legend-item"><div class="color-box" style="background:lightgreen"></div>Отремонтировано</div>
            <div class="legend-item"><div class="color-box" style="background:yellow"></div>Инструмент</div>
            <div class="legend-item"><div class="color-box" style="background:gray"></div>Препятствие</div>
            <div class="legend-item"><div class="color-box" style="background:brown"></div>Масло</div>
            <div class="legend-item"><div class="color-box" style="background:pink"></div>Финиш</div>
            <div class="legend-item"><div class="color-box" style="background:#e0e0e0"></div>Посещено</div>
            <div class="legend-item"><div class="robot"></div>Робот</div>
        </div>
        
        <div class="instructions">
            <strong>Инструкция:</strong><br>
            • ЛКМ по клетке: изменить тип клетки<br>
            • Используйте кнопки для ручного управления роботом<br>
            • Нажмите "Автообход" для автоматического выполнения задачи<br>
            • Робот найдет и отремонтирует все детали, затем пойдет к финишу
        </div>
    </div>
    
    <script>
        let mazeData = [];
        let isAutoRunning = false;
        
        const colors = {
            'Floor': 'white',
            'Detail': 'lightblue',
            'Repaired': 'lightgreen',
            'Tool': 'yellow',
            'Obstacle': 'gray',
            'Oil': 'brown',
            'Finish': 'pink'
        };
        
        async function loadMaze() {
            const response = await fetch('/api/maze');
            const data = await response.json();
            mazeData = data.maze;
            renderMaze();
        }
        
        function renderMaze() {
            const container = document.getElementById('maze');
            container.innerHTML = '';
            
            const table = document.createElement('div');
            table.className = 'maze';
            
            for (let y = mazeData.height - 1; y >= 0; y--) {
                const row = document.createElement('div');
                row.className = 'row';
                
                for (let x = 0; x < mazeData.width; x++) {
                    const cell = mazeData.cells[x][y];
                    const cellDiv = document.createElement('div');
                    cellDiv.className = 'cell';
                    cellDiv.dataset.x = x;
                    cellDiv.dataset.y = y;
                    
                    if (cell.visited) {
                        cellDiv.style.backgroundColor = '#e0e0e0';
                    } else {
                        cellDiv.style.backgroundColor = colors[cell.type] || 'white';
                    }
                    
                    if (cell.robot) {
                        const robot = document.createElement('div');
                        robot.className = 'robot';
                        cellDiv.appendChild(robot);
                    }
                    
                    cellDiv.onclick = () => changeCellType(x, y);
                    row.appendChild(cellDiv);
                }
                
                table.appendChild(row);
            }
            
            container.appendChild(table);
        }
        
        async function changeCellType(x, y) {
            const type = document.getElementById('cellType').value;
            
            const response = await fetch('/api/change_cell', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({x, y, type})
            });
            
            const data = await response.json();
            mazeData = data.maze;
            renderMaze();
            updateStatus(data.status);
        }
        
        async function move(direction) {
            if (isAutoRunning) {
                updateStatus('Дождитесь завершения автообхода');
                return;
            }
            
            const response = await fetch('/api/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({direction})
            });
            
            const data = await response.json();
            mazeData = data.maze;
            renderMaze();
            updateStatus(data.status);
        }
        
        async function repair() {
            if (isAutoRunning) {
                updateStatus('Дождитесь завершения автообхода');
                return;
            }
            
            const response = await fetch('/api/repair', {
                method: 'POST'
            });
            
            const data = await response.json();
            mazeData = data.maze;
            renderMaze();
            updateStatus(data.status);
        }
        
        async function startAuto() {
            if (isAutoRunning) {
                updateStatus('Автообход уже выполняется');
                return;
            }
            
            isAutoRunning = true;
            document.getElementById('status').textContent = 'Запущен автоматический обход...';
            
            // Получаем план автообхода с сервера
            const response = await fetch('/api/get_auto_plan', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.plan) {
                // Выполняем план пошагово
                for (let step of data.plan) {
                    await executeStep(step);
                    await sleep(300); // Задержка для наглядности
                }
                
                mazeData = data.final_maze;
                renderMaze();
                updateStatus('Автоматический обход завершен!');
            } else {
                updateStatus('Ошибка при построении плана');
            }
            
            isAutoRunning = false;
        }
        
        async function executeStep(step) {
            if (step.type === 'move') {
                const response = await fetch('/api/move', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({direction: step.direction})
                });
                
                const data = await response.json();
                mazeData = data.maze;
                renderMaze();
                updateStatus(step.message);
            } else if (step.type === 'repair') {
                const response = await fetch('/api/repair', {
                    method: 'POST'
                });
                
                const data = await response.json();
                mazeData = data.maze;
                renderMaze();
                updateStatus(step.message);
            }
        }
        
        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
        
        function updateStatus(text) {
            document.getElementById('status').textContent = text;
        }
        
        // Загружаем лабиринт при старте
        loadMaze();
    </script>
</body>
</html>
'''

# --- Классы (упрощенные) ---
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
    def __init__(self, cell_type: WorkshopCellType, x: int = 0, y: int = 0):
        self.cell_type = cell_type
        self.has_robot = False
        self.x = x
        self.y = y
        self.visited = False
    
    def to_dict(self):
        return {
            'type': self.cell_type.name,
            'robot': self.has_robot,
            'visited': self.visited,
            'x': self.x,
            'y': self.y
        }

class Workshop:
    def __init__(self, width: int = 8, height: int = 6):
        self.width = width
        self.height = height
        self.cells = [[WorkshopCell(WorkshopCellType.Floor, x, y) 
                      for y in range(height)] for x in range(width)]
        self.setup_default()
    
    def setup_default(self):
        # Очищаем все ячейки
        for x in range(self.width):
            for y in range(self.height):
                self.cells[x][y] = WorkshopCell(WorkshopCellType.Floor, x, y)
        
        # Стартовая позиция робота
        self.cells[0][0].has_robot = True
        self.cells[0][0].visited = True
        
        # Детали для ремонта
        self.cells[2][2].cell_type = WorkshopCellType.Detail
        self.cells[5][3].cell_type = WorkshopCellType.Detail
        self.cells[4][5].cell_type = WorkshopCellType.Detail
        
        # Препятствия
        self.cells[3][2].cell_type = WorkshopCellType.Obstacle
        self.cells[4][4].cell_type = WorkshopCellType.Obstacle
        
        # Масло
        self.cells[6][2].cell_type = WorkshopCellType.Oil
        
        # Инструменты
        self.cells[2][5].cell_type = WorkshopCellType.Tool
        
        # Финиш
        self.cells[7][5].cell_type = WorkshopCellType.Finish
    
    def get_adjacent_cell(self, x: int, y: int, direction: WorkDirection):
        dx, dy = 0, 0
        
        if direction == WorkDirection.Forward:  # Вперед (север)
            dy = 1
        elif direction == WorkDirection.Backward:  # Назад (юг)
            dy = -1
        elif direction == WorkDirection.Left:  # Влево (запад)
            dx = -1
        elif direction == WorkDirection.Right:  # Вправо (восток)
            dx = 1
        elif direction == WorkDirection.DiagUp:  # Диаг. вверх (северо-запад)
            dx = -1
            dy = 1
        elif direction == WorkDirection.DiagDown:  # Диаг. вниз (юго-восток)
            dx = 1
            dy = -1
        
        nx, ny = x + dx, y + dy
        if 0 <= nx < self.width and 0 <= ny < self.height:
            return self.cells[nx][ny]
        return None
    
    def find_robot(self) -> Tuple[int, int]:
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].has_robot:
                    return x, y
        return 0, 0
    
    def find_all_details(self) -> List[Tuple[int, int]]:
        details = []
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].cell_type == WorkshopCellType.Detail:
                    details.append((x, y))
        return details
    
    def find_finish(self) -> Optional[Tuple[int, int]]:
        for x in range(self.width):
            for y in range(self.height):
                if self.cells[x][y].cell_type == WorkshopCellType.Finish:
                    return (x, y)
        return None
    
    def to_dict(self):
        return {
            'width': self.width,
            'height': self.height,
            'cells': [[self.cells[x][y].to_dict() for y in range(self.height)] 
                     for x in range(self.width)]
        }

# Глобальные переменные
workshop = Workshop()

# --- Улучшенный алгоритм поиска пути ---
def find_path(start: Tuple[int, int], target: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Находит путь от start до target с помощью BFS"""
    from collections import deque
    
    if start == target:
        return [start]
    
    visited = set()
    queue = deque()
    queue.append((start, []))  # (position, path)
    
    # Все возможные направления движения
    directions = [
        (1, 0, WorkDirection.Right),    # вправо
        (-1, 0, WorkDirection.Left),    # влево
        (0, 1, WorkDirection.Forward),  # вперед
        (0, -1, WorkDirection.Backward), # назад
        (-1, 1, WorkDirection.DiagUp),  # диаг. вверх
        (1, -1, WorkDirection.DiagDown) # диаг. вниз
    ]
    
    while queue:
        (x, y), path = queue.popleft()
        
        if (x, y) in visited:
            continue
        visited.add((x, y))
        
        new_path = path + [(x, y)]
        
        if (x, y) == target:
            return new_path  # Возвращаем путь включая стартовую позицию
        
        # Проверяем соседние клетки
        for dx, dy, direction in directions:
            nx, ny = x + dx, y + dy
            
            if 0 <= nx < workshop.width and 0 <= ny < workshop.height:
                cell = workshop.cells[nx][ny]
                # Можно проходить через пол, детали, инструменты, финиш
                if cell.cell_type not in (WorkshopCellType.Obstacle, WorkshopCellType.Oil):
                    if (nx, ny) not in visited:
                        queue.append(((nx, ny), new_path))
    
    return []  # Путь не найден

def convert_path_to_directions(path: List[Tuple[int, int]]) -> List[WorkDirection]:
    """Конвертирует путь в последовательность направлений"""
    directions = []
    
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 1 and dy == 0:
            directions.append(WorkDirection.Right)
        elif dx == -1 and dy == 0:
            directions.append(WorkDirection.Left)
        elif dx == 0 and dy == 1:
            directions.append(WorkDirection.Forward)
        elif dx == 0 and dy == -1:
            directions.append(WorkDirection.Backward)
        elif dx == -1 and dy == 1:
            directions.append(WorkDirection.DiagUp)
        elif dx == 1 and dy == -1:
            directions.append(WorkDirection.DiagDown)
    
    return directions

# API маршруты
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/maze')
def get_maze():
    return jsonify({'maze': workshop.to_dict()})

@app.route('/api/change_cell', methods=['POST'])
def change_cell():
    data = request.json
    x, y, type_name = data['x'], data['y'], data['type']
    
    # Не меняем клетку с роботом
    if workshop.cells[x][y].has_robot:
        return jsonify({
            'maze': workshop.to_dict(),
            'status': 'Нельзя изменить клетку с роботом'
        })
    
    workshop.cells[x][y].cell_type = WorkshopCellType[type_name]
    return jsonify({
        'maze': workshop.to_dict(),
        'status': f'Клетка ({x},{y}) изменена на {type_name}'
    })

@app.route('/api/move', methods=['POST'])
def move_robot():
    data = request.json
    direction = WorkDirection[data['direction']]
    
    x, y = workshop.find_robot()
    next_cell = workshop.get_adjacent_cell(x, y, direction)
    
    if next_cell is None:
        return jsonify({
            'maze': workshop.to_dict(),
            'status': 'Невозможно переместиться за пределы лабиринта'
        })
    
    if next_cell.cell_type in (WorkshopCellType.Obstacle, WorkshopCellType.Oil):
        return jsonify({
            'maze': workshop.to_dict(),
            'status': 'Препятствие на пути'
        })
    
    # Перемещаем робота
    workshop.cells[x][y].has_robot = False
    next_cell.has_robot = True
    next_cell.visited = True
    
    # Ремонт детали, если робот на ней
    if next_cell.cell_type == WorkshopCellType.Detail:
        next_cell.cell_type = WorkshopCellType.Repaired
        status = 'Робот перемещен, деталь отремонтирована'
    else:
        status = 'Робот перемещен'
    
    return jsonify({
        'maze': workshop.to_dict(),
        'status': status
    })

@app.route('/api/repair', methods=['POST'])
def repair_cell():
    x, y = workshop.find_robot()
    cell = workshop.cells[x][y]
    
    if cell.cell_type == WorkshopCellType.Detail:
        cell.cell_type = WorkshopCellType.Repaired
        status = 'Деталь отремонтирована'
    else:
        status = 'Здесь нет детали'
    
    return jsonify({
        'maze': workshop.to_dict(),
        'status': status
    })

@app.route('/api/get_auto_plan', methods=['POST'])
def get_auto_plan():
    """Строит план автоматического обхода"""
    plan = []
    
    # Находим текущую позицию робота
    start_x, start_y = workshop.find_robot()
    
    # Находим все детали
    details = workshop.find_all_details()
    
    # Находим финиш
    finish = workshop.find_finish()
    
    if not finish:
        return jsonify({'error': 'Финиш не найден'})
    
    current_pos = (start_x, start_y)
    
    # Посещаем все детали
    for detail in details:
        detail_x, detail_y = detail
        
        # Находим путь к детали
        path = find_path(current_pos, (detail_x, detail_y))
        if not path:
            continue
        
        # Конвертируем путь в направления
        directions = convert_path_to_directions(path)
        
        # Добавляем перемещения в план
        for direction in directions:
            plan.append({
                'type': 'move',
                'direction': direction.name,
                'message': f'Движение к детали в ({detail_x},{detail_y})'
            })
        
        # Добавляем ремонт детали
        plan.append({
            'type': 'repair',
            'message': f'Ремонт детали в ({detail_x},{detail_y})'
        })
        
        current_pos = (detail_x, detail_y)
    
    # Идем к финишу
    finish_x, finish_y = finish
    path_to_finish = find_path(current_pos, (finish_x, finish_y))
    
    if path_to_finish:
        directions = convert_path_to_directions(path_to_finish)
        
        for direction in directions:
            plan.append({
                'type': 'move',
                'direction': direction.name,
                'message': f'Движение к финишу в ({finish_x},{finish_y})'
            })
    
    # Создаем копию лабиринта для симуляции выполнения плана
    # (чтобы вернуть конечное состояние)
    import copy
    
    # Внимание: это упрощенная симуляция
    # В реальном приложении нужно было бы выполнять план шаг за шагом
    final_workshop = copy.deepcopy(workshop)
    
    # Симулируем выполнение плана
    robot_x, robot_y = start_x, start_y
    for step in plan:
        if step['type'] == 'move':
            direction = WorkDirection[step['direction']]
            next_cell = final_workshop.get_adjacent_cell(robot_x, robot_y, direction)
            if next_cell:
                final_workshop.cells[robot_x][robot_y].has_robot = False
                next_cell.has_robot = True
                next_cell.visited = True
                robot_x, robot_y = next_cell.x, next_cell.y
                
                # Ремонт детали при движении
                if next_cell.cell_type == WorkshopCellType.Detail:
                    next_cell.cell_type = WorkshopCellType.Repaired
        elif step['type'] == 'repair':
            cell = final_workshop.cells[robot_x][robot_y]
            if cell.cell_type == WorkshopCellType.Detail:
                cell.cell_type = WorkshopCellType.Repaired
    
    return jsonify({
        'plan': plan,
        'final_maze': final_workshop.to_dict()
    })

if __name__ == '__main__':
    app.run(debug=True, port=5005)
