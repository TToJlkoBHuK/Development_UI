import tkinter as tk
from shelve import Shelf
from tkinter import filedialog, messagebox
import threading
from core import RobotMaze, RobotMiner, CellType
from typing import List
from mapping_executor import translate_and_exec
import os

class MinerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Miner")
        self.root.geometry("1200x720")
        self.cell_colors = {
            CellType.PATH: '#D0D7DE',
            CellType.ORE: '#FFB74D',
            CellType.PROCESSED: '#81C784',
            CellType.SHAFT: '#455A64',
            CellType.DANGEROUS: '#E53935',
            CellType.FINISH: '#8E24AA',
        }
        self.cell_symbols = {
            CellType.PATH: 'P',
            CellType.ORE: 'O',
            CellType.PROCESSED: '✓',
            CellType.SHAFT: '#',
            CellType.DANGEROUS: '!',
            CellType.FINISH: 'F',
        }
        self.robot_color = '#FF5252'
        self.workshop: RobotMaze = None
        self.robot: RobotMiner = None
        self.cell_size = 40
        self.delay = 0.25
        self.create_widgets()
        self.initial_state = None

    def create_widgets(self):
        self.root.configure(bg='#0f1724')
        main_frame = tk.Frame(self.root, bg='#0f1724')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        left_panel = tk.Frame(main_frame, bg='#123047')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,8))
        right_panel = tk.Frame(main_frame, bg='#e9eef2', width=360)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        top_bar = tk.Frame(left_panel, bg='#0f1724', height=64)
        top_bar.pack(fill=tk.X, padx=10, pady=10)
        title = tk.Label(top_bar, text="Robot Miner", bg='#0f1724', fg='#E6F0FF', font=('Helvetica', 18, 'bold'))
        title.pack(side=tk.LEFT, padx=6)
        left_buttons = tk.Frame(top_bar, bg='#0f1724')
        left_buttons.pack(side=tk.RIGHT, padx=6)
        load_btn = tk.Button(left_buttons, text="Load Map", command=self.load_map, bg='#4DD0E1', fg='black', width=12, bd=0)
        load_btn.pack(side=tk.LEFT, padx=6)
        reset_btn = tk.Button(left_buttons, text="Reset", command=self.reset_maze, bg='#FF8A65', fg='black', width=10, bd=0)
        reset_btn.pack(side=tk.LEFT, padx=6)
        run_big_btn = tk.Button(top_bar, text="RUN", command=self.run_commands, bg='#43A047', fg='white', width=8, height=1, font=('Helvetica', 12, 'bold'), bd=0)
        run_big_btn.pack(side=tk.RIGHT, padx=8)
        canvas_frame = tk.Frame(left_panel, bg='#102332', bd=2, relief=tk.RIDGE)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,12))
        self.canvas = tk.Canvas(canvas_frame, bg='#0b1a26', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        control_frame = tk.Frame(right_panel, bg='#e9eef2')
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        cmds_label = tk.Label(control_frame, text="Commands", bg='#e9eef2', fg='#102332', font=('Helvetica', 12, 'bold'))
        cmds_label.pack(anchor=tk.W)
        self.commands_text = tk.Text(control_frame, height=10, width=40, bg='white', fg='black', bd=1)
        self.commands_text.pack(fill=tk.X, pady=(6,6))
        examples = "Examples:\nИдтиМин\nРуда\nСместитьсяВправо\nПуть"
        sample_label = tk.Label(control_frame, text=examples, bg='#e9eef2', fg='#5b6872', justify=tk.LEFT)
        sample_label.pack(anchor=tk.W, pady=(0,8))
        run_btn = tk.Button(control_frame, text="Run Commands", command=self.run_commands, bg='#2E7D32', fg='white', bd=0)
        run_btn.pack(fill=tk.X, pady=(0,8))
        speed_frame = tk.Frame(control_frame, bg='#e9eef2')
        speed_frame.pack(fill=tk.X, pady=(0,8))
        sp_label = tk.Label(speed_frame, text="Speed", bg='#e9eef2', fg='#102332')
        sp_label.pack(side=tk.LEFT)
        self.speed_scale = tk.Scale(speed_frame, from_=0.05, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, bg='#e9eef2', length=200, command=self._on_speed_change)
        self.speed_scale.set(self.delay)
        self.speed_scale.pack(side=tk.RIGHT)
        legend_box = tk.Frame(right_panel, bg='#f7fafb', bd=1, relief=tk.FLAT)
        legend_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6,12))
        lg_title = tk.Label(legend_box, text="Legend", bg='#f7fafb', fg='#102332', font=('Helvetica', 12, 'bold'))
        lg_title.pack(anchor=tk.W, padx=8, pady=(6,4))
        cell_names = {
            CellType.PATH: "Путь (P)",
            CellType.ORE: "Руда (O)",
            CellType.PROCESSED: "Обработано (✓)",
            CellType.SHAFT: "Забой (#)",
            CellType.DANGEROUS: "Опасно (!)",
            CellType.FINISH: "Финиш (F)",
        }
        for ct, name in cell_names.items():
            self._add_legend_item(legend_box, ct, name)
        self._add_legend_item(legend_box, None, "Робот", is_robot=True)
        self.status_var = tk.StringVar()
        self.status_var.set("Load map to start")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bg='#08111a', fg='#e6f0ff', anchor=tk.W, padx=8)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.bind("<Configure>", lambda e: self.draw_maze())

    def _add_legend_item(self, parent, cell_type, text, is_robot=False):
        row = tk.Frame(parent, bg='#f7fafb')
        row.pack(fill=tk.X, padx=8, pady=4)
        c = tk.Canvas(row, width=28, height=22, bg='#f7fafb', highlightthickness=0)
        c.pack(side=tk.LEFT)
        if is_robot:
            c.create_polygon(14,3,5,18,24,18, fill=self.robot_color, outline='black')
        else:
            color = self.cell_colors.get(cell_type, '#c0cbd4')
            c.create_rectangle(4,4,24,18, fill=color, outline='black')
            symbol = self.cell_symbols.get(cell_type, '')
            if symbol:
                c.create_text(14,11, text=symbol, fill='white')
        lbl = tk.Label(row, text=text, bg='#f7fafb', fg='#102332')
        lbl.pack(side=tk.LEFT, padx=8)

    def load_map(self):
        file_path = filedialog.askopenfilename(title="Select map file", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            if not lines:
                messagebox.showerror("Error", "File is empty")
                return
            width = len(lines[0].split())
            height = len(lines)
            for i, line in enumerate(lines[1:], 1):
                if len(line.split()) != width:
                    messagebox.showerror("Error", f"Row {i + 1}: width mismatch")
                    return
            matrix_input: List[List[int]] = []
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
            bottom_first = matrix_input[::-1]
            self.workshop = RobotMaze(width, height)
            self.workshop.load_from_values(bottom_first)
            self.robot = RobotMiner(self.workshop)
            self.save_initial_state()
            self.status_var.set(f"Map loaded: {width}x{height}")
            self.draw_maze()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load map:\n{str(e)}")

    def draw_maze(self):
        if not self.workshop:
            return
        self.canvas.delete("all")
        cw = self.canvas.winfo_width() or 600
        ch = self.canvas.winfo_height() or 400
        cell_size_x = cw // self.workshop.width
        cell_size_y = ch // self.workshop.height
        self.cell_size = min(cell_size_x, cell_size_y, 64)
        pad_x = (cw - self.workshop.width * self.cell_size) // 2
        pad_y = (ch - self.workshop.height * self.cell_size) // 2
        for y in range(self.workshop.height):
            for x in range(self.workshop.width):
                cell = self.workshop.get_cell_by_coordinates(x, y)
                canvas_y = self.workshop.height - 1 - y
                x1 = pad_x + x * self.cell_size
                y1 = pad_y + canvas_y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                if cell.cell_type in self.cell_colors:
                    color = self.cell_colors[cell.cell_type]
                    symbol = self.cell_symbols.get(cell.cell_type, '?')
                else:
                    color = self.cell_colors[CellType.PATH]
                    symbol = self.cell_symbols[CellType.PATH]
                outline = '#FFD54F' if cell.has_robot else '#263238'
                width = 3 if cell.has_robot else 1
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=outline, width=width)
                if self.cell_size > 20:
                    text_color = 'white' if color in ['#455A64', '#E53935', '#0b1a26'] else '#1b2730'
                    self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=symbol, fill=text_color, font=('Helvetica', max(8, self.cell_size // 4)))
                if cell.has_robot:
                    self.draw_robot(x1, y1, x2, y2)
        self.draw_grid(pad_x, pad_y)

    def draw_grid(self, pad_x, pad_y):
        for x in range(self.workshop.width + 1):
            x_pos = pad_x + x * self.cell_size
            self.canvas.create_line(x_pos, pad_y, x_pos, pad_y + self.workshop.height * self.cell_size, fill='#243544', dash=(2,2))
        for y in range(self.workshop.height + 1):
            canvas_y = self.workshop.height - y
            y_pos = pad_y + canvas_y * self.cell_size
            self.canvas.create_line(pad_x, y_pos, pad_x + self.workshop.width * self.cell_size, y_pos, fill='#243544', dash=(2,2))

    def draw_robot(self, x1, y1, x2, y2):
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        size = self.cell_size // 3
        points = [(cx, cy - size), (cx - size, cy + size), (cx + size, cy + size)]
        self.canvas.create_polygon(points, fill=self.robot_color, outline='#2b2b2b', width=2)

    def save_initial_state(self):
        if not self.workshop:
            return
        data = []
        for y in range(self.workshop.height):
            row = []
            for x in range(self.workshop.width):
                cell = self.workshop.get_cell_by_coordinates(x, y)
                row.append({'type': cell.cell_type, 'robot': cell.has_robot})
            data.append(row)
        self.initial_state = (self.workshop.width, self.workshop.height, data)

    def reset_maze(self):
        if not hasattr(self, 'initial_state') or self.initial_state is None:
            self.status_var.set("No saved state")
            return
        width, height, data = self.initial_state
        self.workshop = RobotMaze(width, height)
        self.workshop.initialize_maze(CellType.PATH)
        for y in range(height):
            for x in range(width):
                cell_data = data[y][x]
                cell = self.workshop.get_cell_by_coordinates(x, y)
                cell.cell_type = cell_data['type']
                cell.has_robot = cell_data['robot']
        self.robot = RobotMiner(self.workshop)
        self.draw_maze()
        self.status_var.set("Reset to initial state")

    def run_commands(self):
        if not self.workshop or not self.robot:
            messagebox.showwarning("Warning", "Load map first")
            return
        raw = self.commands_text.get("1.0", "end").strip()
        if not raw:
            messagebox.showwarning("Warning", "No commands")
            return
        commands_text = raw
        mapping_path = os.path.join(os.path.dirname(__file__), "mapping.yaml")
        def _worker():
            try:
                translate_and_exec(
                    commands_text,
                    mapping_path,
                    self.robot,
                    delay=self.delay,
                    on_step=lambda: self.root.after(0, self.draw_maze)
                )
                self.root.after(0, self.check_completion_conditions)
                self.root.after(0, lambda: self.status_var.set("Executed"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Execution error", str(e)))
                self.root.after(0, lambda: self.status_var.set("Error"))
        threading.Thread(target=_worker, daemon=True).start()

    def _on_speed_change(self, value):
        try:
            v = float(value)
            self.delay = v
            self.status_var.set(f"Speed set to {v:.2f}s")
        except:
            pass

    def check_completion_conditions(self):
        if not self.workshop or not self.robot:
            return
        remaining_path = 0
        remaining_ore = 0
        for y in range(self.workshop.height):
            for x in range(self.workshop.width):
                cell = self.workshop.get_cell_by_coordinates(x, y)
                if cell.cell_type == CellType.PATH:
                    remaining_path += 1
                elif cell.cell_type == CellType.ORE:
                    remaining_ore += 1
        at_finish = (self.robot.current_cell is not None and self.robot.current_cell.cell_type == CellType.FINISH)
        success = (remaining_path == 0 and remaining_ore == 0 and at_finish)
        if success:
            self.root.after(0, lambda: messagebox.showinfo("Success", "Program completed successfully!\n\n✓ No PATH or ORE cells left\n✓ Robot is on FINISH"))
            self.root.after(0, lambda: self.status_var.set("Success"))
        else:
            errors = []
            if remaining_path > 0:
                errors.append(f"PATH cells left: {remaining_path}")
            if remaining_ore > 0:
                errors.append(f"ORE cells left: {remaining_ore}")
            if not at_finish:
                errors.append("Robot not on FINISH")
            error_msg = "Conditions not met:\n" + "\n".join(f"• {e}" for e in errors)
            self.root.after(0, lambda: messagebox.showwarning("Incomplete", error_msg))
            self.root.after(0, lambda: self.status_var.set("Incomplete"))

if __name__ == "__main__":
    root = tk.Tk()
    app = MinerGUI(root)
    root.mainloop()
#
# путь
# руда
# сместитьсяВправо
#
# руда
# сместитьсяВправо
#
# руда
# сместитьсяВправо
#
# путь
# руда
#
# сместитьсяВправо


#
# for _ in range(5):
#     путь
#     руда
#     сместитьсяВправо
#
# for _ in range(2):
#     идтимин
#     путь
#     руда
#
# сместитьсяВлево
#
# for _ in range(4):
#      руда
#      идтиМин
#
# сместитьсяВправо