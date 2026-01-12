import tkinter as tk
from tkinter import messagebox
import time

from stage0 import (
    LabyrinthRobot,
    RobotLabAssistant,
    CellType,
)

CELL_COLORS = {
    CellType.EMPTY: "#ffffff",
    CellType.TEST_TUBE: "#ffd966",
    CellType.ANALYZED: "#93c47d",
    CellType.REAGENT: "#9fc5e8",
    CellType.BARRIER: "#333333",
    CellType.TRASH: "#6d6d6d",
    CellType.FINISH: "#76d7c4",
}

CELL_ORDER = [
    CellType.EMPTY,
    CellType.TEST_TUBE,
    CellType.ANALYZED,
    CellType.REAGENT,
    CellType.BARRIER,
    CellType.TRASH,
    CellType.FINISH,
]


class RobotLabUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Робот Лаборант")

        self.width = 7
        self.height = 7

        self.lab = LabyrinthRobot(self.width, self.height)
        self.robot = RobotLabAssistant(self.lab)

        layout = {
            (2, 2): CellType.TEST_TUBE,
            (2, 3): CellType.TEST_TUBE,
            (2, 4): CellType.TEST_TUBE,

            (3, 2): CellType.REAGENT,
            (3, 3): CellType.REAGENT,
            (3, 4): CellType.REAGENT,

            (4, 2): CellType.BARRIER,
            (4, 3): CellType.BARRIER,
            (4, 4): CellType.BARRIER,
            (3, 5): CellType.BARRIER,
            (4, 5): CellType.BARRIER,

            (2, 5): CellType.TRASH,
            (1, 5): CellType.TRASH,

            (6, 6): CellType.FINISH,
        }


        for (x, y), t in layout.items():
            self.lab.cells[y][x].cell_type = t

        start_cell = self.lab.cells[0][0]
        start_cell.is_robot = True
        self.robot.current_cell = start_cell

        self._snapshot = self._take_snapshot()

        self._build_ui()
        self.update_grid()

    def _build_ui(self):
        self.frame_grid = tk.Frame(self.root)
        self.frame_grid.grid(row=0, column=0, padx=10, pady=10)

        self.buttons = [[None for _ in range(self.width)] for _ in range(self.height)]

        for y in range(self.height):
            ui_row = self.height - 1 - y
            for x in range(self.width):
                b = tk.Button(
                    self.frame_grid,
                    width=10,
                    height=4,
                    command=lambda xx=x, yy=y: self.on_cell_click(xx, yy),
                )
                b.grid(row=ui_row, column=x, padx=2, pady=2)
                self.buttons[y][x] = b

        self.frame_right = tk.Frame(self.root)
        self.frame_right.grid(row=0, column=1, sticky="n", padx=10, pady=10)

        tk.Label(
            self.frame_right,
            text="Программа (1 команда = 1 строка):"
        ).pack(anchor="w")

        self.txt_program = tk.Text(self.frame_right, width=36, height=18)
        self.txt_program.pack()

        self.txt_program.insert(
            "1.0",
            "move_to_test_tube\n"
            "move_to_test_tube\n"
            "\n"
            "move_right\n"
            "move_right\n"
            "handle_test_tube\n"
            "\n"
            "move_to_test_tube\n"
            "handle_test_tube\n"
            "\n"
            "move_to_test_tube\n"
            "handle_test_tube\n"
            "\n"
            "move_left\n"
            "move_left\n"
            "\n"
            "move_to_test_tube\n"
            "move_to_test_tube\n"
            "move_right\n"
            "move_right\n"
            "move_right\n"
            "move_right\n"
            "move_right\n"
            "move_right\n"
        )

        self.btn_execute = tk.Button(
            self.frame_right,
            text="Выполнить",
            command=self.on_execute
        )
        self.btn_execute.pack(fill="x", pady=(8, 4))

        self.btn_reset = tk.Button(
            self.frame_right,
            text="Сброс",
            command=self.on_reset
        )
        self.btn_reset.pack(fill="x")

        tk.Label(
            self.frame_right,
            text=(
                "Команды движения:\n"
                "move_to_test_tube  — вверх (север)\n"
                "move_back_from_table — вниз (юг)\n"
                "move_left  — влево (запад)\n"
                "move_right — вправо (восток)\n"
                "move_up    — вверх-влево (северо-запад)\n"
                "move_down  — вниз-вправо (юго-восток)\n\n"
                "Команды действия:\n"
                "handle_test_tube — Пробирка → Проанализировано\n"
                "handle_empty    — Пусто → Пробирка"
            ),
            justify="left"
        ).pack(anchor="w", pady=(8, 0))

    def _take_snapshot(self):
        types = {(c.x, c.y): c.cell_type for c in self.lab.all_cells()}
        cur = self.robot.current_cell
        robot_pos = (cur.x, cur.y)
        return types, robot_pos

    def on_reset(self):
        types, robot_pos = self._snapshot
        for (x, y), t in types.items():
            cell = self.lab.cells[y][x]
            cell.cell_type = t
            cell.is_robot = False

        rx, ry = robot_pos
        self.lab.cells[ry][rx].is_robot = True
        self.robot.current_cell = self.lab.cells[ry][rx]

        self.update_grid()

    def on_cell_click(self, x, y):
        cell = self.lab.cells[y][x]
        idx = CELL_ORDER.index(cell.cell_type)
        cell.cell_type = CELL_ORDER[(idx + 1) % len(CELL_ORDER)]
        self.update_grid()

    def update_grid(self):
        for y in range(self.height):
            for x in range(self.width):
                cell = self.lab.cells[y][x]
                b = self.buttons[y][x]

                text = cell.cell_type.name
                if cell.is_robot:
                    text = "🤖\n" + text

                b.config(text=text, bg=CELL_COLORS[cell.cell_type])

    def on_execute(self):
        program_text = self.txt_program.get("1.0", "end").strip()
        commands = [
            c.strip() for c in program_text.splitlines()
            if c.strip() and not c.startswith("#")
        ]

        self.btn_execute.config(state="disabled")
        self.btn_reset.config(state="disabled")

        try:
            for cmd in commands:
                if not self.execute_command(cmd):
                    messagebox.showerror("Ошибка", f"Команда не выполнена: {cmd}")
                    return

                self.update_grid()
                self.root.update()
                time.sleep(0.15)

            messagebox.showinfo("Готово", "Программа выполнена")

        finally:
            self.btn_execute.config(state="normal")
            self.btn_reset.config(state="normal")

    def execute_command(self, cmd: str):
        r = self.robot

        if cmd == "move_to_test_tube":
            return r.move_to_test_tube()
        elif cmd == "move_back_from_table":
            return r.move_back_from_table()
        elif cmd == "move_left":
            return r.move_left()
        elif cmd == "move_right":
            return r.move_right()
        elif cmd == "move_up":
            return r.move_up()
        elif cmd == "move_down":
            return r.move_down()
        elif cmd == "handle_test_tube":
            r.handle_test_tube()
            return True
        elif cmd == "handle_empty":
            r.handle_empty()
            return True
        else:
            return False


if __name__ == "__main__":
    root = tk.Tk()
    app = RobotLabUI(root)
    root.mainloop()
