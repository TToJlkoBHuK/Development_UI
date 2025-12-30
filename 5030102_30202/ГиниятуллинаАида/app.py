from __future__ import annotations

from flask import Flask, render_template, request, jsonify
from typing import List, Optional, Tuple, Dict
from collections import deque
from enum import Enum

app = Flask(__name__)


class ТипЯчеекПроект(Enum):
    Пол = "Пол"
    Модуль = "Модуль"
    Инструмент = "Инструмент"
    Препятствие = "Препятствие"
    Финиш = "Финиш"
    Контур = "Контур"

class ТипНаправленийИнжНапр(Enum):
    ИнжВперёд = "ИнжВперёд"
    ИнжНазад = "ИнжНазад"
    ИнжЛево = "ИнжЛево"
    ИнжПраво = "ИнжПраво"
    ДиагИнжВ = "ДиагИнжВ"
    ДиагИнжН = "ДиагИнжН"

class Ячейка:
    def __init__(self, тип: ТипЯчеекПроект = ТипЯчеекПроект.Пол):
        self.тип = тип
        self.робот = False

class Лабиринт:
    def __init__(self, ширина=10, длина=8):
        self.ширина = ширина
        self.длина = длина
        self.поле: List[List[Ячейка]] = [[Ячейка() for _ in range(ширина)] for _ in range(длина)]
        self.поле[длина-1][ширина-1].тип = ТипЯчеекПроект.Финиш
        self.поле[0][0].робот = True

    def получить_соседа(self, x, y, направление):
        offsets = {
            "ИнжВперёд": (0, 1),
            "ИнжНазад": (0, -1),
            "ИнжЛево": (-1, 0),
            "ИнжПраво": (1, 0),
            "ДиагИнжВ": (-1, 1),
            "ДиагИнжН": (1, 1),
        }
        dx, dy = offsets[направление]
        nx, ny = x + dx, y + dy
        if 0 <= nx < self.ширина and 0 <= ny < self.длина:
            cell = self.поле[ny][nx]
            if cell.тип not in (ТипЯчеекПроект.Инструмент, ТипЯчеекПроект.Препятствие):
                return nx, ny
        return None

    def сериализовать(self):
        return [
            [
                {
                    "type": cell.тип.value,
                    "robot": cell.робот
                } for cell in row
            ] for row in self.поле
        ]

maze = Лабиринт()
running = False
current_path = []

def find_path(start_x, start_y, goal_x, goal_y):
    # Простой BFS
    queue = deque([(start_x, start_y, [])])
    visited = {(start_x, start_y)}
    while queue:
        x, y, path = queue.popleft()
        if x == goal_x and y == goal_y:
            return path
        for dir_name in ТипНаправленийИнжНапр:
            neigh = maze.получить_соседа(x, y, dir_name.value)
            if neigh and neigh not in visited:
                visited.add(neigh)
                queue.append((*neigh, path + [dir_name.value]))
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_maze')
def get_maze():
    return jsonify(maze.сериализовать())

@app.route('/click', methods=['POST'])
def click():
    data = request.json
    x = data['x']
    y = data['y']
    button = data['button']  # 'left' or 'right'

    if button == 'right':
        for row in maze.поле:
            for cell in row:
                cell.робот = False
        if maze.поле[y][x].тип not in (ТипЯчеекПроект.Инструмент, ТипЯчеекПроект.Препятствие):
            maze.поле[y][x].робот = True
    else:
        order = [ТипЯчеекПроект.Пол, ТипЯчеекПроект.Модуль, ТипЯчеекПроект.Инструмент,
                 ТипЯчеекПроект.Препятствие, ТипЯчеекПроект.Финиш, ТипЯчеекПроект.Контур]
        current = maze.поле[y][x].тип
        idx = order.index(current)
        maze.поле[y][x].тип = order[(idx + 1) % len(order)]

    return jsonify(maze.сериализовать())

@app.route('/step')
def step():
    robot_pos = None
    for yy in range(maze.длина):
        for xx in range(maze.ширина):
            if maze.поле[yy][xx].робот:
                robot_pos = (xx, yy)
                break
        if robot_pos:
            break

    if not robot_pos:
        return jsonify(maze.сериализовать())

    x, y = robot_pos

    if maze.поле[y][x].тип == ТипЯчеекПроект.Пол:
        maze.поле[y][x].тип = ТипЯчеекПроект.Модуль
    elif maze.поле[y][x].тип == ТипЯчеекПроект.Модуль:
        maze.поле[y][x].тип = ТипЯчеекПроект.Контур

    targets = [(xx, yy) for yy in range(maze.длина) for xx in range(maze.ширина)
               if maze.поле[yy][xx].тип in (ТипЯчеекПроект.Пол, ТипЯчеекПроект.Модуль)]

    if targets:
        best = min(targets, key=lambda t: len(find_path(x, y, t[0], t[1])) or float('inf'))
        path = find_path(x, y, best[0], best[1])
        if path:
            direction = path[0]
            neigh = maze.получить_соседа(x, y, direction)
            if neigh:
                maze.поле[y][x].робот = False
                nx, ny = neigh
                maze.поле[ny][nx].робот = True
    else:
        finish = (maze.ширина - 1, maze.длина - 1)
        if (x, y) != finish:
            path = find_path(x, y, finish[0], finish[1])
            if path:
                direction = path[0]
                neigh = maze.получить_соседа(x, y, direction)
                if neigh:
                    maze.поле[y][x].робот = False
                    nx, ny = neigh
                    maze.поле[ny][nx].робот = True

    return jsonify(maze.сериализовать())

@app.route('/run', methods=['POST'])
def run():
    global running
    running = not running
    return jsonify({"running": running})

@app.route('/reset')
def reset():
    global maze
    maze = Лабиринт()
    return jsonify(maze.сериализовать())

if __name__ == '__main__':
    app.run(debug=True)