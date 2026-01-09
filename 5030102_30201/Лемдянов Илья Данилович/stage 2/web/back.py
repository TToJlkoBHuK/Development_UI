# back.py
from flask import Flask, render_template, request, jsonify
import os
import sys
import copy
import threading
import traceback

proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from core import RobotMaze, RobotMiner, CellType

from mapping_executor import translate_and_exec

app = Flask(__name__, template_folder="templates", static_folder="static")

storage = {}

def create_session(sid):
    storage[sid] = {
        'current_state': None,
        'initial_state': None,
        'width': 0,
        'height': 0,
        'running': False,
        'finished': False,
        'last_error': None
    }
    return storage[sid]

def get_session(sid):
    if sid not in storage:
        create_session(sid)
    return storage[sid]


@app.route('/')
def index():
    sid = request.args.get('sid', '')
    return render_template('index.html', sid=sid)


@app.route('/upload_map', methods=['POST'])
def upload_map():
    try:
        file = request.files.get('file')
        if not file or file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400

        raw = file.read()
        try:
            content = raw.decode('utf-8')
        except Exception:
            try:
                content = raw.decode('latin-1')
            except Exception:
                content = raw.decode('utf-8', errors='replace')

        lines = [line.strip() for line in content.splitlines()
                 if line.strip() and not line.strip().startswith('#')]

        if not lines:
            return jsonify({'error': 'Файл пустой или все строки — комментарии'}), 400

        matrix = []
        for lineno, line in enumerate(lines, start=1):
            parts = line.split()
            if not parts:
                continue
            row = []
            for token in parts:
                t = token.strip().rstrip(',').lstrip(',')
                if t == '':
                    continue
                try:
                    if t.startswith(('0x', '0X')):
                        val = int(t, 16)
                    else:
                        val = int(t)
                except ValueError:
                    return jsonify({'error': f'Неправильный токен на строке {lineno}: "{t}"'}), 400

                if (val & 0x7) == CellType.MINE.value:
                    val = (val & 0xF8) | CellType.PATH.value
                row.append(val)
            matrix.append(row)

        lengths = {len(r) for r in matrix}
        if len(lengths) != 1:
            return jsonify({'error': 'Неправильная матрица: строки разной длины'}), 400


        bottom_first = matrix[::-1]
        width = len(bottom_first[0])
        height = len(bottom_first)


        maze = RobotMaze(width, height)
        maze.load_from_values(bottom_first)

        import hashlib
        sid = hashlib.md5(content.encode('utf-8', errors='replace')).hexdigest()[:12]
        session = create_session(sid)
        session['current_state'] = copy.deepcopy(bottom_first)
        session['initial_state'] = copy.deepcopy(bottom_first)
        session['width'] = width
        session['height'] = height

        return jsonify({'success': True, 'sid': sid, 'width': width, 'height': height})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@app.route('/get_maze')
def get_maze():
    sid = request.args.get('sid')
    if not sid or sid not in storage:
        return jsonify({'error': 'No map loaded'}), 400

    session = storage[sid]
    if not session.get('current_state'):
        return jsonify({'error': 'No map loaded'}), 400

    maze_values = session['current_state']
    maze = RobotMaze(session['width'], session['height'])
    maze.load_from_values(maze_values)

    cells = []
    for y in range(maze.height - 1, -1, -1):
        row = []
        for x in range(maze.width):
            c = maze.get_cell_by_coordinates(x, y)
            row.append({
                'type': c.cell_type.value,
                'type_name': c.cell_type.name,
                'has_robot': c.has_robot
            })
        cells.append(row)

    return jsonify({'width': maze.width, 'height': maze.height, 'cells': cells})


@app.route('/run_commands', methods=['POST'])
def run_commands():
    try:
        data = request.json or {}
        sid = data.get('sid')
        commands = data.get('commands', '')
        delay = float(data.get('delay', 0.0))

        if not sid or sid not in storage:
            return jsonify({'error': 'No map loaded'}), 400
        if not commands or not commands.strip():
            return jsonify({'error': 'No commands to execute'}), 400

        session = storage[sid]
        if session.get('running'):
            return jsonify({'error': 'Execution already in progress for this session'}), 409

        maze_values = session.get('current_state')
        if not maze_values:
            return jsonify({'error': 'No map loaded'}), 400

        session['running'] = True
        session['finished'] = False
        session['last_error'] = None

        def worker():
            try:
                maze = RobotMaze(session['width'], session['height'])
                maze.load_from_values(maze_values)
                robot = RobotMiner(maze)

                mapping_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mapping.yaml'))
                if not os.path.exists(mapping_path):
                    alt = os.path.abspath("mapping.yaml")
                    if os.path.exists(alt):
                        mapping_path = alt

                def on_step(*args, **kwargs):
                    try:
                        session['current_state'] = copy.deepcopy(maze.to_values())
                    except Exception as e:
                        print(f"[on_step] error: {e}")

                translate_and_exec(commands, mapping_path, robot, delay=delay, on_step=on_step)

                session['current_state'] = maze.to_values()
                session['finished'] = True
                session['running'] = False
                session['last_error'] = None
            except Exception as e:
                traceback.print_exc()
                session['last_error'] = str(e)
                session['running'] = False
                session['finished'] = False
                print(f"[worker] error for sid={sid}: {e}")

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        return jsonify({'success': True, 'started': True}), 202
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@app.route('/run_status')
def run_status():
    sid = request.args.get('sid')
    if not sid or sid not in storage:
        return jsonify({'error': 'No map loaded'}), 400
    s = storage[sid]
    return jsonify({'running': bool(s.get('running')), 'finished': bool(s.get('finished')), 'last_error': s.get('last_error')})


@app.route('/reset_maze', methods=['POST'])
def reset_maze():
    try:
        data = request.json or {}
        sid = data.get('sid')
        if not sid or sid not in storage:
            return jsonify({'error': 'No map loaded'}), 400
        session = storage[sid]
        if not session.get('initial_state'):
            return jsonify({'error': 'No initial state to reset to'}), 400

        session['current_state'] = copy.deepcopy(session['initial_state'])

        maze = RobotMaze(session['width'], session['height'])
        maze.load_from_values(session['current_state'])

        cells = []
        for y in range(maze.height - 1, -1, -1):
            row = []
            for x in range(maze.width):
                c = maze.get_cell_by_coordinates(x, y)
                row.append({'type': c.cell_type.value, 'type_name': c.cell_type.name, 'has_robot': c.has_robot})
            cells.append(row)

        return jsonify({'success': True, 'cells': cells, 'width': maze.width, 'height': maze.height})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5000)
