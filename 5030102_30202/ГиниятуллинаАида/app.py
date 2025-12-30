from __future__ import annotations

from flask import Flask, render_template, jsonify, request  # Добавлен request
from typing import List, Tuple, Optional
from collections import deque
from enum import Enum
import math

app = Flask(__name__)


class ТипЯчеекПроект(Enum):
    Пол = "Пол"
    Модуль = "Модуль"
    Инструмент = "Инструмент"
    Препятствие = "Препятствие"
    Финиш = "Финиш"
    Контур = "Контур"


class Ячейка:
    def __init__(self, тип: ТипЯчеекПроект = ТипЯчеекПроект.Пол):
        self.тип = тип
        self.робот = False


class Лабиринт:
    def __init__(self, ширина: int = 10, длина: int = 8):
        self.ширина = ширина
        self.длина = длина
        self.поле: List[List[Ячейка]] = [[Ячейка() for _ in range(ширина)] for _ in range(длина)]
        self.поле[длина - 1][ширина - 1].тип = ТипЯчеекПроект.Финиш
        self.поле[0][0].робот = True

    def получить_соседа(self, x: int, y: int, направление: str) -> Optional[Tuple[int, int]]:
        offsets = {
            "ИнжВперёд": (0, 1),  # вниз
            "ИнжНазад": (0, -1),  # вверх
            "ИнжЛево": (-1, 0),  # влево
            "ИнжПраво": (1, 0),  # вправо
            "ДиагИнжВ": (-1, 1),  # влево-вниз
            "ДиагИнжН": (1, 1),  # вправо-вниз
        }
        dx, dy = offsets.get(направление, (0, 0))
        nx, ny = x + dx, y + dy
        if 0 <= nx < self.ширина and 0 <= ny < self.длина:
            cell = self.поле[ny][nx]
            if cell.тип not in (ТипЯчеекПроект.Инструмент, ТипЯчеекПроект.Препятствие):
                return nx, ny
        return None

    def сериализовать(self):
        return [
            [
                {"type": cell.тип.value, "robot": cell.робот}
                for cell in row
            ]
            for row in self.поле
        ]


maze = Лабиринт()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_maze')
def get_maze():
    return jsonify({"maze": maze.сериализовать(), "status": "Готово"})


@app.route('/click', methods=['POST'])
def click():
    data = request.json
    x = data['x']
    y = data['y']
    button = data['button']

    if button == 'right':
        for row in maze.поле:
            for cell in row:
                cell.робот = False
        if maze.поле[y][x].тип not in (ТипЯчеекПроект.Инструмент, ТипЯчеекПроект.Препятствие):
            maze.поле[y][x].робот = True
    else:
        order = [
            ТипЯчеекПроект.Пол,
            ТипЯчеекПроект.Модуль,
            ТипЯчеекПроект.Инструмент,
            ТипЯчеекПроект.Препятствие,
            ТипЯчеекПроект.Финиш,
            ТипЯчеекПроект.Контур,
        ]
        current = maze.поле[y][x].тип
        idx = order.index(current)
        maze.поле[y][x].тип = order[(idx + 1) % len(order)]

    return jsonify({"maze": maze.сериализовать(), "status": "Изменено"})


def найти_путь_к_цели(start_x: int, start_y: int, target_x: int, target_y: int) -> Optional[str]:
    """Находит направление для движения к цели с использованием BFS"""
    if (start_x, start_y) == (target_x, target_y):
        return None

    # Приоритет направлений (сначала прямые, потом диагонали)
    directions = [
        ("ИнжПраво", (1, 0)),
        ("ИнжЛево", (-1, 0)),
        ("ИнжВперёд", (0, 1)),
        ("ИнжНазад", (0, -1)),
        ("ДиагИнжН", (1, 1)),
        ("ДиагИнжВ", (-1, 1)),
    ]

    # Простой поиск: выбираем направление, которое приближает к цели
    best_dir = None
    min_dist = float('inf')

    for dir_name, (dx, dy) in directions:
        nx, ny = start_x + dx, start_y + dy
        if 0 <= nx < maze.ширина and 0 <= ny < maze.длина:
            cell = maze.поле[ny][nx]
            if cell.тип in (ТипЯчеекПроект.Инструмент, ТипЯчеекПроект.Препятствие):
                continue
            dist = abs(nx - target_x) + abs(ny - target_y)
            if dist < min_dist:
                min_dist = dist
                best_dir = dir_name

    return best_dir


@app.route('/step')
def step():
    # Находим позицию робота
    robot_pos = None
    for y in range(maze.длина):
        for x in range(maze.ширина):
            if maze.поле[y][x].робот:
                robot_pos = (x, y)
                break
        if robot_pos:
            break

    if not robot_pos:
        return jsonify({"maze": maze.сериализовать(), "status": "Робот не найден", "finished": True})

    x, y = robot_pos

    # Обработка текущей клетки
    if maze.поле[y][x].тип == ТипЯчеекПроект.Пол:
        maze.поле[y][x].тип = ТипЯчеекПроект.Модуль
    elif maze.поле[y][x].тип == ТипЯчеекПроект.Модуль:
        maze.поле[y][x].тип = ТипЯчеекПроект.Контур

    # Проверяем, остались ли необработанные клетки
    targets_left = False
    for row in maze.поле:
        for cell in row:
            if cell.тип in (ТипЯчеекПроект.Пол, ТипЯчеекПроект.Модуль):
                targets_left = True
                break
        if targets_left:
            break

    # Если нет целей и робот на финише - завершаем
    if not targets_left and (x, y) == (maze.ширина - 1, maze.длина - 1):
        return jsonify({
            "maze": maze.сериализовать(),
            "status": "Задача завершена!",
            "finished": True
        })

    # Находим цель
    if targets_left:
        # Находим ближайшую необработанную клетку
        targets = []
        for yy in range(maze.длина):
            for xx in range(maze.ширина):
                if maze.поле[yy][xx].тип in (ТипЯчеекПроект.Пол, ТипЯчеекПроект.Модуль):
                    targets.append((xx, yy))

        # Выбираем цель с минимальным расстоянием
        tx, ty = min(targets, key=lambda t: abs(t[0] - x) + abs(t[1] - y))
    else:
        # Двигаемся к финишу
        tx, ty = maze.ширина - 1, maze.длина - 1

    # Находим направление для движения
    direction = найти_путь_к_цели(x, y, tx, ty)

    if direction:
        # Пытаемся сделать шаг в выбранном направлении
        new_pos = maze.получить_соседа(x, y, direction)
        if new_pos:
            nx, ny = new_pos
            maze.поле[y][x].робот = False
            maze.поле[ny][nx].робот = True
            status = "Выполняется..."
        else:
            status = "Не могу двигаться в этом направлении"
    else:
        status = "На месте"

    # Проверяем завершение после движения
    if not targets_left and (nx if direction else x, ny if direction else y) == (maze.ширина - 1, maze.длина - 1):
        status = "Задача завершена!"
        return jsonify({
            "maze": maze.сериализовать(),
            "status": status,
            "finished": True
        })

    return jsonify({
        "maze": maze.сериализовать(),
        "status": status,
        "finished": False
    })


@app.route('/run', methods=['POST'])
def run_toggle():
    return jsonify({"running": True})


@app.route('/reset')
def reset():
    global maze
    maze = Лабиринт()
    return jsonify({"maze": maze.сериализовать(), "status": "Сброшено"})


@app.route('/demo')
def demo():
    global maze
    maze = Лабиринт()

    # Демо-лабиринт
    for x in range(2, 8):
        maze.поле[3][x].тип = ТипЯчеекПроект.Препятствие
    maze.поле[2][3].тип = ТипЯчеекПроект.Инструмент
    maze.поле[1][1].тип = ТипЯчеекПроект.Модуль
    maze.поле[1][8].тип = ТипЯчеекПроект.Модуль
    maze.поле[5][2].тип = ТипЯчеекПроект.Пол
    maze.поле[6][5].тип = ТипЯчеекПроект.Пол
    maze.поле[4][7].тип = ТипЯчеекПроект.Пол

    return jsonify({"maze": maze.сериализовать(), "status": "Демо загружено"})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
