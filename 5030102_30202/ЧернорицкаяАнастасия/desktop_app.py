import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QFrame, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont
from main import ТипЯчеекРемесло, ТипНаправленийТехНапр, ЛабиринтРоботТехник, РоботТехник


class CellWidget(QFrame):

    def __init__(self, cell, cell_size = 45):
        super().__init__()
        self.cell = cell
        self.cell_size = cell_size
        self.setFixedSize(cell_size, cell_size)
        self.setLineWidth(2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Цвета для типов ячеек
        colors = {
            ТипЯчеекРемесло.Пол: QColor(255, 255, 255),
            ТипЯчеекРемесло.Оборуд: QColor(255, 255, 0),
            ТипЯчеекРемесло.Починено: QColor(0, 255, 0),
            ТипЯчеекРемесло.Запчасть: QColor(0, 0, 255),
            ТипЯчеекРемесло.Барьер: QColor(255, 0, 0),
            ТипЯчеекРемесло.Финиш: QColor(128, 0, 128),
            ТипЯчеекРемесло.Склад: QColor(128, 128, 128)
        }

        # Рисуем фон
        color = colors.get(self.cell.тип_ячейки, QColor(255, 255, 255))
        painter.fillRect(0, 0, self.cell_size, self.cell_size, QBrush(color))

        # Рисуем рамку
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.drawRect(0, 0, self.cell_size, self.cell_size)

        # Рисуем робота
        if self.cell.ячейка_робота:
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            center_x = self.cell_size // 2
            center_y = self.cell_size // 2
            radius = self.cell_size // 3
            painter.drawEllipse(center_x - radius, center_y - radius,
                                radius * 2, radius * 2)

            # Глаза
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(center_x - radius // 2, center_y - radius // 2,
                                radius // 3, radius // 3)
            painter.drawEllipse(center_x + radius // 4, center_y - radius // 2,
                                radius // 3, radius // 3)


class RobotDesktopApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.labyrinth = None
        self.robot = None
        self.cell_size = 45
        self.move_count = 0
        self.max_moves = 50  # Лимит ходов
        self.init_ui()
        self.create_random_labyrinth()
        QMessageBox.information(self, "Начало игры",
                                "По лабиринту движется Робот Техник!\n\n"
                                "Цель игры:\n"
                                "1. Починить всё оборудование (жёлтые клетки)\n"
                                "2. Забрать все запчасти (синие клетки)\n"
                                "3. Добраться до финиша (фиолетовая клетка)\n\n"
                                "Управление:\n"
                                "Используйте кнопки для движения\n"
                                "Нажмите 'Оборудовать' на клетке с оборудованием\n"
                                "Нажмите 'Взять запчасть' на синей клетке\n\n"
                                "Удачи!")

    def init_ui(self):
        self.setWindowTitle("Робот Техник")
        self.setGeometry(50, 50, 800, 700)
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QHBoxLayout(central_widget)

        # Левая панель - управление
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)

        # Центральная панель - лабиринт
        labyrinth_panel = self.create_labyrinth_panel()
        main_layout.addWidget(labyrinth_panel, 2)

        # Правая панель - информация и легенда
        info_panel = self.create_info_panel()
        main_layout.addWidget(info_panel, 1)

    def create_control_panel(self):
        panel = QGroupBox("Управление")
        layout = QVBoxLayout()

        # Кнопки движения
        movement_group = QGroupBox("Движение")
        movement_layout = QGridLayout()

        # Располагаем кнопки в виде креста
        self.btn_forward = QPushButton("Вперед")
        self.btn_backward = QPushButton("Назад")
        self.btn_left = QPushButton("Влево")
        self.btn_right = QPushButton("Вправо")
        self.btn_upleft = QPushButton("Подняться")
        self.btn_downright = QPushButton("Спуститься")

        for btn in [self.btn_forward, self.btn_backward, self.btn_left,
                    self.btn_right, self.btn_upleft, self.btn_downright]:
            btn.setFixedSize(70, 60)

        movement_layout.addWidget(self.btn_forward, 0, 1)
        movement_layout.addWidget(self.btn_backward, 1, 1)
        movement_layout.addWidget(self.btn_left, 0, 0)
        movement_layout.addWidget(self.btn_right, 0, 2)
        movement_layout.addWidget(self.btn_upleft, 1, 0)
        movement_layout.addWidget(self.btn_downright, 1, 2)

        movement_group.setLayout(movement_layout)

        # Подключаем события
        self.btn_forward.clicked.connect(lambda: self.move_robot(ТипНаправленийТехНапр.ТехВперед))
        self.btn_backward.clicked.connect(lambda: self.move_robot(ТипНаправленийТехНапр.ТехНазад))
        self.btn_left.clicked.connect(lambda: self.move_robot(ТипНаправленийТехНапр.ТехЛево))
        self.btn_right.clicked.connect(lambda: self.move_robot(ТипНаправленийТехНапр.ТехПраво))
        self.btn_upleft.clicked.connect(lambda: self.move_robot(ТипНаправленийТехНапр.ДиагТВ))
        self.btn_downright.clicked.connect(lambda: self.move_robot(ТипНаправленийТехНапр.ДиагТН))

        layout.addWidget(movement_group)

        # Действия робота
        actions_group = QGroupBox("Действия")
        actions_layout = QVBoxLayout()

        self.btn_equip = QPushButton("Оборудовать")
        self.btn_part = QPushButton("Взять запчасть")

        self.btn_equip.clicked.connect(self.repair_equipment)
        self.btn_part.clicked.connect(self.take_part)

        actions_layout.addWidget(self.btn_equip)
        actions_layout.addWidget(self.btn_part)
        actions_group.setLayout(actions_layout)

        layout.addWidget(actions_group)

        # Управление лабиринтом
        manage_group = QGroupBox("Управление лабиринтом")
        manage_layout = QVBoxLayout()

        self.btn_new = QPushButton("Создать новый лабиринт")
        self.btn_finish = QPushButton("Завершить работу")

        self.btn_new.clicked.connect(self.create_random_labyrinth)
        self.btn_finish.clicked.connect(self.finish_work)

        manage_layout.addWidget(self.btn_new)
        manage_layout.addWidget(self.btn_finish)

        manage_group.setLayout(manage_layout)

        layout.addWidget(manage_group)
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def create_labyrinth_panel(self):
        panel = QGroupBox("Лабиринт")
        self.labyrinth_layout = QGridLayout()
        self.labyrinth_layout.setSpacing(0)
        panel.setLayout(self.labyrinth_layout)
        return panel

    def create_info_panel(self):
        panel = QGroupBox("Информация")
        layout = QVBoxLayout()

        # Текущая информация
        info_group = QGroupBox("Текущее состояние")
        info_layout = QVBoxLayout()

        self.lbl_position = QLabel("Позиция: (0, 0)")
        self.lbl_cell_type = QLabel("Тип ячейки: Неизвестно")
        self.lbl_moves = QLabel("Ходов: 0/50")
        self.lbl_status = QLabel("Статус: Не инициализирован")

        # Устанавливаем стили
        self.lbl_position.setStyleSheet("font-size: 12pt; padding: 5px;")
        self.lbl_cell_type.setStyleSheet("font-size: 12pt; padding: 5px;")
        self.lbl_moves.setStyleSheet("font-size: 12pt; padding: 5px; color: #333;")
        self.lbl_status.setStyleSheet("font-size: 12pt; padding: 5px; font-weight: bold;")

        info_layout.addWidget(self.lbl_position)
        info_layout.addWidget(self.lbl_cell_type)
        info_layout.addWidget(self.lbl_moves)
        info_layout.addWidget(self.lbl_status)
        info_group.setLayout(info_layout)

        layout.addWidget(info_group)

        # Обозначения
        legend_group = QGroupBox("Обозначения")
        legend_layout = QVBoxLayout()

        colors = {
            "Пол": QColor(255, 255, 255),
            "Оборуд": QColor(255, 255, 0),
            "Починено": QColor(0, 255, 0),
            "Запчасть": QColor(0, 0, 255),
            "Барьер": QColor(255, 0, 0),
            "Финиш": QColor(128, 0, 128),
            "Склад": QColor(128, 128, 128),
            "Робот": QColor(0, 0, 0)
        }

        for name, color in colors.items():
            legend_item = QWidget()
            item_layout = QHBoxLayout(legend_item)
            item_layout.setContentsMargins(5, 5, 5, 5)

            color_label = QLabel()
            color_label.setFixedSize(20, 20)
            color_label.setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid black;")
            if name == "Робот":
                color_label.setStyleSheet(f"background-color: black; border: 1px solid black; border-radius: 10px;")

            text_label = QLabel(name)
            text_label.setStyleSheet("font-size: 10pt;")
            item_layout.addWidget(color_label)
            item_layout.addWidget(text_label)
            item_layout.addStretch()

            legend_layout.addWidget(legend_item)

        legend_group.setLayout(legend_layout)
        layout.addWidget(legend_group)
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def create_random_labyrinth(self):
        width = 8
        height = 8

        self.labyrinth = ЛабиринтРоботТехник()
        self.labyrinth.ИнициализироватьЛабиринт(ТипЯчеекРемесло.Пол, width, height)
        self.move_count = 0

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

        self.update_display()

    def reset_labyrinth(self):
        self.create_random_labyrinth()

    def update_display(self):
        # Очищаем старые ячейки
        while self.labyrinth_layout.count():
            item = self.labyrinth_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Добавляем новые ячейки
        if self.labyrinth and self.labyrinth.ячейки:
            for robot_y in range(self.labyrinth.длина):
                for x in range(self.labyrinth.ширина):
                    cell = self.labyrinth.ячейки[robot_y][x]
                    cell_widget = CellWidget(cell, self.cell_size)

                    display_y = self.labyrinth.длина - 1 - robot_y
                    self.labyrinth_layout.addWidget(cell_widget, display_y, x)
        self.labyrinth_layout.setSizeConstraint(QGridLayout.SetFixedSize)

        # Обновляем информацию
        if self.robot and self.robot.текущая_ячейка:
            current = self.robot.текущая_ячейка
            self.lbl_position.setText(f"Позиция: ({current.x}, {current.y})")
            cell_type = current.тип_ячейки.value if current.тип_ячейки else "Неизвестно"
            self.lbl_cell_type.setText(f"Тип ячейки: {cell_type}")

            moves_left = self.max_moves - self.move_count
            move_text = f"Ходов: {self.move_count}/{self.max_moves}"
            self.lbl_moves.setText(move_text)

            if self.robot.ЗавершитьРаботу():
                self.lbl_status.setText("Победа!")
                self.lbl_status.setStyleSheet("color: green; font-size: 12pt; font-weight: bold; padding: 5px;")
                QMessageBox.information(self, "Поздравляем!",
                                        "Работа успешно завершена!\nВсе оборудование починено.")
                self.reset_labyrinth()
            else:
                self.lbl_status.setText("Статус: В работе")
                self.lbl_status.setStyleSheet("color: blue; font-size: 12pt; padding: 5px;")

    def move_robot(self, direction):
        if not self.robot:
            QMessageBox.warning(self, "Ошибка", "Робот не инициализирован!")
            return
        if self.move_count >= self.max_moves:
            QMessageBox.warning(self, "Лимит ходов исчерпан!",
                                f"Вы использовали все {self.max_moves} ходов!\n"
                                "Создайте новый лабиринт или завершите игру.")
            return

        result = self.robot.Перейти(direction)
        if result:
            self.move_count+=1
            self.update_display()
        else:
            QMessageBox.warning(self, "Ошибка", "Невозможно переместиться в этом направлении!")

    def repair_equipment(self):
        if self.robot:
            self.robot.Оборуд()
            self.update_display()

    def take_part(self):
        if self.robot:
            self.robot.Запчасть()
            self.update_display()

    def finish_work(self):
        self.close()

def run_desktop_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = RobotDesktopApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_desktop_app()