from __future__ import annotations

from collections import deque
from enum import Enum
from typing import List, Optional, Tuple, Dict

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QBrush, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)


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


class ЯчейкаРоботИнженер:
    def __init__(self, тип_ячейки: ТипЯчеекПроект = ТипЯчеекПроект.Пол, ячейка_робота: bool = False):
        self.тип_ячейки = тип_ячейки
        self.ячейка_робота = ячейка_робота
        self.x = 0
        self.y = 0


class ЛабиринтРоботИнженер:
    def __init__(self):
        self.ширина = 0
        self.длина = 0
        self.ячейки: List[List[ЯчейкаРоботИнженер]] = []

    def ИнициализироватьЛабиринт(self, тип_ячейки: ТипЯчеекПроект, ширина: int = 10, длина: int = 8):
        self.ширина = ширина
        self.длина = длина
        self.ячейки = [[ЯчейкаРоботИнженер(тип_ячейки) for _ in range(ширина)] for _ in range(длина)]
        for y in range(длина):
            for x in range(ширина):
                self.ячейки[y][x].x = x
                self.ячейки[y][x].y = y

    def ПолучитьСоседнююЯчейку(self, текущая: ЯчейкаРоботИнженер, направление: ТипНаправленийИнжНапр) -> Optional[ЯчейкаРоботИнженер]:
        offsets = {
            ТипНаправленийИнжНапр.ИнжВперёд: (0, 1),
            ТипНаправленийИнжНапр.ИнжНазад: (0, -1),
            ТипНаправленийИнжНапр.ИнжЛево: (-1, 0),
            ТипНаправленийИнжНапр.ИнжПраво: (1, 0),
            ТипНаправленийИнжНапр.ДиагИнжВ: (-1, 1),
            ТипНаправленийИнжНапр.ДиагИнжН: (1, 1),
        }
        dx, dy = offsets[направление]
        nx, ny = текущая.x + dx, текущая.y + dy
        if 0 <= nx < self.ширина and 0 <= ny < self.длина:
            cell = self.ячейки[ny][nx]
            if cell.тип_ячейки not in (ТипЯчеекПроект.Инструмент, ТипЯчеекПроект.Препятствие):
                return cell
        return None


class РоботИнженер:
    def __init__(self, лабиринт: ЛабиринтРоботИнженер):
        self.лабиринт = лабиринт
        self.текущая_ячейка: Optional[ЯчейкаРоботИнженер] = None
        for row in лабиринт.ячейки:
            for cell in row:
                if cell.ячейка_робота:
                    self.текущая_ячейка = cell
                    return

    def _переместиться(self, новая: Optional[ЯчейкаРоботИнженер]) -> bool:
        if not новая:
            return False
        if self.текущая_ячейка:
            self.текущая_ячейка.ячейка_робота = False
        self.текущая_ячейка = новая
        новая.ячейка_робота = True
        return True

    def Перейти(self, направление: ТипНаправленийИнжНапр):
        сосед = self.лабиринт.ПолучитьСоседнююЯчейку(self.текущая_ячейка, направление)
        return self._переместиться(сосед)

    def ДвигИнжВперёд(self): return self.Перейти(ТипНаправленийИнжНапр.ИнжВперёд)
    def ДвигИнжНазад(self): return self.Перейти(ТипНаправленийИнжНапр.ИнжНазад)
    def ДвигИнжЛево(self): return self.Перейти(ТипНаправленийИнжНапр.ИнжЛево)
    def ДвигИнжПраво(self): return self.Перейти(ТипНаправленийИнжНапр.ИнжПраво)
    def ДиагИнжВ(self): return self.Перейти(ТипНаправленийИнжНапр.ДиагИнжВ)
    def ДиагИнжН(self): return self.Перейти(ТипНаправленийИнжНапр.ДиагИнжН)

    def Пол(self):
        if self.текущая_ячейка and self.текущая_ячейка.тип_ячейки == ТипЯчеекПроект.Пол:
            self.текущая_ячейка.тип_ячейки = ТипЯчеекПроект.Модуль

    def Модуль(self):
        if self.текущая_ячейка and self.текущая_ячейка.тип_ячейки == ТипЯчеекПроект.Модуль:
            self.текущая_ячейка.тип_ячейки = ТипЯчеекПроект.Контур


class MissionRuntime:
    def __init__(self, maze: ЛабиринтРоботИнженер, robot: РоботИнженер):
        self.maze = maze
        self.robot = robot
        self.path: List[str] = []
        self.target = None
        self.finish = next((c for row in maze.ячейки for c in row if c.тип_ячейки == ТипЯчеекПроект.Финиш), None)
        self.done = False

    def _find_path(self, start: ЯчейкаРоботИнженер, goal: ЯчейкаРоботИнженер) -> List[str]:
        if start == goal:
            return []
        queue = deque([start])
        came_from: Dict[ЯчейкаРоботИнженер, Tuple[ЯчейкаРоботИнженер, str]] = {start: (start, "")}
        while queue:
            curr = queue.popleft()
            if curr == goal:
                path = []
                while came_from[curr][1]:
                    path.append(came_from[curr][1])
                    curr = came_from[curr][0]
                path.reverse()
                return path
            for d in ТипНаправленийИнжНапр:
                neigh = self.maze.ПолучитьСоседнююЯчейку(curr, d)
                if neigh and neigh not in came_from:
                    came_from[neigh] = (curr, d.value)
                    queue.append(neigh)
        return []

    def step(self):
        if self.done or not self.robot.текущая_ячейка:
            return

        # Обработка текущей клетки
        self.robot.Пол()
        self.robot.Модуль()

        # Есть ли цели?
        targets = [c for row in self.maze.ячейки for c in row if c.тип_ячейки in (ТипЯчеекПроект.Пол, ТипЯчеекПроект.Модуль)]
        if targets:
            if not self.path or self.target not in targets:
                best = min(targets, key=lambda t: len(self._find_path(self.robot.текущая_ячейка, t)) if self._find_path(self.robot.текущая_ячейка, t) else float('inf'), default=None)
                if best:
                    self.target = best
                    self.path = self._find_path(self.robot.текущая_ячейка, best)
            if self.path:
                move = self.path.pop(0)
                mapping = {
                    ТипНаправленийИнжНапр.ИнжВперёд.value: self.robot.ДвигИнжВперёд,
                    ТипНаправленийИнжНапр.ИнжНазад.value: self.robot.ДвигИнжНазад,
                    ТипНаправленийИнжНапр.ИнжЛево.value: self.robot.ДвигИнжЛево,
                    ТипНаправленийИнжНапр.ИнжПраво.value: self.robot.ДвигИнжПраво,
                    ТипНаправленийИнжНапр.ДиагИнжВ.value: self.robot.ДиагИнжВ,
                    ТипНаправленийИнжНапр.ДиагИнжН.value: self.robot.ДиагИнжН,
                }
                mapping[move]()
        else:
            # Идём на финиш
            if self.finish and self.robot.текущая_ячейка != self.finish:
                if not self.path:
                    self.path = self._find_path(self.robot.текущая_ячейка, self.finish)
                if self.path:
                    move = self.path.pop(0)
                    mapping = {
                        ТипНаправленийИнжНапр.ИнжВперёд.value: self.robot.ДвигИнжВперёд,
                        ТипНаправленийИнжНапр.ИнжНазад.value: self.robot.ДвигИнжНазад,
                        ТипНаправленийИнжНапр.ИнжЛево.value: self.robot.ДвигИнжЛево,
                        ТипНаправленийИнжНапр.ИнжПраво.value: self.robot.ДвигИнжПраво,
                        ТипНаправленийИнжНапр.ДиагИнжВ.value: self.robot.ДиагИнжВ,
                        ТипНаправленийИнжНапр.ДиагИнжН.value: self.robot.ДиагИнжН,
                    }
                    mapping[move]()
            else:
                self.done = True


class MazeEditor:
    def __init__(self, maze: ЛабиринтРоботИнженер):
        self.maze = maze

    def place_robot(self, x: int, y: int):
        for row in self.maze.ячейки:
            for c in row:
                c.ячейка_робота = False
        if 0 <= y < self.maze.длина and 0 <= x < self.maze.ширина:
            c = self.maze.ячейки[y][x]
            if c.тип_ячейки not in (ТипЯчеекПроект.Инструмент, ТипЯчеекПроект.Препятствие):
                c.ячейка_робота = True

    def set_cell_type(self, x: int, y: int, t: ТипЯчеекПроект):
        if 0 <= y < self.maze.длина and 0 <= x < self.maze.ширина:
            self.maze.ячейки[y][x].тип_ячейки = t

    def cycle_cell_type(self, x: int, y: int):
        order = [ТипЯчеекПроект.Пол, ТипЯчеекПроект.Модуль, ТипЯчеекПроект.Инструмент,
                 ТипЯчеекПроект.Препятствие, ТипЯчеекПроект.Финиш, ТипЯчеекПроект.Контур]
        if 0 <= y < self.maze.длина and 0 <= x < self.maze.ширина:
            c = self.maze.ячейки[y][x]
            idx = (order.index(c.тип_ячейки) + 1) % len(order)
            self.set_cell_type(x, y, order[idx])


class MazeView(QGraphicsView):
    def __init__(self, parent: "MainWindow"):
        super().__init__()
        self.parent = parent

    def mousePressEvent(self, event):
        if self.parent.running:
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        x, y = self.parent.scene_to_world(scene_pos.x(), scene_pos.y())
        if x is None or y is None:
            return
        if event.button() == Qt.LeftButton:
            self.parent.editor.cycle_cell_type(x, y)
        elif event.button() == Qt.RightButton:
            self.parent.editor.place_robot(x, y)
        self.parent.redraw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("РоботИнженер")

        self.cell_size = 44
        self.margin = 12

        self.maze = ЛабиринтРоботИнженер()
        self.maze.ИнициализироватьЛабиринт(ТипЯчеекПроект.Пол, 10, 8)
        self.editor = MazeEditor(self.maze)
        self.editor.set_cell_type(9, 7, ТипЯчеекПроект.Финиш)
        self.editor.place_robot(0, 0)

        self.robot = None
        self.runtime = None
        self.running = False
        self.steps = 0

        self.scene = QGraphicsScene()
        self.view = MazeView(self)
        self.view.setScene(self.scene)

        self.status = QLabel("ЛКМ: тип клетки | ПКМ: робот")
        layout = QVBoxLayout()
        layout.addWidget(self.view)

        controls = QHBoxLayout()
        for text, slot in [("Run", self.on_run), ("Step", self.on_step), ("Reset", self.on_reset), ("Demo", self.on_demo)]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            controls.addWidget(btn)

        layout.addLayout(controls)
        layout.addWidget(self.status)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

        self.redraw()

    def view_width(self) -> int:
        return self.margin * 2 + self.maze.ширина * self.cell_size

    def view_height(self) -> int:
        return self.margin * 2 + self.maze.длина * self.cell_size

    def world_to_scene(self, x: int, y: int) -> Tuple[float, float]:
        sx = self.margin + x * self.cell_size
        sy = self.margin + (self.maze.длина - 1 - y) * self.cell_size
        return sx, sy

    def scene_to_world(self, sx: float, sy: float) -> Tuple[Optional[int], Optional[int]]:
        grid_x = sx - self.margin
        grid_y = sy - self.margin
        if grid_x < 0 or grid_y < 0:
            return None, None
        cell_x = int(grid_x // self.cell_size)
        cell_y = int(grid_y // self.cell_size)
        if cell_x >= self.maze.ширина or cell_y >= self.maze.длина:
            return None, None
        world_y = self.maze.длина - 1 - cell_y
        return cell_x, world_y

    def redraw(self):
        self.scene.clear()
        self.scene.setSceneRect(0, 0, self.view_width(), self.view_height())

        for y in range(self.maze.длина - 1, -1, -1):
            for x in range(self.maze.ширина):
                c = self.maze.ячейки[y][x]
                sx, sy = self.world_to_scene(x, y)
                rect = QGraphicsRectItem(sx, sy, self.cell_size, self.cell_size)
                rect.setPen(QPen(Qt.black))
                rect.setBrush(QBrush(self.get_color(c.тип_ячейки)))
                self.scene.addItem(rect)

                label = self.get_label(c.тип_ячейки)
                if label:
                    text = QGraphicsTextItem(label)
                    text.setDefaultTextColor(Qt.black)
                    text.setFont(QFont("Arial", 12, QFont.Bold))
                    text.setPos(sx + 14, sy + 10)
                    self.scene.addItem(text)

                if c.ячейка_робота:
                    r = self.cell_size * 0.28
                    circle = QGraphicsEllipseItem(sx + self.cell_size / 2 - r, sy + self.cell_size / 2 - r, 2 * r, 2 * r)
                    circle.setBrush(QBrush(Qt.black))
                    self.scene.addItem(circle)

        self.update_status()

    def get_color(self, t: ТипЯчеекПроект):
        colors = {
            ТипЯчеекПроект.Пол: Qt.white,
            ТипЯчеекПроект.Модуль: Qt.yellow,
            ТипЯчеекПроект.Инструмент: Qt.cyan,
            ТипЯчеекПроект.Препятствие: Qt.darkGray,
            ТипЯчеекПроект.Финиш: Qt.red,
            ТипЯчеекПроект.Контур: Qt.green,
        }
        return colors.get(t, Qt.white)

    def get_label(self, t: ТипЯчеекПроект) -> str:
        labels = {
            ТипЯчеекПроект.Пол: "П",
            ТипЯчеекПроект.Модуль: "М",
            ТипЯчеекПроект.Инструмент: "И",
            ТипЯчеекПроект.Препятствие: "Б",
            ТипЯчеекПроект.Финиш: "Ф",
            ТипЯчеекПроект.Контур: "К",
        }
        return labels.get(t, "")

    def update_status(self):
        remaining = sum(1 for row in self.maze.ячейки for c in row if c.тип_ячейки in (ТипЯчеекПроект.Пол, ТипЯчеекПроект.Модуль))
        pos = f"({self.robot.текущая_ячейка.x},{self.robot.текущая_ячейка.y})" if self.robot and self.robot.текущая_ячейка else "не размещён"
        self.status.setText(f"Робот: {pos} | Осталось П/М: {remaining} | Шаги: {self.steps}")

    def prepare_runtime(self):
        self.robot = РоботИнженер(self.maze)
        self.runtime = MissionRuntime(self.maze, self.robot)
        self.steps = 0

    def on_run(self):
        if self.running:
            return
        self.prepare_runtime()
        self.running = True
        self.timer.start(100)

    def on_step(self):
        if self.running:
            return
        if not self.runtime:
            self.prepare_runtime()
        self.runtime.step()
        self.steps += 1
        self.redraw()

    def tick(self):
        if not self.running:
            return
        self.runtime.step()
        self.steps += 1
        if self.runtime.done:
            self.running = False
            self.timer.stop()
        self.redraw()

    def on_reset(self):
        if self.running:
            return
        self.maze.ИнициализироватьЛабиринт(ТипЯчеекПроект.Пол, 10, 8)
        self.editor = MazeEditor(self.maze)
        self.editor.set_cell_type(9, 7, ТипЯчеекПроект.Финиш)
        self.editor.place_robot(0, 0)
        self.runtime = None
        self.running = False
        self.redraw()

    def on_demo(self):
        if self.running:
            return
        self.on_reset()
        for x in range(2, 8):
            self.editor.set_cell_type(x, 3, ТипЯчеекПроект.Препятствие)
        self.editor.set_cell_type(3, 2, ТипЯчеекПроект.Инструмент)
        self.editor.set_cell_type(1, 1, ТипЯчеекПроект.Модуль)
        self.editor.set_cell_type(4, 4, ТипЯчеекПроект.Пол)
        self.redraw()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())