import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import Optional, List, Iterator
import yaml
from enum import Enum
import random


class ТипНаправленийХимНапр(Enum):
    ВперёдX = "ВперёдX"
    НазадX = "НазадX"
    ВлевоX = "ВлевоX"
    ВправоX = "ВправоX"
    ДиагXB = "ДиагXB"
    ДиагXH = "ДиагXH"


class ТипЯчеекХимии(Enum):
    Пусто = "Пусто"
    Реактив = "Реактив"
    Обработано = "Обработано"
    Контейнер = "Контейнер"
    Опасно = "Опасно"
    Барьер = "Барьер"
    Финиш = "Финиш"


class ЯчейкаРоботХимик:
    def __init__(
            self,
            тип_ячейки: Optional[ТипЯчеекХимии] = None,
            ячейка_робота: bool = False,
            x: int = 0,
            y: int = 0,
    ) -> None:
        self.ячейка_робота: bool = ячейка_робота
        self.тип_ячейки: Optional[ТипЯчеекХимии] = тип_ячейки
        self.x: int = x
        self.y: int = y

    def __repr__(self) -> str:
        return f"Ячейка({self.x},{self.y}):{self.тип_ячейки.name if self.тип_ячейки else None}"


class ЛабиринтРоботХимик:
    def __init__(
            self,
            ширина: int = 5,
            длина: int = 5,
    ) -> None:
        self.ширина: int = ширина
        self.длина: int = длина
        self.ячейки: List[List[ЯчейкаРоботХимик]] = []
        self.создать_случайный_лабиринт()

    def ПолучитьСоседнююЯчейку(
            self,
            текущая_ячейка: ЯчейкаРоботХимик,
            направление_поиска: ТипНаправленийХимНапр,
    ) -> Optional[ЯчейкаРоботХимик]:
        if текущая_ячейка is None:
            return None
        if not self.ячейки:
            return None

        x, y = текущая_ячейка.x, текущая_ячейка.y

        if направление_поиска == ТипНаправленийХимНапр.ВперёдX:
            dx, dy = (0, 1)
        elif направление_поиска == ТипНаправленийХимНапр.НазадX:
            dx, dy = (0, -1)
        elif направление_поиска == ТипНаправленийХимНапр.ВлевоX:
            dx, dy = (-1, 0)
        elif направление_поиска == ТипНаправленийХимНапр.ВправоX:
            dx, dy = (1, 0)
        elif направление_поиска == ТипНаправленийХимНапр.ДиагXB:
            dx, dy = (-1, 1)
        elif направление_поиска == ТипНаправленийХимНапр.ДиагXH:
            dx, dy = (1, -1)
        else:
            return None

        nx, ny = x + dx, y + dy

        if not (0 <= nx < self.ширина and 0 <= ny < self.длина):
            return None

        соседняя = self.ячейки[ny][nx]

        if соседняя.тип_ячейки in (ТипЯчеекХимии.Опасно, ТипЯчеекХимии.Барьер):
            return None

        return соседняя

    def ПолучитьИтератор(self) -> Iterator[ЯчейкаРоботХимик]:
        if not self.ячейки:
            return iter(())

        x = 0
        y = 0
        direction = 1

        while True:
            yield self.ячейки[y][x]

            if direction == 1:
                if x < self.ширина - 1:
                    x += 1
                else:
                    if y == self.длина - 1:
                        break
                    y += 1
                    direction = -1
            else:
                if x > 0:
                    x -= 1
                else:
                    if y == self.длина - 1:
                        break
                    y += 1
                    direction = 1

    def создать_случайный_лабиринт(self) -> None:
        self.ширина = 5
        self.длина = 5
        self.ячейки = []

        for y in range(self.длина):
            row = []
            for x in range(self.ширина):
                row.append(ЯчейкаРоботХимик(тип_ячейки=ТипЯчеекХимии.Пусто, x=x, y=y))
            self.ячейки.append(row)

        ячейки_для_реактивов = random.sample(
            [(x, y) for y in range(self.длина) for x in range(self.ширина)
             if not (x == 0 and y == 0)],
            min(3, self.ширина * self.длина - 1)
        )

        for x, y in ячейки_для_реактивов:
            self.ячейки[y][x].тип_ячейки = ТипЯчеекХимии.Реактив

        опасные_ячейки = random.sample(
            [(x, y) for y in range(self.длина) for x in range(self.ширина)
             if not (x == 0 and y == 0) and self.ячейки[y][x].тип_ячейки == ТипЯчеекХимии.Пусто],
            min(3, self.ширина * self.длина - 1 - len(ячейки_для_реактивов))
        )

        for i, (x, y) in enumerate(опасные_ячейки):
            if i % 2 == 0:
                self.ячейки[y][x].тип_ячейки = ТипЯчеекХимии.Опасно
            else:
                self.ячейки[y][x].тип_ячейки = ТипЯчеекХимии.Барьер

        контейнеры = random.sample(
            [(x, y) for y in range(self.длина) for x in range(self.ширина)
             if not (x == 0 and y == 0) and self.ячейки[y][x].тип_ячейки == ТипЯчеекХимии.Пусто],
            min(1, self.ширина * self.длина - 1 - len(ячейки_для_реактивов) - len(опасные_ячейки))
        )

        if контейнеры:
            x, y = контейнеры[0]
            self.ячейки[y][x].тип_ячейки = ТипЯчеекХимии.Контейнер

        возможные_финиши = [(x, y) for y in range(self.длина) for x in range(self.ширина)
                            if not (x == 0 and y == 0) and self.ячейки[y][x].тип_ячейки == ТипЯчеекХимии.Пусто]

        if возможные_финиши:
            x, y = random.choice(возможные_финиши)
            self.ячейки[y][x].тип_ячейки = ТипЯчеекХимии.Финиш

        self.ячейки[0][0].ячейка_робота = True


class РоботХимик:
    def __init__(self, лабиринт: ЛабиринтРоботХимик) -> None:
        self.лабиринт: ЛабиринтРоботХимик = лабиринт
        self.текущая_ячейка: Optional[ЯчейкаРоботХимик] = None
        self.шаги = 0
        self.обработано_реактивов = 0
        self.обработано_пустот = 0

        for row in self.лабиринт.ячейки:
            for cell in row:
                if cell.ячейка_робота:
                    self.текущая_ячейка = cell
                    break
            if self.текущая_ячейка:
                break

        if self.текущая_ячейка is None:
            self.лабиринт.ячейки[0][0].ячейка_робота = True
            self.текущая_ячейка = self.лабиринт.ячейки[0][0]

    def _переместить_робота(self, направление: ТипНаправленийХимНапр) -> Optional[ЯчейкаРоботХимик]:
        if self.текущая_ячейка is None:
            return None

        цель = self.лабиринт.ПолучитьСоседнююЯчейку(self.текущая_ячейка, направление)

        if цель is None:
            return None

        self.текущая_ячейка.ячейка_робота = False
        цель.ячейка_робота = True
        self.текущая_ячейка = цель
        self.шаги += 1

        return цель

    def ДвигВперёд(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ВперёдX)

    def Отодвинуть(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.НазадX)

    def СдвинутьВлево(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ВлевоX)

    def СдвинутьВправо(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ВправоX)

    def Подняться(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ДиагXB)

    def Спуститься(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ДиагXH)

    def Реактив(self) -> None:
        if self.текущая_ячейка is None:
            return
        if self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Реактив:
            self.текущая_ячейка.тип_ячейки = ТипЯчеекХимии.Обработано
            self.обработано_реактивов += 1

    def Пусто(self) -> None:
        if self.текущая_ячейка is None:
            return
        if self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Пусто:
            self.текущая_ячейка.тип_ячейки = ТипЯчеекХимии.Реактив
            self.обработано_пустот += 1

    def обработать_текущую_ячейку(self) -> None:
        if self.текущая_ячейка is None:
            return

        if self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Реактив:
            self.Реактив()
        elif self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Пусто:
            self.Пусто()
            self.Реактив()

    def проверить_цель(self) -> bool:
        if self.текущая_ячейка is None:
            return False

        for row in self.лабиринт.ячейки:
            for cell in row:
                if cell.тип_ячейки in [ТипЯчеекХимии.Реактив, ТипЯчеекХимии.Пусто]:
                    return False

        return self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Финиш


class ChemistryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Робот-Химик")
        self.root.geometry("1200x700")

        self.condition_text = """
УСЛОВИЕ ЗАДАЧИ:

РоботХимик выполняет задачи в контексте 'Химии'.
Координатная система: ось Y направлена вверх (на север), 
ось X направлена вправо (на восток). 
Начало координат — в нижней левой ячейке.

Методы специализации и их действие:
- Реактив: заменяет Реактив → Обработано
- Пусто: заменяет Пусто → Реактив

Цель:
1. После завершения работы не должно остаться ячеек 
   следующих типов: Реактив, Пусто
2. Программа должна завершиться на ячейке типа: Финиш

Ограничения перемещения:
- нельзя заходить на ячейки типа: Опасно
- нельзя заходить на ячейки типа: Барьер

Управление:
- Используйте кнопки для движения и обработки ячеек
- Авто-режим: запускает движение змейкой с обработкой
- Проверка цели: проверяет выполнение условий
"""

        self.initialize_game()

        self.canvas_size = 90
        self.setup_ui()

        self.draw_grid()
        self.log("Система инициализирована. Робот готов к работе.")
        self.update_stats()

    def initialize_game(self):
        self.maze = ЛабиринтРоботХимик(ширина=5, длина=5)
        self.robot = РоботХимик(self.maze)

        self.iterator = iter(())
        self.auto_mode = False

    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, padx=10)

        canvas_width = 5 * self.canvas_size
        canvas_height = 5 * self.canvas_size
        self.canvas = tk.Canvas(left_frame, width=canvas_width, height=canvas_height,
                                bg="#f0f0f0", relief=tk.FLAT)
        self.canvas.pack()

        tk.Label(left_frame, text="Y (Север) ↑", font=("Arial", 10)).pack()
        tk.Label(left_frame, text="X (Восток) →", font=("Arial", 10)).pack()

        center_frame = tk.Frame(main_frame)
        center_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20)

        stats_frame = tk.LabelFrame(center_frame, text="Статистика", padx=10, pady=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.stats_label = tk.Label(stats_frame, text="", font=("Arial", 10))
        self.stats_label.pack()

        control_frame = tk.LabelFrame(center_frame, text="Управление движением", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        btn_style = {"width": 15, "height": 2, "font": ("Arial", 10)}

        diag_frame = tk.Frame(control_frame)
        diag_frame.pack(pady=5)
        tk.Button(diag_frame, text="Подняться", command=self.podnyatsya,
                  bg="#e6f2ff", **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(diag_frame, text="Спуститься", command=self.spustitsya,
                  bg="#e6f2ff", **btn_style).pack(side=tk.LEFT, padx=2)

        dir_frame = tk.Frame(control_frame)
        dir_frame.pack(pady=5)

        tk.Button(dir_frame, text="Вперёд", command=self.dvig_vpered,
                  bg="#d9edf7", **btn_style).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(dir_frame, text="Влево", command=self.sdvinut_vlevo,
                  bg="#d9edf7", **btn_style).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(dir_frame, text="Обработать", command=self.obrabotat,
                  bg="#dff0d8", **btn_style).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(dir_frame, text="Вправо", command=self.sdvinut_vpravo,
                  bg="#d9edf7", **btn_style).grid(row=1, column=2, padx=2, pady=2)
        tk.Button(dir_frame, text="Назад", command=self.otdodvinut,
                  bg="#d9edf7", **btn_style).grid(row=2, column=1, padx=2, pady=2)

        action_frame = tk.LabelFrame(center_frame, text="Действия с веществами", padx=10, pady=10)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(action_frame, text="Реактив → Обработано", command=self.reaktiv,
                  bg="#f2dede", **btn_style).pack(pady=5)
        tk.Button(action_frame, text="Пусто → Реактив", command=self.pusto,
                  bg="#fcf8e3", **btn_style).pack(pady=5)

        auto_frame = tk.LabelFrame(center_frame, text="Автоматический режим", padx=10, pady=10)
        auto_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(auto_frame, text="Запустить змейку", command=self.start_snake,
                  bg="#dff0d8", **btn_style).pack(pady=5)
        tk.Button(auto_frame, text="Остановить", command=self.stop_auto,
                  bg="#f2dede", **btn_style).pack(pady=5)
        tk.Button(auto_frame, text="Проверить цель", command=self.proverit_cel,
                  bg="#d9edf7", **btn_style).pack(pady=5)

        tk.Button(center_frame, text="Начать заново", command=self.nachat_zanovo,
                  bg="#f8d7da", width=20, height=2, font=("Arial", 12)).pack(pady=20)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        condition_frame = tk.LabelFrame(right_frame, text="Условие задачи", padx=10, pady=10)
        condition_frame.pack(fill=tk.BOTH, expand=True)

        self.condition_area = scrolledtext.ScrolledText(condition_frame, width=40, height=15,
                                                        font=("Arial", 9), wrap=tk.WORD)
        self.condition_area.pack(fill=tk.BOTH, expand=True)
        self.condition_area.insert(tk.END, self.condition_text)
        self.condition_area.config(state=tk.DISABLED)

        log_frame = tk.LabelFrame(right_frame, text="Лог действий", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(log_frame, width=40, height=10,
                                                  font=("Courier", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def draw_grid(self):
        self.canvas.delete("all")

        for y in range(self.maze.длина):
            for x in range(self.maze.ширина):
                cell = self.maze.ячейки[y][x]

                canvas_y = (self.maze.длина - 1 - y) * self.canvas_size
                canvas_x = x * self.canvas_size

                color = self.get_cell_color(cell.тип_ячейки)

                self.canvas.create_rectangle(
                    canvas_x, canvas_y,
                    canvas_x + self.canvas_size, canvas_y + self.canvas_size,
                    fill=color, outline="#333333", width=1
                )

                self.canvas.create_rectangle(
                    canvas_x, canvas_y,
                    canvas_x + self.canvas_size, canvas_y + self.canvas_size,
                    outline="#cccccc", width=1
                )

                coord_text = f"{x},{y}"
                self.canvas.create_text(
                    canvas_x + 20, canvas_y + 20,
                    text=coord_text, font=("Arial", 9), fill="#666666"
                )

                if cell.тип_ячейки:
                    type_text = cell.тип_ячейки.value[:3]
                    self.canvas.create_text(
                        canvas_x + self.canvas_size // 2,
                        canvas_y + self.canvas_size // 2,
                        text=type_text, font=("Arial", 11, "bold"), fill="#333333"
                    )

                if cell.ячейка_робота:
                    center_x = canvas_x + self.canvas_size // 2
                    center_y = canvas_y + self.canvas_size // 2
                    radius = self.canvas_size // 3

                    self.canvas.create_oval(
                        center_x - radius, center_y - radius,
                        center_x + radius, center_y + radius,
                        fill="#4a86e8", outline="#1c4587", width=2
                    )

                    self.canvas.create_text(
                        center_x, center_y,
                        text="R", font=("Arial", 14, "bold"), fill="white"
                    )

                    self.canvas.create_line(
                        center_x, center_y + radius // 2,
                        center_x, center_y - radius // 2,
                        arrow=tk.LAST, width=2, fill="white"
                    )

    def get_cell_color(self, cell_type):
        colors = {
            ТипЯчеекХимии.Пусто: "#ffffff",
            ТипЯчеекХимии.Реактив: "#d9ead3",
            ТипЯчеекХимии.Обработано: "#c9daf8",
            ТипЯчеекХимии.Контейнер: "#f3f3f3",
            ТипЯчеекХимии.Опасно: "#f4cccc",
            ТипЯчеекХимии.Барьер: "#999999",
            ТипЯчеекХимии.Финиш: "#fff2cc",
        }
        return colors.get(cell_type, "#ffffff")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def update_stats(self):
        if self.robot.текущая_ячейка:
            stats_text = (
                f"Шагов: {self.robot.шаги}\n"
                f"Обработано реактивов: {self.robot.обработано_реактивов}\n"
                f"Обработано пустот: {self.robot.обработано_пустот}\n"
                f"Текущая позиция: ({self.robot.текущая_ячейка.x},{self.robot.текущая_ячейка.y})\n"
                f"Тип ячейки: {self.robot.текущая_ячейка.тип_ячейки.value}"
            )
            self.stats_label.config(text=stats_text)

    def dvig_vpered(self):
        result = self.robot.ДвигВперёд()
        if result:
            self.log(f"ДвигВперёд → ({result.x},{result.y})")
            self.draw_grid()
            self.update_stats()
        else:
            self.log("ДвигВперёд: движение невозможно!")

    def otdodvinut(self):
        result = self.robot.Отодвинуть()
        if result:
            self.log(f"Отодвинуть → ({result.x},{result.y})")
            self.draw_grid()
            self.update_stats()
        else:
            self.log("Отодвинуть: движение невозможно!")

    def sdvinut_vlevo(self):
        result = self.robot.СдвинутьВлево()
        if result:
            self.log(f"СдвинутьВлево → ({result.x},{result.y})")
            self.draw_grid()
            self.update_stats()
        else:
            self.log("СдвинутьВлево: движение невозможно!")

    def sdvinut_vpravo(self):
        result = self.robot.СдвинутьВправо()
        if result:
            self.log(f"СдвинутьВправо → ({result.x},{result.y})")
            self.draw_grid()
            self.update_stats()
        else:
            self.log("СдвинутьВправо: движение невозможно!")

    def podnyatsya(self):
        result = self.robot.Подняться()
        if result:
            self.log(f"Подняться → ({result.x},{result.y})")
            self.draw_grid()
            self.update_stats()
        else:
            self.log("Подняться: движение невозможно!")

    def spustitsya(self):
        result = self.robot.Спуститься()
        if result:
            self.log(f"Спуститься → ({result.x},{result.y})")
            self.draw_grid()
            self.update_stats()
        else:
            self.log("Спуститься: движение невозможно!")

    def reaktiv(self):
        self.robot.Реактив()
        self.log(f"Реактив → Обработано в ({self.robot.текущая_ячейка.x},{self.robot.текущая_ячейка.y})")
        self.draw_grid()
        self.update_stats()

    def pusto(self):
        self.robot.Пусто()
        self.log(f"Пусто → Реактив в ({self.robot.текущая_ячейка.x},{self.robot.текущая_ячейка.y})")
        self.draw_grid()
        self.update_stats()

    def obrabotat(self):
        old_type = self.robot.текущая_ячейка.тип_ячейки
        self.robot.обработать_текущую_ячейку()
        new_type = self.robot.текущая_ячейка.тип_ячейки

        if old_type != new_type:
            self.log(f"Обработано: {old_type.value} → {new_type.value}")
        else:
            self.log(f"Ячейка не требует обработки: {old_type.value}")

        self.draw_grid()
        self.update_stats()

    def start_snake(self):
        self.iterator = self.maze.ПолучитьИтератор()
        self.auto_mode = True
        self.log("Запущен автоматический режим (змейка)")
        self.auto_step()

    def auto_step(self):
        if not self.auto_mode:
            return

        try:
            next_cell = next(self.iterator)

            if (next_cell.x == self.robot.текущая_ячейка.x and
                    next_cell.y == self.robot.текущая_ячейка.y):
                next_cell = next(self.iterator)

            dx = next_cell.x - self.robot.текущая_ячейка.x
            dy = next_cell.y - self.robot.текущая_ячейка.y

            result = None
            if dx == 1 and dy == 0:
                result = self.robot.СдвинутьВправо()
            elif dx == -1 and dy == 0:
                result = self.robot.СдвинутьВлево()
            elif dx == 0 and dy == 1:
                result = self.robot.ДвигВперёд()
            elif dx == 0 and dy == -1:
                result = self.robot.Отодвинуть()
            elif dx == -1 and dy == 1:
                result = self.robot.Подняться()
            elif dx == 1 and dy == -1:
                result = self.robot.Спуститься()

            if result:
                self.robot.обработать_текущую_ячейку()
                self.log(f"Авто-шаг → ({result.x},{result.y})")
                self.draw_grid()
                self.update_stats()

                self.root.after(500, self.auto_step)
            else:
                self.log("Авто-шаг: движение невозможно!")
                self.auto_mode = False

        except StopIteration:
            self.log("Автоматический режим завершен: пройдены все ячейки")
            self.auto_mode = False

    def stop_auto(self):
        self.auto_mode = False
        self.log("Автоматический режим остановлен")

    def proverit_cel(self):
        if self.robot.проверить_цель():
            messagebox.showinfo("Цель достигнута!",
                                "Поздравляем! Робот успешно выполнил задачу:\n"
                                "1. Все реактивы и пустоты обработаны\n"
                                "2. Робот находится на финише")
            self.log("Цель достигнута!")
        else:
            remaining = []
            for row in self.maze.ячейки:
                for cell in row:
                    if cell.тип_ячейки == ТипЯчеекХимии.Реактив:
                        remaining.append(f"Реактив в ({cell.x},{cell.y})")
                    elif cell.тип_ячейки == ТипЯчеекХимии.Пусто:
                        remaining.append(f"Пусто в ({cell.x},{cell.y})")

            if remaining:
                message = "Цель не достигнута!\nНе обработано:\n" + "\n".join(remaining[:5])
                if len(remaining) > 5:
                    message += f"\n... и ещё {len(remaining) - 5}"
                messagebox.showwarning("Цель не достигнута", message)
            elif self.robot.текущая_ячейка.тип_ячейки != ТипЯчеекХимии.Финиш:
                messagebox.showwarning("Цель не достигнута",
                                       "Робот не на финише!\n"
                                       f"Текущая позиция: ({self.robot.текущая_ячейка.x},{self.robot.текущая_ячейка.y})")
            else:
                messagebox.showinfo("Проверка", "Все условия выполнены, кроме нахождения на финише")

    def nachat_zanovo(self):
        self.stop_auto()
        self.initialize_game()
        self.log("=" * 50)
        self.log("НОВАЯ ИГРА: создан случайный лабиринт 5x5")
        self.log("Робот начинает в позиции (0,0)")
        self.log("=" * 50)
        self.draw_grid()
        self.update_stats()


def create_mapping_yaml():
    mapping = {
        'классы': [
            {
                'Класс диаграммы': 'РоботХимик',
                'свойства': [
                    {'лабиринт': 'лабиринт'}
                ],
                'методы': [
                    {'ДвигВперёд': 'ДвигВперёд'},
                    {'Отодвинуть': 'Отодвинуть'},
                    {'СдвинутьВлево': 'СдвинутьВлево'},
                    {'СдвинутьВправо': 'СдвинутьВправо'},
                    {'Подняться': 'Подняться'},
                    {'Спуститься': 'Спуститься'},
                    {'Реактив': 'Реактив'},
                    {'Пусто': 'Пусто'}
                ]
            },
            {
                'Класс диаграммы': 'ЛабиринтРоботХимик',
                'свойства': [
                    {'ширина': 'ширина'},
                    {'длина': 'длина'},
                    {'ячейки': 'ячейки'}
                ],
                'методы': [
                    {'ПолучитьСоседнююЯчейку': 'ПолучитьСоседнююЯчейку'},
                    {'ПолучитьИтератор': 'ПолучитьИтератор'},
                    {'ИнициализироватьЛабиринт': 'ИнициализироватьЛабиринт'}
                ]
            },
            {
                'Класс диаграммы': 'ЯчейкаРоботХимик',
                'свойства': [
                    {'ячейка_робота': 'ячейка_робота'},
                    {'тип_ячейки': 'тип_ячейки'}
                ],
                'методы': []
            }
        ],
        'перечисления': [
            {
                'ПеречислениеНаДиаграмме': 'ТипНаправленийХимНапр',
                'опции': [
                    {'ВперёдX': 'ВперёдX'},
                    {'НазадX': 'НазадX'},
                    {'ВлевоX': 'ВлевоX'},
                    {'ВправоX': 'ВправоX'},
                    {'ДиагXB': 'ДиагXB'},
                    {'ДиагXH': 'ДиагXH'}
                ]
            },
            {
                'ПеречислениеНаДиаграмме': 'ТипЯчеекХимии',
                'опции': [
                    {'Пусто': 'Пусто'},
                    {'Реактив': 'Реактив'},
                    {'Обработано': 'Обработано'},
                    {'Контейнер': 'Контейнер'},
                    {'Опасно': 'Опасно'},
                    {'Барьер': 'Барьер'},
                    {'Финиш': 'Финиш'}
                ]
            }
        ]
    }

    with open('mapping.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(mapping, f, allow_unicode=True, default_flow_style=False)


def main():
    create_mapping_yaml()

    root = tk.Tk()
    app = ChemistryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
