# desktop.py - Этап 1: Десктопное приложение для РоботОператор

import tkinter as tk
from tkinter import messagebox
from collections import deque
from main import (
    DirectionTypePanelDir,
    CellTypePanel,
    OperatorRobotMaze,
    OperatorRobotCell,
    OperatorRobot
)


class OperatorRobotVisualizer:

    def __init__(self, robot: OperatorRobot, cell_size=60):
        self.robot = robot
        self.cell_size = cell_size

        self.root = tk.Tk()
        self.root.title("Робот Оператор - Панели")

        self.colors = {
            CellTypePanel.FLOOR.value: "white",
            CellTypePanel.PANEL.value: "lightblue",
            CellTypePanel.ACTIVE.value: "green",
            CellTypePanel.SLUICE.value: "gray",
            CellTypePanel.WALL.value: "black",
            CellTypePanel.BLOCK.value: "darkgray",
            CellTypePanel.FINISH.value: "gold"
        }

        canvas_width = robot.maze.width * cell_size
        canvas_height = robot.maze.height * cell_size
        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg="white"
        )
        self.canvas.pack(padx=10, pady=10)

        self.info_label = tk.Label(
            self.root,
            text="Готов к работе",
            font=("Arial", 12)
        )
        self.info_label.pack(pady=5)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        self.start_button = tk.Button(
            button_frame,
            text="Начать работу",
            command=self.start_work
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.step_button = tk.Button(
            button_frame,
            text="Один шаг",
            command=self.make_step
        )
        self.step_button.pack(side=tk.LEFT, padx=5)

        self.robot_marker = None
        self.is_working = False

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for y in range(self.robot.maze.height):
            for x in range(self.robot.maze.width):
                display_y = self.robot.maze.height - 1 - y

                cell = self.robot.maze.get_cell_by_coordinates(x, y)
                if not cell:
                    continue

                color = self.colors.get(cell.cell_type.value, "white")

                x1 = x * self.cell_size
                y1 = display_y * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="gray"
                )

                text = self._get_cell_label(cell.cell_type)
                if text:
                    self.canvas.create_text(
                        (x1 + x2) / 2, (y1 + y2) / 2,
                        text=text,
                        font=("Arial", 10)
                    )

        self.draw_robot()

    def _get_cell_label(self, cell_type: CellTypePanel) -> str:
        labels = {
            CellTypePanel.FLOOR: "П",
            CellTypePanel.PANEL: "Пн",
            CellTypePanel.ACTIVE: "А",
            CellTypePanel.SLUICE: "Ш",
            CellTypePanel.WALL: "■",
            CellTypePanel.BLOCK: "▓",
            CellTypePanel.FINISH: "F"
        }
        return labels.get(cell_type, "")

    def draw_robot(self):
        if self.robot_marker:
            self.canvas.delete(self.robot_marker)

        if not self.robot.current_cell:
            return

        x = self.robot.current_cell.x
        y = self.robot.current_cell.y
        display_y = self.robot.maze.height - 1 - y

        x_center = x * self.cell_size + self.cell_size / 2
        y_center = display_y * self.cell_size + self.cell_size / 2
        radius = self.cell_size / 3

        self.robot_marker = self.canvas.create_oval(
            x_center - radius, y_center - radius,
            x_center + radius, y_center + radius,
            fill="red", outline="darkred", width=2
        )

        self.canvas.create_text(
            x_center, y_center,
            text="R",
            font=("Arial", 14, "bold"),
            fill="white"
        )

    def update_info(self, text: str):
        self.info_label.config(text=text)

    def _is_free(self, x: int, y: int) -> bool:
        if not (0 <= x < self.robot.maze.width and 0 <= y < self.robot.maze.height):
            return False
        cell = self.robot.maze.get_cell_by_coordinates(x, y)
        if not cell:
            return False
        return cell.cell_type not in (CellTypePanel.WALL, CellTypePanel.BLOCK)

    def _find_nearest_target(self):
        targets = []
        for y in range(self.robot.maze.height):
            for x in range(self.robot.maze.width):
                cell = self.robot.maze.get_cell_by_coordinates(x, y)
                if cell and cell.cell_type in (CellTypePanel.FLOOR, CellTypePanel.PANEL):
                    targets.append((x, y))

        if targets:
            return targets

        for y in range(self.robot.maze.height):
            for x in range(self.robot.maze.width):
                cell = self.robot.maze.get_cell_by_coordinates(x, y)
                if cell and cell.cell_type == CellTypePanel.FINISH:
                    return [(x, y)]

        return []

    def _bfs_next_step(self, start, goals):
        goals = set(goals)
        queue = deque([start])
        prev = {start: None}

        while queue:
            x, y = queue.popleft()

            if (x, y) in goals:
                cur = (x, y)
                while prev[cur] is not None and prev[cur] != start:
                    cur = prev[cur]
                return cur if cur != start else None

            neighbors = [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1),
                (x - 1, y + 1),
                (x + 1, y - 1)
            ]

            for nx, ny in neighbors:
                if (nx, ny) not in prev and self._is_free(nx, ny):
                    prev[(nx, ny)] = (x, y)
                    queue.append((nx, ny))

        return None

    def move_robot(self) -> bool:
        x, y = self.robot.current_cell.x, self.robot.current_cell.y
        goals = self._find_nearest_target()

        if not goals:
            self.update_info("Целей нет (все Пол/Панель обработаны)")
            return False

        next_pos = self._bfs_next_step((x, y), goals)

        if next_pos is None:
            self.update_info("Путь к цели не найден")
            return False

        nx, ny = next_pos

        if nx == x + 1 and ny == y:
            return self.robot.channel_right() is not None
        elif nx == x - 1 and ny == y:
            return self.robot.channel_left() is not None
        elif nx == x and ny == y + 1:
            return self.robot.channel_forward() is not None
        elif nx == x and ny == y - 1:
            return self.robot.channel_backward() is not None
        elif nx == x - 1 and ny == y + 1:
            return self.robot.lift_diag() is not None
        elif nx == x + 1 and ny == y - 1:
            return self.robot.descend_diag() is not None

        return False

    def make_step(self):
        if not self.robot.current_cell:
            self.update_info("Робот не найден!")
            return

        current_cell = self.robot.current_cell
        x, y = current_cell.x, current_cell.y

        if current_cell.cell_type == CellTypePanel.FLOOR:
            self.robot.floor()
            self.update_info(f"Позиция ({x}, {y}): Пол → Панель")
        elif current_cell.cell_type == CellTypePanel.PANEL:
            self.robot.panel()
            self.update_info(f"Позиция ({x}, {y}): Панель → Активно")
        elif current_cell.cell_type == CellTypePanel.FINISH:
            self.update_info(f"Позиция ({x}, {y}): ФИНИШ! Работа завершена!")
            self.draw_grid()
            self.is_working = False
            return
        else:
            self.update_info(f"Позиция ({x}, {y}): Ячейка не требует обработки")

        self.move_robot()

        self.draw_grid()
        self.root.update()

    def start_work(self):
        self.is_working = True
        self.start_button.config(state=tk.DISABLED)
        self.automatic_work()

    def automatic_work(self):
        if not self.is_working:
            self.start_button.config(state=tk.NORMAL)
            return

        if not self.robot.current_cell:
            self.update_info("Ошибка: робот не найден!")
            self.is_working = False
            self.start_button.config(state=tk.NORMAL)
            return

        current_cell = self.robot.current_cell

        if current_cell.cell_type == CellTypePanel.FINISH:
            self.update_info("РАБОТА ЗАВЕРШЕНА! Робот достиг финиша!")
            self.is_working = False
            self.start_button.config(state=tk.NORMAL)
            return

        self.make_step()

        self.root.after(100, self.automatic_work)

    def run(self):
        self.root.mainloop()


def create_test_grid(width: int, height: int):
    cell_values = []

    for y in range(height):
        row = []
        for x in range(width):
            if x == 0 and y == 0:
                cell_value = CellTypePanel.FLOOR.value | 0x8
            elif x == width - 1 and y == height - 1:
                cell_value = CellTypePanel.FINISH.value
            elif (x == 2 and y == 1) or (x == 3 and y == 2):
                cell_value = CellTypePanel.WALL.value
            elif x == 1 and y == 2:
                cell_value = CellTypePanel.BLOCK.value
            elif (x + y) % 3 == 0:
                cell_value = CellTypePanel.PANEL.value
            else:
                cell_value = CellTypePanel.FLOOR.value

            row.append(cell_value)
        cell_values.append(row)

    return cell_values


def main():
    width = 7
    height = 5

    cell_values = create_test_grid(width, height)

    maze = OperatorRobotMaze(cells=cell_values)

    robot = OperatorRobot(maze)

    visualizer = OperatorRobotVisualizer(robot)
    visualizer.run()


if __name__ == "__main__":
    main()
