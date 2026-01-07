import streamlit as st
import random
import yaml
from enum import Enum


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
    def __init__(self, тип_ячейки=None, ячейка_робота=False, x=0, y=0):
        self.ячейка_робота = ячейка_робота
        self.тип_ячейки = тип_ячейки
        self.x = x
        self.y = y


class ЛабиринтРоботХимик:
    def __init__(self, ширина=5, длина=5):
        self.ширина = ширина
        self.длина = длина
        self.ячейки = []
        self.создать_случайный_лабиринт()

    def ПолучитьСоседнююЯчейку(self, текущая_ячейка, направление_поиска):
        if текущая_ячейка is None or not self.ячейки:
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

    def ПолучитьИтератор(self):
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

    def создать_случайный_лабиринт(self):
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
    def __init__(self, лабиринт):
        self.лабиринт = лабиринт
        self.шаги = 0
        self.обработано_реактивов = 0
        self.обработано_пустот = 0

        for row in self.лабиринт.ячейки:
            for cell in row:
                if cell.ячейка_робота:
                    self.текущая_ячейка = cell
                    return

        self.лабиринт.ячейки[0][0].ячейка_робота = True
        self.текущая_ячейка = self.лабиринт.ячейки[0][0]

    def _переместить_робота(self, направление):
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

    def ДвигВперёд(self):
        return self._переместить_робота(ТипНаправленийХимНапр.ВперёдX)

    def Отодвинуть(self):
        return self._переместить_робота(ТипНаправленийХимНапр.НазадX)

    def СдвинутьВлево(self):
        return self._переместить_робота(ТипНаправленийХимНапр.ВлевоX)

    def СдвинутьВправо(self):
        return self._переместить_робота(ТипНаправленийХимНапр.ВправоX)

    def Подняться(self):
        return self._переместить_робота(ТипНаправленийХимНапр.ДиагXB)

    def Спуститься(self):
        return self._переместить_робота(ТипНаправленийХимНапр.ДиагXH)

    def Реактив(self):
        if self.текущая_ячейка is None:
            return
        if self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Реактив:
            self.текущая_ячейка.тип_ячейки = ТипЯчеекХимии.Обработано
            self.обработано_реактивов += 1

    def Пусто(self):
        if self.текущая_ячейка is None:
            return
        if self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Пусто:
            self.текущая_ячейка.тип_ячейки = ТипЯчеекХимии.Реактив
            self.обработано_пустот += 1

    def обработать_текущую_ячейку(self):
        if self.текущая_ячейка is None:
            return

        if self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Реактив:
            self.Реактив()
        elif self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Пусто:
            self.Пусто()
            self.Реактив()

    def проверить_цель(self):
        if self.текущая_ячейка is None:
            return False

        for row in self.лабиринт.ячейки:
            for cell in row:
                if cell.тип_ячейки in [ТипЯчеекХимии.Реактив, ТипЯчеекХимии.Пусто]:
                    return False

        return self.текущая_ячейка.тип_ячейки == ТипЯчеекХимии.Финиш


def init_session_state():
    if 'robot' not in st.session_state:
        maze = ЛабиринтРоботХимик(ширина=5, длина=5)
        st.session_state.robot = РоботХимик(maze)
        st.session_state.iterator = None
        st.session_state.auto_mode = False
        st.session_state.logs = []


def get_cell_color(cell_type):
    colors = {
        "Пусто": "white",
        "Реактив": "#90EE90",
        "Обработано": "#87CEEB",
        "Контейнер": "#D3D3D3",
        "Опасно": "#FFB6C1",
        "Барьер": "#696969",
        "Финиш": "#FFD700",
    }
    return colors.get(cell_type, "white")


def render_grid():
    robot = st.session_state.robot
    maze = robot.лабиринт

    st.markdown("### Лабиринт 5×5")

    for y in range(maze.длина - 1, -1, -1):
        cols = st.columns(maze.ширина)

        for x in range(maze.ширина):
            cell = maze.ячейки[y][x]
            cell_type = cell.тип_ячейки.value if cell.тип_ячейки else "Пусто"
            color = get_cell_color(cell_type)

            with cols[x]:
                border_color = "#4A86E8" if cell.ячейка_робота else "#333333"
                border_width = "3px" if cell.ячейка_робота else "1px"

                st.markdown(f"""
                <div style="
                    background-color: {color};
                    border: {border_width} solid {border_color};
                    border-radius: 5px;
                    height: 70px;
                    width: 70px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    margin: 5px auto;
                    position: relative;
                    box-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                ">
                    <div style="position: absolute; top: 5px; left: 5px; font-size: 10px; color: #666; font-weight: bold;">
                        {x},{y}
                    </div>
                    <div style="font-size: 12px; font-weight: bold; color: #333; margin-top: 15px;">
                        {cell_type[:3]}
                    </div>
                """, unsafe_allow_html=True)

                if cell.ячейка_робота:
                    st.markdown(
                        '<div style="font-size: 18px; margin-top: 5px; font-weight: bold; color: #4A86E8;">R</div>',
                        unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)


def move_robot(direction):
    robot = st.session_state.robot
    result = None

    if direction == "Вперёд":
        result = robot.ДвигВперёд()
    elif direction == "Назад":
        result = robot.Отодвинуть()
    elif direction == "Влево":
        result = robot.СдвинутьВлево()
    elif direction == "Вправо":
        result = robot.СдвинутьВправо()
    elif direction == "Подняться":
        result = robot.Подняться()
    elif direction == "Спуститься":
        result = robot.Спуститься()

    if result:
        st.session_state.logs.append(f"Движение {direction} → ({result.x},{result.y})")
    else:
        st.session_state.logs.append(f"Движение {direction}: невозможно!")


def process_cell():
    robot = st.session_state.robot
    old_type = robot.текущая_ячейка.тип_ячейки.value if robot.текущая_ячейка.тип_ячейки else "None"
    robot.обработать_текущую_ячейку()
    new_type = robot.текущая_ячейка.тип_ячейки.value if robot.текущая_ячейка.тип_ячейки else "None"

    if old_type != new_type:
        st.session_state.logs.append(f"Обработка: {old_type} → {new_type}")
    else:
        st.session_state.logs.append(f"Ячейка не требует обработки: {old_type}")


def start_snake():
    robot = st.session_state.robot
    st.session_state.iterator = robot.лабиринт.ПолучитьИтератор()
    st.session_state.auto_mode = True
    st.session_state.logs.append("Запущен автоматический режим (змейка)")


def auto_step():
    if not st.session_state.auto_mode:
        return

    try:
        robot = st.session_state.robot
        next_cell = next(st.session_state.iterator)

        if (next_cell.x == robot.текущая_ячейка.x and
                next_cell.y == robot.текущая_ячейка.y):
            next_cell = next(st.session_state.iterator)

        dx = next_cell.x - robot.текущая_ячейка.x
        dy = next_cell.y - robot.текущая_ячейка.y

        result = None
        if dx == 1 and dy == 0:
            result = robot.СдвинутьВправо()
        elif dx == -1 and dy == 0:
            result = robot.СдвинутьВлево()
        elif dx == 0 and dy == 1:
            result = robot.ДвигВперёд()
        elif dx == 0 and dy == -1:
            result = robot.Отодвинуть()
        elif dx == -1 and dy == 1:
            result = robot.Подняться()
        elif dx == 1 and dy == -1:
            result = robot.Спуститься()

        if result:
            robot.обработать_текущую_ячейку()
            st.session_state.logs.append(f"Авто-шаг → ({result.x},{result.y})")
        else:
            st.session_state.logs.append("Авто-шаг: движение невозможно!")
            st.session_state.auto_mode = False

    except StopIteration:
        st.session_state.logs.append("Автоматический режим завершен: пройдены все ячейки")
        st.session_state.auto_mode = False


def check_goal():
    robot = st.session_state.robot
    if robot.проверить_цель():
        st.success("🎉 Цель достигнута!")
        st.session_state.logs.append("Цель достигнута!")
    else:
        remaining = []
        for row in robot.лабиринт.ячейки:
            for cell in row:
                if cell.тип_ячейки == ТипЯчеекХимии.Реактив:
                    remaining.append(f"Реактив в ({cell.x},{cell.y})")
                elif cell.тип_ячейки == ТипЯчеекХимии.Пусто:
                    remaining.append(f"Пусто в ({cell.x},{cell.y})")

        if remaining:
            st.warning(f"Цель не достигнута! Не обработано: {len(remaining)} ячеек")
            st.session_state.logs.append(f"Цель не достигнута! Не обработано: {len(remaining)} ячеек")
        elif robot.текущая_ячейка.тип_ячейки != ТипЯчеекХимии.Финиш:
            st.warning(f"Робот не на финише! Позиция: ({robot.текущая_ячейка.x},{robot.текущая_ячейка.y})")
            st.session_state.logs.append(
                f"Робот не на финише! Позиция: ({robot.текущая_ячейка.x},{robot.текущая_ячейка.y})")
        else:
            st.info("Все условия выполнены, кроме нахождения на финише")
            st.session_state.logs.append("Все условия выполнены, кроме нахождения на финише")


def restart_game():
    st.session_state.auto_mode = False
    st.session_state.iterator = None
    st.session_state.logs = []
    maze = ЛабиринтРоботХимик(ширина=5, длина=5)
    st.session_state.robot = РоботХимик(maze)
    st.session_state.logs.append("НОВАЯ ИГРА: случайный лабиринт 5x5")
    st.session_state.logs.append("Робот начинает в позиции (0,0)")


def render_controls():
    st.markdown("### Управление движением")

    col1, col2, col3 = st.columns(3)

    with col2:
        if st.button("⬆", key="up", use_container_width=True, help="ДвигВперёд"):
            move_robot("Вперёд")
            st.rerun()

    with col1:
        if st.button("⬅", key="left", use_container_width=True, help="СдвинутьВлево"):
            move_robot("Влево")
            st.rerun()

    with col2:
        if st.button("⚡", key="process", use_container_width=True, type="primary", help="Обработать ячейку"):
            process_cell()
            st.rerun()

    with col3:
        if st.button("➡", key="right", use_container_width=True, help="СдвинутьВправо"):
            move_robot("Вправо")
            st.rerun()

    with col2:
        if st.button("⬇", key="down", use_container_width=True, help="Отодвинуть"):
            move_robot("Назад")
            st.rerun()

    st.markdown("")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("↖ Подняться", key="up_left", use_container_width=True):
            move_robot("Подняться")
            st.rerun()

    with col2:
        if st.button("↘ Спуститься", key="down_right", use_container_width=True):
            move_robot("Спуститься")
            st.rerun()

    st.markdown("### Действия")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Реактив", key="react", use_container_width=True, help="Реактив → Обработано"):
            st.session_state.robot.Реактив()
            st.session_state.logs.append(f"Реактив → Обработано")
            st.rerun()

    with col2:
        if st.button("Пусто", key="empty", use_container_width=True, help="Пусто → Реактив"):
            st.session_state.robot.Пусто()
            st.session_state.logs.append(f"Пусто → Реактив")
            st.rerun()

    st.markdown("### Авто-режим")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("▶", key="start_auto", use_container_width=True, help="Запустить змейку"):
            start_snake()
            st.rerun()

    with col2:
        if st.button("⏭", key="next_auto", use_container_width=True,
                     disabled=not st.session_state.auto_mode, help="Следующий шаг"):
            auto_step()
            st.rerun()

    with col3:
        if st.button("⏹", key="stop_auto", use_container_width=True,
                     disabled=not st.session_state.auto_mode, help="Остановить"):
            st.session_state.auto_mode = False
            st.session_state.logs.append("Автоматический режим остановлен")
            st.rerun()

    st.markdown("")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Проверить", key="check", use_container_width=True):
            check_goal()
            st.rerun()

    with col2:
        if st.button("🔄 Новая", key="restart", use_container_width=True):
            restart_game()
            st.rerun()


def render_logs():
    st.markdown("### Лог действий")

    with st.container(height=300):
        if st.session_state.logs:
            for log in reversed(st.session_state.logs[-15:]):
                st.text(log)
        else:
            st.text("Лог пуст")


def render_legend():
    with st.expander("Легенда цветов"):
        legend_items = [
            ("Пусто", "white", "Пустая ячейка"),
            ("Реактив", "#90EE90", "Химический реактив"),
            ("Обработано", "#87CEEB", "Обработанный реактив"),
            ("Контейнер", "#D3D3D3", "Контейнер"),
            ("Опасно", "#FFB6C1", "Опасная зона"),
            ("Барьер", "#696969", "Препятствие"),
            ("Финиш", "#FFD700", "Финишная ячейка"),
        ]

        for label, color, desc in legend_items:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(
                    f'<div style="background-color:{color}; width:30px; height:20px; border:1px solid black; border-radius:3px;"></div>',
                    unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{label}**<br><small>{desc}</small>", unsafe_allow_html=True)


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
    st.set_page_config(page_title="Робот-Химик", layout="wide")

    st.markdown("""
    <style>
    .main-title {
        font-size: 32px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 20px;
        text-align: center;
    }
    .section-header {
        font-size: 18px;
        font-weight: bold;
        color: #34495e;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    .log-entry {
        font-family: monospace;
        font-size: 12px;
        padding: 2px 0;
        border-bottom: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

    init_session_state()

    st.markdown('<div class="main-title">🤖 Робот-Химик</div>', unsafe_allow_html=True)

    if st.session_state.auto_mode:
        st.info("Автоматический режим активен")

    # Основной макет
    col1, col2 = st.columns([2, 1])

    with col1:
        render_grid()

    with col2:
        render_controls()
        render_logs()
        render_legend()

        with st.expander("Условие задачи"):
            st.markdown("""
            **Цель:**
            1. Обработать все реактивы и пустые ячейки
            2. Закончить на финише

            **Действия:**
            - Реактив → Обработано
            - Пусто → Реактив → Обработано

            **Ограничения:**
            - Нельзя ходить на Опасно и Барьер

            **Координаты:**
            - Y - север (вверх)
            - X - восток (вправо)
            - Начало: (0,0) - нижний левый угол
            """)


if __name__ == "__main__":
    create_mapping_yaml()
    main()
