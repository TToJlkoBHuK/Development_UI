from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import time
from enum import Enum
from typing import Optional, List, Tuple
import json

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


class ТипЯчеекСетей(Enum):
    """Типы ячеек сетки"""
    Пусто = 0
    Труба = 1
    Соединено = 2
    Подвал = 3
    Стена = 4
    Вода = 5
    Финиш = 6


class ЛабиринтРоботСантехник:
    """Класс лабиринта (сетки)"""

    def __init__(self, ширина: int, длина: int, ячейки: list):
        self.ширина = ширина
        self.длина = длина
        self.ячейки = ячейки


class ЯчейкаРоботСантехник:
    """Класс ячейки"""

    def __init__(self, ячейка_робота: bool, тип_ячейки: int):
        self.ячейка_робота = ячейка_робота
        self.тип_ячейки = тип_ячейки

    def to_dict(self):
        return {
            'ячейка_робота': self.ячейка_робота,
            'тип_ячейки': self.тип_ячейки
        }


class РоботСантехник:
    """Главный класс робота-сантехника"""

    def __init__(self, лабиринт: ЛабиринтРоботСантехник):
        self.лабиринт = лабиринт
        self.ширина = лабиринт.ширина
        self.длина = лабиринт.длина
        self.ячейки = лабиринт.ячейки
        self.текущая_позиция = [0, 0]

    def ответил(self):
        """Проверить текущую ячейку"""
        return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]

    def сдвинуть_влево(self):
        """Двигаться влево"""
        if self.текущая_позиция[0] > 0:
            next_cell = self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0] - 1]
            if next_cell.тип_ячейки not in [ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value]:
                self.текущая_позиция[0] -= 1
                return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        return None

    def сдвинуть_вправо(self):
        """Двигаться вправо"""
        if self.текущая_позиция[0] < self.ширина - 1:
            next_cell = self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0] + 1]
            if next_cell.тип_ячейки not in [ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value]:
                self.текущая_позиция[0] += 1
                return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        return None

    def подняться_по_диагр(self):
        """Двигаться вверх"""
        if self.текущая_позиция[1] < self.длина - 1:
            next_cell = self.ячейки[self.текущая_позиция[1] + 1][self.текущая_позиция[0]]
            if next_cell.тип_ячейки not in [ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value]:
                self.текущая_позиция[1] += 1
                return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        return None

    def спуститься_по_диагр(self):
        """Двигаться вниз"""
        if self.текущая_позиция[1] > 0:
            next_cell = self.ячейки[self.текущая_позиция[1] - 1][self.текущая_позиция[0]]
            if next_cell.тип_ячейки not in [ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value]:
                self.текущая_позиция[1] -= 1
                return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        return None

    def пусто(self):
        """Обработка ячейки типа Пусто: Пусто → Труба"""
        current_cell = self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        if current_cell.тип_ячейки == ТипЯчеекСетей.Пусто.value:
            current_cell.тип_ячейки = ТипЯчеекСетей.Труба.value

    def труба(self):
        """Обработка ячейки типа Труба: Труба → Соединено"""
        current_cell = self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        if current_cell.тип_ячейки == ТипЯчеекСетей.Труба.value:
            current_cell.тип_ячейки = ТипЯчеекСетей.Соединено.value

    def get_state(self):
        """Получить состояние для отправки клиенту"""
        return {
            'ширина': self.ширина,
            'длина': self.длина,
            'ячейки': [[cell.to_dict() for cell in row] for row in self.ячейки],
            'текущая_позиция': self.текущая_позиция
        }


def создать_тестовую_сетку(ширина, длина):
    """Создать тестовую сетку"""
    ячейки = []

    for y in range(длина):
        строка = []
        for x in range(ширина):
            if x == 0 and y == 0:
                строка.append(ЯчейкаРоботСантехник(True, ТипЯчеекСетей.Пусто.value))
            elif x == ширина - 1 and y == длина - 1:
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Финиш.value))
            elif (x == 2 and y == 1) or (x == 3 and y == 2):
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Стена.value))
            elif x == 1 and y == 2:
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Вода.value))
            elif (x + y) % 3 == 0:
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Труба.value))
            else:
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Пусто.value))

        ячейки.append(строка)

    return ячейки


# Глобальный робот
ширина = 7
длина = 5
ячейки = создать_тестовую_сетку(ширина, длина)
лабиринт = ЛабиринтРоботСантехник(ширина, длина, ячейки)
робот = РоботСантехник(лабиринт)


def _свободна(xn, yn):
    if not (0 <= xn < робот.ширина and 0 <= yn < робот.длина):
        return False
    t = робот.ячейки[yn][xn].тип_ячейки
    return t not in (ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value)


def _найти_ближайшую_цель():
    targets = []
    for y in range(робот.длина):
        for x in range(робот.ширина):
            t = робот.ячейки[y][x].тип_ячейки
            if t in (ТипЯчеекСетей.Пусто.value, ТипЯчеекСетей.Труба.value):
                targets.append((x, y))
    if targets:
        return targets
    for y in range(робот.длина):
        for x in range(робот.ширина):
            if робот.ячейки[y][x].тип_ячейки == ТипЯчеекСетей.Финиш.value:
                return [(x, y)]
    return []


def _bfs_следующий_шаг(start, goals):
    from collections import deque
    goals = set(goals)

    q = deque([start])
    prev = {start: None}

    while q:
        x, y = q.popleft()
        if (x, y) in goals:
            cur = (x, y)
            while prev[cur] is not None and prev[cur] != start:
                cur = prev[cur]
            return cur if cur != start else None

        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in prev and _свободна(nx, ny):
                prev[(nx, ny)] = (x, y)
                q.append((nx, ny))

    return None


def переместить_робота():
    x, y = робот.текущая_позиция
    goals = _найти_ближайшую_цель()
    if not goals:
        return False, "Целей нет"

    nxt = _bfs_следующий_шаг((x, y), goals)
    if nxt is None:
        return False, "Путь не найден"

    nx, ny = nxt
    if nx == x + 1:
        return робот.сдвинуть_вправо() is not None, "Движение вправо"
    if nx == x - 1:
        return робот.сдвинуть_влево() is not None, "Движение влево"
    if ny == y + 1:
        return робот.подняться_по_диагр() is not None, "Движение вверх"
    if ny == y - 1:
        return робот.спуститься_по_диагр() is not None, "Движение вниз"

    return False, "Нет движения"


@app.route('/api/state', methods=['GET'])
def get_state():
    """Получить текущее состояние"""
    return jsonify(робот.get_state())


@app.route('/api/reset', methods=['POST'])
def reset():
    """Сбросить лабиринт"""
    global робот, лабиринт, ячейки
    ячейки = создать_тестовую_сетку(ширина, длина)
    лабиринт = ЛабиринтРоботСантехник(ширина, длина, ячейки)
    робот = РоботСантехник(лабиринт)
    return jsonify(робот.get_state())


@app.route('/api/step', methods=['POST'])
def step():
    """Сделать один шаг"""
    current_cell = робот.ответил()
    x, y = робот.текущая_позиция
    message = ""

    if current_cell.тип_ячейки == ТипЯчеекСетей.Пусто.value:
        робот.пусто()
        message = f"Позиция ({x}, {y}): Пусто → Труба"
    elif current_cell.тип_ячейки == ТипЯчеекСетей.Труба.value:
        робот.труба()
        message = f"Позиция ({x}, {y}): Труба → Соединено"
    elif current_cell.тип_ячейки == ТипЯчеекСетей.Финиш.value:
        message = f"Позиция ({x}, {y}): ФИНИШ! Работа завершена!"
        return jsonify({'state': робот.get_state(), 'message': message, 'finished': True})
    else:
        message = f"Позиция ({x}, {y}): Ячейка не требует обработки"

    success, move_msg = переместить_робота()

    return jsonify({
        'state': робот.get_state(),
        'message': message + " | " + move_msg,
        'finished': False
    })


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
