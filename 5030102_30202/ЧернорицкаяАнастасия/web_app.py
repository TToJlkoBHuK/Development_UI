from flask import Flask, render_template, jsonify, request
import random
from main import ТипЯчеекРемесло, ТипНаправленийТехНапр, ЛабиринтРоботТехник, РоботТехник
import json

app = Flask(__name__)


class WebRobotGame:
    def __init__(self):
        self.labyrinth = None
        self.robot = None
        self.move_count = 0
        self.max_moves = 50
        self.game_id = None

    def create_random_labyrinth(self, game_id):
        width = 8
        height = 8

        self.labyrinth = ЛабиринтРоботТехник()
        self.labyrinth.ИнициализироватьЛабиринт(ТипЯчеекРемесло.Пол, width, height)
        self.move_count = 0
        self.game_id = game_id

        # Добавляем случайные объекты
        types = [
            ТипЯчеекРемесло.Оборуд,
            ТипЯчеекРемесло.Запчасть,
            ТипЯчеекРемесло.Барьер,
            ТипЯчеекРемесло.Склад
        ]

        for _ in range(10):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            if x != 0 or y != 0:  # Не ставим на стартовую позицию
                self.labyrinth.ячейки[y][x].тип_ячейки = random.choice(types)

        # Ставим финиш
        finish_x = width - 1
        finish_y = height - 1
        self.labyrinth.ячейки[finish_y][finish_x].тип_ячейки = ТипЯчеекРемесло.Финиш

        # Ставим робота в левый нижний угол
        start_x, start_y = 0, 0
        self.labyrinth.ячейки[start_y][start_x].ячейка_робота = True
        self.labyrinth.ячейки[start_y][start_x].тип_ячейки = ТипЯчеекРемесло.Пол

        self.robot = РоботТехник(self.labyrinth)

    def get_game_state(self):
        if not self.labyrinth or not self.robot:
            return None

        maze_data = []
        for y in range(self.labyrinth.длина):
            row = []
            for x in range(self.labyrinth.ширина):
                cell = self.labyrinth.ячейки[y][x]
                row.append({
                    'type': cell.тип_ячейки.value if cell.тип_ячейки else 'Пол',
                    'has_robot': cell.ячейка_робота
                })
            maze_data.append(row)

        current = self.robot.текущая_ячейка
        return {
            'maze': maze_data,
            'position': {'x': current.x, 'y': current.y},
            'cell_type': current.тип_ячейки.value if current.тип_ячейки else 'Неизвестно',
            'moves': f"{self.move_count}/{self.max_moves}",
            'status': 'Победа!' if self.robot.ЗавершитьРаботу() else 'В работе',
            'can_finish': self.robot.ЗавершитьРаботу(),
            'moves_left': self.max_moves - self.move_count,
            'game_over': self.move_count >= self.max_moves
        }

    def move_robot(self, direction):
        if not self.robot or self.move_count >= self.max_moves:
            return False, "Лимит ходов исчерпан или игра окончена"

        result = self.robot.Перейти(direction)
        if result:
            self.move_count += 1
            return True, "Успешное перемещение"
        else:
            return False, "Невозможно переместиться в этом направлении"

    def repair_equipment(self):
        if self.robot:
            self.robot.Оборуд()
            return True
        return False

    def take_part(self):
        if self.robot:
            self.robot.Запчасть()
            return True
        return False


games = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/new_game', methods=['POST'])
def new_game():
    game_id = str(random.randint(1000, 9999))
    game = WebRobotGame()
    game.create_random_labyrinth(game_id)
    games[game_id] = game

    return jsonify({
        'success': True,
        'game_id': game_id,
        'state': game.get_game_state()
    })


@app.route('/api/game_state/<game_id>', methods=['GET'])
def game_state(game_id):
    if game_id not in games:
        return jsonify({'success': False, 'error': 'Игра не найдена'})

    game = games[game_id]
    return jsonify({
        'success': True,
        'state': game.get_game_state()
    })


@app.route('/api/move/<game_id>', methods=['POST'])
def move(game_id):
    if game_id not in games:
        return jsonify({'success': False, 'error': 'Игра не найдена'})

    data = request.json
    direction_map = {
        'forward': ТипНаправленийТехНапр.ТехВперед,
        'backward': ТипНаправленийТехНапр.ТехНазад,
        'left': ТипНаправленийТехНапр.ТехЛево,
        'right': ТипНаправленийТехНапр.ТехПраво,
        'upleft': ТипНаправленийТехНапр.ДиагТВ,
        'downright': ТипНаправленийТехНапр.ДиагТН  # Исправлено на правильное направление
    }

    direction = direction_map.get(data.get('direction'))
    if not direction:
        return jsonify({'success': False, 'error': 'Неверное направление'})

    game = games[game_id]
    success, message = game.move_robot(direction)

    return jsonify({
        'success': success,
        'message': message,
        'state': game.get_game_state()
    })


@app.route('/api/repair/<game_id>', methods=['POST'])
def repair(game_id):
    if game_id not in games:
        return jsonify({'success': False, 'error': 'Игра не найдена'})

    game = games[game_id]
    success = game.repair_equipment()

    return jsonify({
        'success': success,
        'state': game.get_game_state()
    })


@app.route('/api/take_part/<game_id>', methods=['POST'])
def take_part(game_id):
    if game_id not in games:
        return jsonify({'success': False, 'error': 'Игра не найдена'})

    game = games[game_id]
    success = game.take_part()

    return jsonify({
        'success': success,
        'state': game.get_game_state()
    })


@app.route('/api/reset/<game_id>', methods=['POST'])
def reset_game(game_id):
    if game_id not in games:
        return jsonify({'success': False, 'error': 'Игра не найдена'})

    game = games[game_id]
    game.create_random_labyrinth(game_id)

    return jsonify({
        'success': True,
        'state': game.get_game_state()
    })


if __name__ == '__main__':
    app.run(debug=True, port=8596)