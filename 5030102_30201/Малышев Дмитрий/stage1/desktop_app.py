import tkinter as tk
from tkinter import scrolledtext, messagebox
from enum import Enum
from typing import Optional, List
import random
import time


class DirectionType(Enum):
    FORWARD = "Forward"
    BACKWARD = "Backward"
    LEFT = "Left"
    RIGHT = "Right"
    DIAG_UP = "DiagUp"
    DIAG_DOWN = "DiagDown"


class CellType(Enum):
    ROAD = 0x0
    FIRE = 0x1
    FILLED = 0x2
    WATER = 0x3
    BARRIER = 0x4
    FINISH = 0x5
    POST = 0x6

    @classmethod
    def from_value(cls, value: int) -> 'CellType':
        base_value = value & 0x7
        for cell_type in cls:
            if cell_type.value == base_value:
                return cell_type
        return cls.ROAD

    def get_color(self):
        colors = {
            CellType.ROAD: "white",
            CellType.FIRE: "red",
            CellType.FILLED: "orange",
            CellType.WATER: "blue",
            CellType.BARRIER: "black",
            CellType.FINISH: "green",
            CellType.POST: "purple",
        }
        return colors.get(self, "gray")

    def get_symbol(self):
        symbols = {
            CellType.ROAD: "ДОРОГА",
            CellType.FIRE: "ПОЖАР",
            CellType.FILLED: "ЗАЛИТОЕ",
            CellType.WATER: "ВОДА",
            CellType.BARRIER: "БАРЬЕР",
            CellType.FINISH: "ФИНИШ",
            CellType.POST: "ПОСТ",
        }
        return symbols.get(self, "?")


class RobotCell:
    def __init__(self, x: int = 0, y: int = 0, cell_value: int = 0x0):
        self.x = x
        self.y = y
        self.has_robot = (cell_value & 0x8) != 0
        self.cell_type = CellType.from_value(cell_value)

    def get_display_text(self):
        return self.cell_type.get_symbol()

    def get_color(self):
        return self.cell_type.get_color()

    def is_forbidden(self):
        """Проверяет, является ли клетка запрещенной для захода"""
        return self.cell_type in [CellType.BARRIER]


class RobotMaze:
    def __init__(self, width: int = None, height: int = None, cells: List[List[int]] = None):
        self.width = width if width is not None else 0
        self.height = height if height is not None else 0
        self.cells = []

        if cells is not None:
            self.load_from_values(cells)
        elif width is not None and height is not None:
            self.initialize_maze()

    def load_from_values(self, cell_values: List[List[int]]):
        if not cell_values:
            self.height = 0
            self.width = 0
            self.cells = []
            return

        self.height = len(cell_values)
        self.width = len(cell_values[0]) if self.height > 0 else 0

        self.cells = []
        for row_idx in range(self.height - 1, -1, -1):
            y = row_idx
            row = []
            for x in range(self.width):
                cell_value = cell_values[row_idx][x]
                cell = RobotCell(x, y, cell_value)
                row.append(cell)
            self.cells.append(row)

    def initialize_maze(self, cell_type: CellType = None):
        if cell_type is None:
            cell_type = CellType.ROAD

        self.cells = []
        for list_y in range(self.height):
            y = self.height - 1 - list_y
            row = []
            for x in range(self.width):
                cell_value = cell_type.value
                cell = RobotCell(x, y, cell_value)
                row.append(cell)
            self.cells.append(row)

    def get_cell_by_coordinates(self, x: int, y: int) -> Optional[RobotCell]:
        if 0 <= x < self.width and 0 <= y < self.height:
            list_y = self.height - 1 - y
            return self.cells[list_y][x]
        return None

    def get_neighbor_cell(self, current_cell: RobotCell,
                          search_direction: DirectionType) -> Optional[RobotCell]:
        if not self.cells or not current_cell:
            return None

        x, y = current_cell.x, current_cell.y

        offsets = {
            DirectionType.FORWARD.value: (0, 1),
            DirectionType.BACKWARD.value: (0, -1),
            DirectionType.LEFT.value: (-1, 0),
            DirectionType.RIGHT.value: (1, 0),
            DirectionType.DIAG_UP.value: (-1, 1),
            DirectionType.DIAG_DOWN.value: (1, -1),
        }

        dx, dy = offsets.get(search_direction.value, (0, 0))
        return self.get_cell_by_coordinates(x + dx, y + dy)

    def initialize_mission_map(self):
        """Инициализация конкретной карты для миссии 5x5"""
        self.width = 5
        self.height = 5
        self.cells = []

        for list_y in range(self.height):
            y = self.height - 1 - list_y
            row = []
            for x in range(self.width):
                cell = RobotCell(x, y, CellType.ROAD.value)
                row.append(cell)
            self.cells.append(row)

        # Устанавливаем специальные клетки
        self.get_cell_by_coordinates(4, 4).cell_type = CellType.FINISH  # Финиш
        self.get_cell_by_coordinates(3, 4).cell_type = CellType.BARRIER  # Барьер
        self.get_cell_by_coordinates(2, 4).cell_type = CellType.POST  # Пост
        self.get_cell_by_coordinates(1, 4).cell_type = CellType.FIRE  # Пожар

        self.get_cell_by_coordinates(3, 3).cell_type = CellType.FIRE  # Пожар
        self.get_cell_by_coordinates(1, 3).cell_type = CellType.FILLED  # Залитое

        self.get_cell_by_coordinates(3, 2).cell_type = CellType.POST  # Пост
        self.get_cell_by_coordinates(1, 2).cell_type = CellType.FIRE  # Пожар
        self.get_cell_by_coordinates(0, 2).cell_type = CellType.BARRIER  # Барьер

        self.get_cell_by_coordinates(2, 1).cell_type = CellType.FILLED  # Залитое

        self.get_cell_by_coordinates(4, 0).cell_type = CellType.POST  # Пост
        self.get_cell_by_coordinates(3, 0).cell_type = CellType.BARRIER  # Барьер

        # Начальная позиция робота в (0, 0)
        start_cell = self.get_cell_by_coordinates(0, 0)
        start_cell.has_robot = True

    def create_random_maze_5x5(self):
        """Создает случайный лабиринт 5x5 с гарантией, что робот начинает на разрешенной клетке"""
        self.width = 5
        self.height = 5
        self.cells = []

        # Создаем все клетки
        for list_y in range(self.height):
            y = self.height - 1 - list_y
            row = []
            for x in range(self.width):
                cell = RobotCell(x, y, CellType.ROAD.value)
                row.append(cell)
            self.cells.append(row)

        start_cell = self.get_cell_by_coordinates(0, 0)
        start_cell.cell_type = CellType.ROAD

        all_positions = [(x, y) for x in range(5) for y in range(5) if not (x == 0 and y == 0)]
        random.shuffle(all_positions)

        # Распределяем типы клеток
        cell_types = [
            CellType.FIRE, CellType.FIRE, CellType.FIRE,  # 3 пожара
            CellType.FILLED, CellType.FILLED,  # 2 залитых
            CellType.BARRIER, CellType.BARRIER,  # 2 барьера
            CellType.POST, CellType.POST,  # 2 поста
            CellType.FINISH,  # 1 финиш
        ]

        for i, (x, y) in enumerate(all_positions):
            if i < len(cell_types):
                self.get_cell_by_coordinates(x, y).cell_type = cell_types[i]

        start_cell.has_robot = True


class RobotFireman:
    def __init__(self, labyrinth: RobotMaze):
        self.labyrinth = labyrinth
        self.action_history: List[str] = []
        self.mission_completed = False
        self.notification_shown = False

        self.current_cell: Optional[RobotCell] = None
        for y in range(labyrinth.height):
            for x in range(labyrinth.width):
                cell = labyrinth.get_cell_by_coordinates(x, y)
                if cell and cell.has_robot:
                    self.current_cell = cell
                    self.current_x = x
                    self.current_y = y
                    break
            if self.current_cell:
                break

        if not self.current_cell:
            self.current_cell = labyrinth.get_cell_by_coordinates(0, 0)
            if self.current_cell:
                self.current_cell.has_robot = True
                self.current_x = 0
                self.current_y = 0

        self._log_action(f"Начало миссии в ({self.current_x},{self.current_y}).")

    def _log_action(self, action: str):
        """Вспомогательный метод для записи действия с временной меткой."""
        timestamp = time.strftime("%H:%M:%S")
        self.action_history.append(f"[{timestamp}] {action}")

    def _move_robot(self, target: RobotCell) -> bool:
        """Внутренный метод для перемещения робота в указанную клетку."""
        if not self.current_cell or not target:
            self._log_action("Ошибка: нет текущей клетки или целевой клетки!")
            return False

        # Проверяем, не запрещенная ли клетка
        if target.is_forbidden():
            self._log_action(f"Невозможно переместиться на ЗАПРЕЩЕННУЮ клетку ({target.x},{target.y})!")
            return False

        # Проверяем, что клетка соседняя (не телепортация)
        dx = abs(target.x - self.current_x)
        dy = abs(target.y - self.current_y)

        if dx > 1 or dy > 1:
            self._log_action(
                f"Попытка телепортации с ({self.current_x},{self.current_y}) на ({target.x},{target.y})! Отменено.")
            return False

        # Перемещаем робота
        self.current_cell.has_robot = False
        target.has_robot = True
        self.current_cell = target
        self.current_x = target.x
        self.current_y = target.y

        cell_type_names = {
            CellType.ROAD: "Дорога",
            CellType.FIRE: "Пожар",
            CellType.FILLED: "Залитое",
            CellType.WATER: "Вода",
            CellType.BARRIER: "Барьер",
            CellType.FINISH: "Финиш",
            CellType.POST: "Пост",
        }

        cell_name = cell_type_names.get(target.cell_type, "Неизвестно")
        self._log_action(f"Перемещение: ({target.x},{target.y}). Тип: {cell_name}")

        return True

    def attack(self) -> bool:
        """Штурмовать - движение вперед (север, Y+1)"""
        if self.labyrinth and self.current_cell:
            new_cell = self.labyrinth.get_neighbor_cell(
                self.current_cell, DirectionType.FORWARD
            )
            if new_cell:
                if new_cell.is_forbidden():
                    self._log_action(f"Невозможно двигаться вперед - клетка ({new_cell.x},{new_cell.y}) запрещена!")
                    return False
                return self._move_robot(new_cell)
            else:
                self._log_action("Не могу двигаться вперед - клетка за границей!")
        return False

    def retreat(self) -> bool:
        """Отойти - движение назад (юг, Y-1)"""
        if self.labyrinth and self.current_cell:
            new_cell = self.labyrinth.get_neighbor_cell(
                self.current_cell, DirectionType.BACKWARD
            )
            if new_cell:
                if new_cell.is_forbidden():
                    self._log_action(f"Невозможно двигаться назад - клетка ({new_cell.x},{new_cell.y}) запрещена!")
                    return False
                return self._move_robot(new_cell)
            else:
                self._log_action("Не могу двигаться назад - клетка за границей!")
        return False

    def move_left(self) -> bool:
        """СдвинутьЛево - движение влево (запад, X-1)"""
        if self.labyrinth and self.current_cell:
            new_cell = self.labyrinth.get_neighbor_cell(
                self.current_cell, DirectionType.LEFT
            )
            if new_cell:
                if new_cell.is_forbidden():
                    self._log_action(f"Невозможно двигаться влево - клетка ({new_cell.x},{new_cell.y}) запрещена!")
                    return False
                return self._move_robot(new_cell)
            else:
                self._log_action("Не могу двигаться влево - клетка за границей!")
        return False

    def move_right(self) -> bool:
        """СдвинутьПраво - движение вправо (восток, X+1)"""
        if self.labyrinth and self.current_cell:
            new_cell = self.labyrinth.get_neighbor_cell(
                self.current_cell, DirectionType.RIGHT
            )
            if new_cell:
                if new_cell.is_forbidden():
                    self._log_action(f"Невозможно двигаться вправо - клетка ({new_cell.x},{new_cell.y}) запрещена!")
                    return False
                return self._move_robot(new_cell)
            else:
                self._log_action("Не могу двигаться вправо - клетка за границей!")
        return False

    def process_fire(self) -> bool:
        """Обработка Пожар -> Залитое"""
        if self.current_cell and self.current_cell.cell_type == CellType.FIRE:
            self.current_cell.cell_type = CellType.FILLED
            self._log_action(f"В клетке ({self.current_x},{self.current_y}): Найден ПОЖАР. Обработка в ЗАЛИТОЕ.")
            return True
        elif self.current_cell and self.current_cell.cell_type != CellType.FIRE:
            self._log_action(f"В клетке ({self.current_x},{self.current_y}): Нет пожара для обработки.")
        return False

    def process_filled(self) -> bool:
        """Обработка Залитое -> Пост"""
        if self.current_cell and self.current_cell.cell_type == CellType.FILLED:
            self.current_cell.cell_type = CellType.POST
            self._log_action(f"В клетке ({self.current_x},{self.current_y}): Найдено ЗАЛИТОЕ. Обработка в ПОСТ.")
            return True
        elif self.current_cell and self.current_cell.cell_type != CellType.FILLED:
            self._log_action(f"В клетке ({self.current_x},{self.current_y}): Нет залитого для обработки.")
        return False

    def is_mission_complete(self) -> bool:
        """Проверка завершения миссии: Финиш достигнут И нет необработанных клеток."""
        if self.mission_completed:
            return True

        if not (self.current_cell and self.current_cell.cell_type == CellType.FINISH):
            return False

        for y in range(self.labyrinth.height):
            for x in range(self.labyrinth.width):
                cell = self.labyrinth.get_cell_by_coordinates(x, y)
                if cell and cell.cell_type in (CellType.FIRE, CellType.FILLED):
                    return False

        self.mission_completed = True
        return True


class RobotApp:
    def __init__(self, master):
        self.master = master
        master.title("Робот-Пожарный Лабиринт 5x5")

        self.W, self.H = 5, 5
        self.CELL_SIZE = 80
        self.ROBOT_COLOR = "#0000FF"

        self.labyrinth = RobotMaze(self.W, self.H)
        self.labyrinth.initialize_mission_map()
        self.robot = RobotFireman(self.labyrinth)
        self.robot_oval = None

        main_frame = tk.Frame(master)
        main_frame.pack(padx=10, pady=10)

        # 1. Фрейм карты
        map_frame = tk.LabelFrame(main_frame, text="Карта 5x5", padx=5, pady=5)
        map_frame.pack(side=tk.LEFT, padx=10)

        canvas_width = self.W * self.CELL_SIZE + 50
        canvas_height = self.H * self.CELL_SIZE + 50
        self.canvas = tk.Canvas(map_frame, width=canvas_width, height=canvas_height, bg="lightgrey")
        self.canvas.pack()

        self.draw_map_elements()

        # 2. Фрейм управления и истории
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.RIGHT, padx=10, fill=tk.Y)

        # Кнопки управления
        button_frame = tk.LabelFrame(control_frame, text="Управление", padx=10, pady=10)
        button_frame.pack(pady=10, fill=tk.X)

        tk.Button(button_frame, text="Проверить цель", command=self.check_goal,
                  width=25).pack(pady=5)

        manual_frame = tk.LabelFrame(control_frame, text="Ручное управление", padx=10, pady=10)
        manual_frame.pack(pady=10, fill=tk.X)

        tk.Button(manual_frame, text="↑", command=self.move_forward,
                  width=15).grid(row=0, column=1, pady=2, padx=5)
        tk.Button(manual_frame, text="←", command=self.move_left,
                  width=15).grid(row=1, column=0, pady=2, padx=5)
        tk.Button(manual_frame, text="→", command=self.move_right,
                  width=15).grid(row=1, column=2, pady=2, padx=5)
        tk.Button(manual_frame, text="↓", command=self.move_backward,
                  width=15).grid(row=2, column=1, pady=2, padx=5)

        # Кнопки обработки
        action_frame = tk.LabelFrame(control_frame, text="Действия", padx=10, pady=10)
        action_frame.pack(pady=10, fill=tk.X)

        tk.Button(action_frame, text="Потушить пожар", command=self.process_fire,
                  width=20).pack(pady=5)
        tk.Button(action_frame, text="Поставить пост", command=self.process_filled,
                  width=20).pack(pady=5)

        # Кнопки управления лабиринтом
        maze_control_frame = tk.LabelFrame(control_frame, text="Управление лабиринтом", padx=10, pady=10)
        maze_control_frame.pack(pady=10, fill=tk.X)

        tk.Button(maze_control_frame, text="Сброс", command=self.reset_app,
                  width=25).pack(pady=5)
        tk.Button(maze_control_frame, text="Новый лабиринт", command=self.new_maze,
                  width=25).pack(pady=5)

        # История действий
        history_frame = tk.LabelFrame(control_frame, text="История Действий", padx=5, pady=5)
        history_frame.pack(expand=True, fill=tk.BOTH)

        self.history_text = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD, height=18, width=35,
                                                      state='disabled', font=('Courier', 9))
        self.history_text.pack(expand=True, fill=tk.BOTH)

        self.update_display()

    def get_canvas_coords(self, x: int, y: int):
        """Преобразует координаты (x, y) лабиринта в координаты пикселей Canvas."""
        canvas_y = self.H - 1 - y

        x1 = x * self.CELL_SIZE + 25
        y1 = canvas_y * self.CELL_SIZE + 25
        x2 = x1 + self.CELL_SIZE
        y2 = y1 + self.CELL_SIZE
        return x1, y1, x2, y2

    def draw_map_elements(self):
        """Отрисовывает статические элементы карты (сетку, подписи, текст клеток)."""
        self.canvas.delete("all")

        for y in range(self.H):
            for x in range(self.W):
                x1, y1, x2, y2 = self.get_canvas_coords(x, y)
                cell = self.labyrinth.get_cell_by_coordinates(x, y)

                if cell:
                    self.canvas.create_rectangle(x1, y1, x2, y2,
                                                 fill=cell.get_color(),
                                                 outline="black", width=1)

                    text_color = 'white' if cell.get_color() in ["black", "#0000FF"] else 'black'
                    self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2,
                                            text=cell.get_display_text(),
                                            font=("Arial", 8, "bold"),
                                            fill=text_color)

        for x in range(self.W):
            self.canvas.create_text(x * self.CELL_SIZE + 25 + self.CELL_SIZE / 2, 10,
                                    text=f"X={x}", fill='black')
        for y in range(self.H):
            self.canvas.create_text(15, (self.H - 1 - y) * self.CELL_SIZE + 25 + self.CELL_SIZE / 2,
                                    text=f"Y={y}", fill='black')

    def update_display(self):
        """Обновляет карту и историю действий."""
        self.draw_map_elements()

        x_robot, y_robot = self.robot.current_x, self.robot.current_y

        if x_robot is not None and y_robot is not None:
            x1, y1, x2, y2 = self.get_canvas_coords(x_robot, y_robot)
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            radius = 15

            self.robot_oval = self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                fill=self.ROBOT_COLOR, outline="black", width=2
            )

            self.canvas.create_text(center_x, center_y,
                                    text="R",
                                    font=("Arial", 10, "bold"),
                                    fill="white")

        self.history_text.config(state='normal')
        self.history_text.delete('1.0', tk.END)
        for action in self.robot.action_history:
            self.history_text.insert(tk.END, action + '\n')
        self.history_text.see(tk.END)
        self.history_text.config(state='disabled')

        if self.robot.is_mission_complete() and not self.robot.notification_shown:
            self.robot.notification_shown = True
            messagebox.showinfo("Миссия завершена", "Робот завершил обход и обработал все пожары!")

    def move_forward(self):
        if not self.robot.is_mission_complete():
            self.robot.attack()
            self.update_display()
        else:
            messagebox.showinfo("Миссия завершена", "Миссия уже выполнена!")

    def move_backward(self):
        if not self.robot.is_mission_complete():
            self.robot.retreat()
            self.update_display()
        else:
            messagebox.showinfo("Миссия завершена", "Миссия уже выполнена!")

    def move_left(self):
        if not self.robot.is_mission_complete():
            self.robot.move_left()
            self.update_display()
        else:
            messagebox.showinfo("Миссия завершена", "Миссия уже выполнена!")

    def move_right(self):
        if not self.robot.is_mission_complete():
            self.robot.move_right()
            self.update_display()
        else:
            messagebox.showinfo("Миссия завершена", "Миссия уже выполнена!")

    def process_fire(self):
        if not self.robot.is_mission_complete():
            self.robot.process_fire()
            self.update_display()
        else:
            messagebox.showinfo("Миссия завершена", "Миссия уже выполнена!")

    def process_filled(self):
        if not self.robot.is_mission_complete():
            self.robot.process_filled()
            self.update_display()
        else:
            messagebox.showinfo("Миссия завершена", "Миссия уже выполнена!")

    def reset_app(self):
        """Сброс состояния приложения."""
        self.labyrinth = RobotMaze(self.W, self.H)
        self.labyrinth.initialize_mission_map()
        self.robot = RobotFireman(self.labyrinth)

        self.update_display()

        self.robot.action_history = []
        self.robot._log_action("Симулятор сброшен. Миссия началась снова.")
        self.update_display()

    def new_maze(self):
        """Создает новый случайный лабиринт 5x5"""
        self.labyrinth = RobotMaze(self.W, self.H)
        self.labyrinth.create_random_maze_5x5()
        self.robot = RobotFireman(self.labyrinth)

        self.update_display()
        self.robot._log_action("Новый случайный лабиринт 5x5 создан.")

    def check_goal(self):
        """Проверяет, достигнута ли цель"""
        if self.robot.is_mission_complete():
            if not self.robot.notification_shown:
                self.robot.notification_shown = True
                messagebox.showinfo("Цель достигнута!",
                                    "Все пожары потушены и робот на финише!")
            else:
                messagebox.showinfo("Миссия завершена", "Миссия уже выполнена!")
        else:
            messagebox.showinfo("Цель не достигнута",
                                "Цель еще не достигнута.\nУбедитесь, что:\n"
                                "1. Нет ячеек 'Пожар' и 'Залитое'\n"
                                "2. Робот находится на ячейке 'Финиш'")


def main():
    # Запуск UI
    root = tk.Tk()
    app = RobotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()