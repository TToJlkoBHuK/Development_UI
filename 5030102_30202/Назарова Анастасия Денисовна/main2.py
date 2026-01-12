import streamlit as st
import yaml
from enum import Enum


class ТипНаправленийDevOpsНапр(Enum):
    ДеплойВперёд = "ДеплойВперёд"
    ОткатНазад = "ОткатНазад"
    ВлевоСеть = "ВлевоСеть"
    ВправоСеть = "ВправоСеть"
    ДиагDevСЗ = "ДиагDevСЗ"
    ДиагDevЮВ = "ДиагDevЮВ"


class ТипЯчеекСерверов(Enum):
    Сервер = "Сервер"
    Терминал = "Терминал"
    Развернуто = "Развернуто"
    Код = "Код"
    Баг = "Баг"
    Финиш = "Финиш"
    Сеть = "Сеть"


class ЯчейкаРоботПрограммист:
    def __init__(self, тип_ячейки=None, ячейка_робота=False, x=0, y=0):
        self.ячейка_робота = ячейка_робота
        self.тип_ячейки = тип_ячейки
        self.x = x
        self.y = y


class ЛабиринтРоботПрограммист:
    def __init__(self, ширина=5, длина=6):
        self.ширина = ширина
        self.длина = длина
        self.ячейки = []
        self.создать_демо_лабиринт()

    def ПолучитьСоседнююЯчейку(self, текущая_ячейка, направление_поиска):
        if текущая_ячейка is None or not self.ячейки:
            return None

        x, y = текущая_ячейка.x, текущая_ячейка.y

        if направление_поиска == ТипНаправленийDevOpsНапр.ДеплойВперёд:
            dx, dy = (0, 1)
        elif направление_поиска == ТипНаправленийDevOpsНапр.ОткатНазад:
            dx, dy = (0, -1)
        elif направление_поиска == ТипНаправленийDevOpsНапр.ВлевоСеть:
            dx, dy = (-1, 0)
        elif направление_поиска == ТипНаправленийDevOpsНапр.ВправоСеть:
            dx, dy = (1, 0)
        elif направление_поиска == ТипНаправленийDevOpsНапр.ДиагDevСЗ:
            dx, dy = (-1, 1)
        elif направление_поиска == ТипНаправленийDevOpsНапр.ДиагDevЮВ:
            dx, dy = (1, -1)
        else:
            return None

        nx, ny = x + dx, y + dy

        if not (0 <= nx < self.ширина and 0 <= ny < self.длина):
            return None

        соседняя = self.ячейки[ny][nx]

        if соседняя.тип_ячейки in (ТипЯчеекСерверов.Сервер, ТипЯчеекСерверов.Баг):
            return None

        return соседняя

    def ПолучитьИтератор(self):
        if not self.ячейки:
            return iter(())

        x = 0
        y = self.длина - 1
        direction = 1

        while True:
            yield self.ячейки[y][x]

            if direction == 1:
                if x < self.ширина - 1:
                    x += 1
                else:
                    if y == 0:
                        break
                    y -= 1
                    direction = -1
            else:
                if x > 0:
                    x -= 1
                else:
                    if y == 0:
                        break
                    y -= 1
                    direction = 1

    def создать_демо_лабиринт(self):
        data = [
            [14, 6, 3, 4, 1],
            [3, 0, 6, 4, 6],
            [6, 0, 6, 6, 2],
            [1, 0, 4, 4, 1],
            [4, 6, 3, 4, 2],
            [5, 0, 1, 3, 6],
        ]

        self.ячейки = []

        for y in range(self.длина):
            row = []
            for x in range(self.ширина):
                cell_type_val = data[y][x]
                has_robot = cell_type_val == 14
                if has_robot:
                    cell_type_val = 6

                cell_type_map = {
                    0: ТипЯчеекСерверов.Сервер,
                    1: ТипЯчеекСерверов.Терминал,
                    2: ТипЯчеекСерверов.Развернуто,
                    3: ТипЯчеекСерверов.Код,
                    4: ТипЯчеекСерверов.Баг,
                    5: ТипЯчеекСерверов.Финиш,
                    6: ТипЯчеекСерверов.Сеть
                }

                cell_type = cell_type_map.get(cell_type_val, ТипЯчеекСерверов.Сеть)
                row.append(ЯчейкаРоботПрограммист(тип_ячейки=cell_type, ячейка_робота=has_robot, x=x, y=y))
            self.ячейки.append(row)


class РоботПрограммист:
    def __init__(self, лабиринт):
        self.лабиринт = лабиринт
        self.деплоэнергия = None
        self.откатный = None
        self.шаги = 0

        for row in self.лабиринт.ячейки:
            for cell in row:
                if cell.ячейка_робота:
                    self.текущая_ячейка = cell
                    return

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

    def Деплойнуть(self):
        return self._переместить_робота(ТипНаправленийDevOpsНапр.ДеплойВперёд)

    def Откатнуть(self):
        return self._переместить_робота(ТипНаправленийDevOpsНапр.ОткатНазад)

    def СдвинутьВлево(self):
        return self._переместить_робота(ТипНаправленийDevOpsНапр.ВлевоСеть)

    def СдвинутьВправо(self):
        return self._переместить_робота(ТипНаправленийDevOpsНапр.ВправоСеть)

    def ПоднятьКонтейнер(self):
        return self._переместить_робота(ТипНаправленийDevOpsНапр.ДиагDevСЗ)

    def ОпуститьКонтейнер(self):
        return self._переместить_робота(ТипНаправленийDevOpsНапр.ДиагDevЮВ)

    def Код(self):
        if self.текущая_ячейка is None:
            return None

        if self.текущая_ячейка.тип_ячейки == ТипЯчеекСерверов.Код:
            self.текущая_ячейка.тип_ячейки = ТипЯчеекСерверов.Развернуто
            return True
        return False

    def Терминал(self):
        if self.текущая_ячейка is None:
            return None

        if self.текущая_ячейка.тип_ячейки == ТипЯчеекСерверов.Терминал:
            self.текущая_ячейка.тип_ячейки = ТипЯчеекСерверов.Код
            return True
        return False

    def обработать_текущую_ячейку(self):
        if self.текущая_ячейка is None:
            return False

        if self.текущая_ячейка.тип_ячейки == ТипЯчеекСерверов.Терминал:
            self.Терминал()
            self.Код()
            return True

        if self.текущая_ячейка.тип_ячейки == ТипЯчеекСерверов.Код:
            self.Код()
            return True

        return False

    def проверить_цель(self):
        if self.текущая_ячейка is None:
            return False

        for row in self.лабиринт.ячейки:
            for cell in row:
                if cell.тип_ячейки in [ТипЯчеекСерверов.Код, ТипЯчеекСерверов.Терминал]:
                    return False

        return self.текущая_ячейка.тип_ячейки == ТипЯчеекСерверов.Финиш


def init_session_state():
    if 'robot' not in st.session_state:
        maze = ЛабиринтРоботПрограммист(ширина=5, длина=6)
        st.session_state.robot = РоботПрограммист(maze)
        st.session_state.iterator = None
        st.session_state.auto_mode = False
        st.session_state.auto_targets = []
        st.session_state.current_target_index = 0
        st.session_state.logs = ["робот готов к работе"]
        st.session_state.show_success = False
        st.session_state.show_fail = False


def get_cell_color(cell_type):
    colors = {
        "Сервер": "#B3B3B3",
        "Терминал": "#D4DDF1",
        "Развернуто": "#C9E2CD",
        "Код": "#F6D6A1",
        "Баг": "#EBACAB",
        "Финиш": "#896487",
        "Сеть": "#F9F0EE",
    }
    return colors.get(cell_type, "#FFFFFF")


def render_grid():
    robot = st.session_state.robot
    maze = robot.лабиринт

    for y in range(maze.длина - 1, -1, -1):
        cols = st.columns(maze.ширина + 1)

        for x in range(maze.ширина):
            cell = maze.ячейки[y][x]
            cell_type = cell.тип_ячейки.value if cell.тип_ячейки else "Сеть"
            color = get_cell_color(cell_type)

            with cols[x + 1]:
                border_color = "#85A1D2" if cell.ячейка_робота else "#848484"
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
                    <div style="position: absolute; top: 5px; left: 5px; font-size: 10px; color: #666; font-weight: light;">
                        {x},{y}
                    </div>
                    <div style="font-size: 11px; font-weight: light; color: #333; margin-top: 15px;">
                        {cell_type[:4]}
                    </div>
                """, unsafe_allow_html=True)

                if cell.ячейка_робота:
                    st.markdown(
                        '<div style="font-size: 40px; margin-top: -80px; font-weight: bold; color: #85A1D2">🤖</div>',
                        unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

    cols_bottom = st.columns(maze.ширина + 1)


def move_robot(action_name):
    robot = st.session_state.robot
    result = None

    if action_name == "Деплойнуть":
        result = robot.Деплойнуть()
    elif action_name == "Откатнуть":
        result = robot.Откатнуть()
    elif action_name == "СдвинутьВлево":
        result = robot.СдвинутьВлево()
    elif action_name == "СдвинутьВправо":
        result = robot.СдвинутьВправо()
    elif action_name == "ПоднятьКонтейнер":
        result = robot.ПоднятьКонтейнер()
    elif action_name == "ОпуститьКонтейнер":
        result = robot.ОпуститьКонтейнер()

    if result:
        st.session_state.logs.append(f"{action_name} -> ({result.x},{result.y})")
    else:
        st.session_state.logs.append(f"{action_name} невозможно!")

    return result


def start_auto_mode():
    robot = st.session_state.robot
    st.session_state.auto_targets = list(robot.лабиринт.ПолучитьИтератор())
    st.session_state.current_target_index = 0
    st.session_state.auto_mode = True
    st.session_state.logs.append("Авто-режим запущен")


def auto_step():
    if not st.session_state.auto_mode:
        return False

    robot = st.session_state.robot

    if st.session_state.current_target_index >= len(st.session_state.auto_targets):
        st.session_state.auto_mode = False
        st.session_state.logs.append("Авто-режим завершен: пройдены все ячейки")
        check_goal_auto()
        return False

    target_cell = st.session_state.auto_targets[st.session_state.current_target_index]

    if robot.текущая_ячейка is target_cell:
        processed = robot.обработать_текущую_ячейку()
        if processed:
            st.session_state.logs.append(f"Авто: обработана ячейка ({target_cell.x},{target_cell.y})")
        st.session_state.current_target_index += 1
        return True
    else:
        start_x, start_y = robot.текущая_ячейка.x, robot.текущая_ячейка.y
        target_x, target_y = target_cell.x, target_cell.y

        moved = False

        if start_x < target_x:
            result = robot.СдвинутьВправо()
            if result:
                moved = True
                st.session_state.logs.append(f"Авто: Вправо -> ({result.x},{result.y})")
            else:
                st.session_state.logs.append("Авто: Путь заблокирован, пропуск ячейки")
                st.session_state.current_target_index += 1
        elif start_x > target_x:
            result = robot.СдвинутьВлево()
            if result:
                moved = True
                st.session_state.logs.append(f"Авто: Влево -> ({result.x},{result.y})")
            else:
                st.session_state.logs.append("Авто: Путь заблокирован, пропуск ячейки")
                st.session_state.current_target_index += 1
        elif start_y < target_y:
            result = robot.Деплойнуть()
            if result:
                moved = True
                st.session_state.logs.append(f"Авто: Деплой -> ({result.x},{result.y})")
            else:
                st.session_state.logs.append("Авто: Путь заблокирован, пропуск ячейки")
                st.session_state.current_target_index += 1
        elif start_y > target_y:
            result = robot.Откатнуть()
            if result:
                moved = True
                st.session_state.logs.append(f"Авто: Откат -> ({result.x},{result.y})")
            else:
                st.session_state.logs.append("Авто: Путь заблокирован, пропуск ячейки")
                st.session_state.current_target_index += 1

        if not moved and robot.текущая_ячейка is not target_cell:
            st.session_state.logs.append("Авто: Невозможно добраться, пропуск ячейки")
            st.session_state.current_target_index += 1

        return moved


def check_goal():
    robot = st.session_state.robot
    if robot.проверить_цель():
        st.session_state.show_success = True
        st.session_state.logs.append("Цель достигнута!")
    else:
        st.session_state.show_fail = True
        remaining = []
        for row in robot.лабиринт.ячейки:
            for cell in row:
                if cell.тип_ячейки == ТипЯчеекСерверов.Код:
                    remaining.append(f"Код в ({cell.x},{cell.y})")
                elif cell.тип_ячейки == ТипЯчеекСерверов.Терминал:
                    remaining.append(f"Терминал в ({cell.x},{cell.y})")

        if remaining:
            st.session_state.logs.append(f"Цель не достигнута, не обработано {len(remaining)} ячеек")
        elif robot.текущая_ячейка.тип_ячейки != ТипЯчеекСерверов.Финиш:
            st.session_state.logs.append(
                f"Робот не на финише! Позиция: ({robot.текущая_ячейка.x},{robot.текущая_ячейка.y})")
        else:
            st.session_state.logs.append("Все условия выполнены, кроме нахождения на финише")


def check_goal_auto():
    robot = st.session_state.robot
    if robot.проверить_цель():
        st.session_state.show_success = True
    else:
        st.session_state.show_fail = True


def restart_game():
    st.session_state.auto_mode = False
    st.session_state.iterator = None
    st.session_state.auto_targets = []
    st.session_state.current_target_index = 0
    st.session_state.logs = []
    maze = ЛабиринтРоботПрограммист(ширина=5, длина=6)
    st.session_state.robot = РоботПрограммист(maze)
    st.session_state.show_success = False
    st.session_state.show_fail = False
    st.session_state.logs.append("Новая игра")
    st.session_state.logs.append("Робот начинает в позиции (0,0)")


def render_controls():
    st.markdown("### Управление движением")

    col1, col2, col3 = st.columns(3)

    with col2:
        if st.button("Деплой", key="up", use_container_width=True, help="Вперед"):
            move_robot("Деплойнуть")
            st.rerun()

    with col1:
        if st.button("Влево", key="left", use_container_width=True, help="Влево"):
            move_robot("СдвинутьВлево")
            st.rerun()

    with col3:
        if st.button("Вправо", key="right", use_container_width=True, help="Вправо"):
            move_robot("СдвинутьВправо")
            st.rerun()

    with col2:
        if st.button("Откат", key="down", use_container_width=True, help="Назад"):
            move_robot("Откатнуть")
            st.rerun()

    st.markdown("")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Поднять", key="up_left", use_container_width=True, help="Северо-запад"):
            move_robot("ПоднятьКонтейнер")
            st.rerun()

    with col2:
        if st.button("Опустить", key="down_right", use_container_width=True, help="Юго-восток"):
            move_robot("ОпуститьКонтейнер")
            st.rerun()

    st.markdown("### Действия")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Код", key="code", use_container_width=True, help="Код -> Развернуто"):
            robot = st.session_state.robot
            if robot.Код():
                st.session_state.logs.append(f"Код -> Развернуто в ({robot.текущая_ячейка.x},{robot.текущая_ячейка.y})")
            else:
                st.session_state.logs.append("Нет Кода для обработки")
            st.rerun()

    with col2:
        if st.button("Терминал", key="terminal", use_container_width=True, help="Терминал -> Код"):
            robot = st.session_state.robot
            if robot.Терминал():
                st.session_state.logs.append(f"Терминал -> Код в ({robot.текущая_ячейка.x},{robot.текущая_ячейка.y})")
            else:
                st.session_state.logs.append("Нет Терминала для обработки")
            st.rerun()

    st.markdown("### Авто-режим")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Запуск", key="start_auto", use_container_width=True, help="Запустить змейку"):
            start_auto_mode()
            st.rerun()

    with col2:
        if st.button("Шаг", key="next_auto", use_container_width=True,
                     disabled=not st.session_state.auto_mode, help="Следующий шаг авто-режима"):
            auto_step()
            st.rerun()

    with col3:
        if st.button("Стоп", key="stop_auto", use_container_width=True,
                     disabled=not st.session_state.auto_mode, help="Остановить авто-режим"):
            st.session_state.auto_mode = False
            st.session_state.logs.append("Авто-режим остановлен")
            st.rerun()

    st.markdown("")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Проверить цель", key="check", use_container_width=True, help="Проверить выполнение задачи"):
            check_goal()
            st.rerun()

    with col2:
        if st.button("Новая игра", key="restart", use_container_width=True):
            restart_game()
            st.rerun()


def render_stats():
    robot = st.session_state.robot
    current_x = robot.текущая_ячейка.x if robot.текущая_ячейка else 0
    current_y = robot.текущая_ячейка.y if robot.текущая_ячейка else 0
    cell_type = robot.текущая_ячейка.тип_ячейки.value if robot.текущая_ячейка else "Неизвестно"

    st.markdown("### Информация")

    st.text(f"Шагов: {robot.шаги}")
    st.text(f"Позиция: {current_x},{current_y}")
    st.text(f"Тип ячейки: {cell_type}")
    st.text(f"Авто-режим: {'Активен' if st.session_state.auto_mode else 'Выключен'}")


def render_logs():
    st.markdown("### Лог действий")

    if st.session_state.logs:
        for log in reversed(st.session_state.logs[-15:]):
            st.text(log)
    else:
        st.text("Лог пуст")


def render_legend():
    with st.expander("Легенда цветов"):
        legend_items = [
            ("Сервер", "#B3B3B3", "Запрещенная зона"),
            ("Терминал", "#D4DDF1", "Заменяется на Код"),
            ("Развернуто", "#C9E2CD", "Обработанный Код"),
            ("Код", "#F6D6A1", "Заменяется на Развернуто"),
            ("Баг", "#EBACAB", "Запрещенная зона"),
            ("Финиш", "#896487", "Целевая ячейка"),
            ("Сеть", "#F9F0EE", "Пустая ячейка"),
        ]

        for label, color, desc in legend_items:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(
                    f'<div style="background-color:{color}; width:30px; height:20px; border:1px solid #333; border-radius:4px;"></div>',
                    unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{label}**<br><small>{desc}</small>", unsafe_allow_html=True)


def create_mapping_yaml():
    mapping = {
        'классы': [
            {
                'Класс диаграммы': 'РоботПрограммист',
                'свойства': [
                    {'лабиринт': 'лабиринт'},
                    {'деплоэнергия': 'деплоэнергия'},
                    {'откатный': 'откатный'}
                ],
                'методы': [
                    {'Деплойнуть': 'Деплойнуть'},
                    {'Откатнуть': 'Откатнуть'},
                    {'СдвинутьВлево': 'СдвинутьВлево'},
                    {'СдвинутьПраво': 'СдвинутьВправо'},
                    {'ПоднятьКонтейнер': 'ПоднятьКонтейнер'},
                    {'ОпуститьКонтейнер': 'ОпуститьКонтейнер'},
                    {'Код': 'Код'},
                    {'Терминал': 'Терминал'}
                ]
            },
            {
                'Класс диаграммы': 'ЛабиринтРоботПрограммист',
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
                'Класс диаграммы': 'ЯчейкаРоботПрограммист',
                'свойства': [
                    {'ячейка_робота': 'ячейка_робота'},
                    {'тип_ячейки': 'тип_ячейки'}
                ],
                'методы': []
            }
        ],
        'перечисления': [
            {
                'ПеречислениеНаДиаграмме': 'ТипНаправленийDevOpsНапр',
                'опции': [
                    {'ДеплойВперёд': 'ДеплойВперёд'},
                    {'ОткатНазад': 'ОткатНазад'},
                    {'ВлевоСеть': 'ВлевоСеть'},
                    {'ВправоСеть': 'ВправоСеть'},
                    {'ДиагDevC3': 'ДиагDevСЗ'},
                    {'ДиагDevIOB': 'ДиагDevЮВ'}
                ]
            },
            {
                'ПеречислениеНаДиаграмме': 'ТипЯчеекСерверов',
                'опции': [
                    {'Сервер': 'Сервер'},
                    {'Терминал': 'Терминал'},
                    {'Развернуто': 'Развернуто'},
                    {'Код': 'Код'},
                    {'Баг': 'Баг'},
                    {'Финиш': 'Финиш'},
                    {'Сеть': 'Сеть'}
                ]
            }
        ]
    }

    with open('mapping.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(mapping, f, allow_unicode=True, default_flow_style=False)


def main():
    st.set_page_config(
        page_title="Робот-Программист",
        layout="wide"
    )

    init_session_state()

    st.title("⠀⠀⠀⠀⠀⠀⠀Робот-Программист")

    if st.session_state.auto_mode:
        st.info("Автоматический режим активен")

    if st.session_state.show_success:
        st.success("успешный успех хихихи")
        st.session_state.show_success = False

    if st.session_state.show_fail:
        st.warning("Робот еще не доделал все")
        st.session_state.show_fail = False

    col1, col2 = st.columns([2, 1])

    with col1:
        render_grid()

    with col2:
        render_stats()
        render_controls()
        render_logs()
        render_legend()

    with st.expander("Условие задачи"):
        st.markdown("""
        **Цель задачи:**
        1. Обработать все ячейки типа **Код** и **Терминал**
        2. Завершить программу на ячейке типа **Финиш**

        **Преобразования:**
        - **Код** -> заменяет Код -> Развернуто
        - **Терминал** -> заменяет Терминал -> Код

        **Ограничения перемещения:**
        - Нельзя заходить на ячейки типа: **Сервер**
        - Нельзя заходить на ячейки типа: **Баг**

        **Координатная система:**
        - Ось Y направлена вверх 
        - Ось X направлена вправо
        - Начало координат — в нижней левой ячейке (0,0)

        **Авто-режим:**
        - Движется змейкой по итератору
        - Автоматически обрабатывает ячейки
        - При затыкании пропускает ячейку и продолжает
        """)

    create_mapping_yaml()


if __name__ == "__main__":
    main()
