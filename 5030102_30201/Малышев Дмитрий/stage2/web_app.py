import streamlit as st
import random
import time


# ==================== КЛАССЫ ====================

class Maze:
    def __init__(self):
        self.width = 5
        self.height = 5
        self.grid = []
        self.robot_x = 0
        self.robot_y = 0
        self.history = []
        self.mission_completed = False
        self.finish_x = None
        self.finish_y = None
        self.init_default_map()

    def init_default_map(self):
        """Создает карту по умолчанию"""
        self.grid = []
        for y in range(5):
            row = []
            for x in range(5):
                row.append("road")  # Дорога
            self.grid.append(row)

        self.grid[4][4] = "finish"  # Финиш (4,4)
        self.grid[4][3] = "barrier"  # Барьер (3,4)
        self.grid[4][2] = "post"  # Пост (2,4)
        self.grid[4][1] = "fire"  # Пожар (1,4)

        self.grid[3][3] = "fire"  # Пожар (3,3)
        self.grid[3][1] = "filled"  # Залитое (1,3)

        self.grid[2][3] = "post"  # Пост (3,2)
        self.grid[2][1] = "fire"  # Пожар (1,2)
        self.grid[2][0] = "barrier"  # Барьер (0,2)

        self.grid[1][2] = "filled"  # Залитое (2,1)

        self.grid[0][4] = "post"  # Пост (4,0)
        self.grid[0][3] = "barrier"  # Барьер (3,0)

        self.robot_x = 0
        self.robot_y = 0
        self.mission_completed = False

        self.find_finish_position()

    def init_random_map(self):
        """Создает случайную карту"""
        self.grid = []
        for y in range(5):
            row = []
            for x in range(5):
                row.append("road")  # Дорога
            self.grid.append(row)

        cell_types = ["fire", "fire", "fire", "filled", "filled",
                      "barrier", "barrier", "post", "post", "finish"]
        random.shuffle(cell_types)

        positions = []
        for y in range(5):
            for x in range(5):
                if not (x == 0 and y == 0):
                    positions.append((x, y))

        random.shuffle(positions)

        for i, (x, y) in enumerate(positions):
            if i < len(cell_types):
                self.grid[y][x] = cell_types[i]

        self.robot_x = 0
        self.robot_y = 0
        self.mission_completed = False

        self.find_finish_position()

    def find_finish_position(self):
        """Находит координаты клетки финиша"""
        self.finish_x = None
        self.finish_y = None
        for y in range(5):
            for x in range(5):
                if self.grid[y][x] == "finish":
                    self.finish_x = x
                    self.finish_y = y
                    return

    def get_cell_color(self, cell_type):
        """Возвращает цвет клетки"""
        colors = {
            "road": "#FFFFFF",  # Белый
            "fire": "#FF0000",  # Красный
            "filled": "#FFA500",  # Оранжевый
            "finish": "#00FF00",  # Зеленый
            "post": "#800080",  # Фиолетовый
            "barrier": "#000000",  # Черный
        }
        return colors.get(cell_type, "#808080")  # Серый по умолчанию

    def get_cell_text(self, cell_type):
        """Возвращает текст для клетки (без робота)"""
        texts = {
            "road": "",
            "fire": "🔥",
            "filled": "💧",
            "finish": "🏁",
            "post": "📯",
            "barrier": "⬛",
        }
        return texts.get(cell_type, "?")

    def get_cell_name(self, cell_type):
        """Возвращает название типа клетки"""
        names = {
            "road": "Дорога",
            "fire": "Пожар",
            "filled": "Залитое",
            "finish": "Финиш",
            "post": "Пост",
            "barrier": "Барьер",
        }
        return names.get(cell_type, "Неизвестно")

    def can_move_to(self, x, y):
        """Проверяет, может ли робот переместиться в клетку"""
        if x < 0 or x >= 5 or y < 0 or y >= 5:
            return False
        if self.grid[y][x] == "barrier":
            return False
        return True

    def move_robot(self, dx, dy, direction_name):
        """Перемещает робота"""
        new_x = self.robot_x + dx
        new_y = self.robot_y + dy

        if self.can_move_to(new_x, new_y):
            old_x, old_y = self.robot_x, self.robot_y
            self.robot_x = new_x
            self.robot_y = new_y

            self.mission_completed = False

            timestamp = time.strftime("%H:%M:%S")
            cell_name = self.get_cell_name(self.grid[new_y][new_x])
            self.history.append(
                f"[{timestamp}] {direction_name}: ({old_x},{old_y}) → ({new_x},{new_y}) [{cell_name}]")
            return True
        else:
            timestamp = time.strftime("%H:%M:%S")
            self.history.append(f"[{timestamp}] Не могу двигаться {direction_name}!")
            return False

    def extinguish_fire(self):
        """Тушит пожар на текущей клетке (Пожар -> Залитое)"""
        current_cell = self.grid[self.robot_y][self.robot_x]
        timestamp = time.strftime("%H:%M:%S")

        if current_cell == "fire":
            self.grid[self.robot_y][self.robot_x] = "filled"

            self.mission_completed = False

            self.history.append(f"[{timestamp}] Потушен пожар в ({self.robot_x},{self.robot_y})")
            return True
        else:
            self.history.append(f"[{timestamp}] Здесь нет пожара для тушения")
            return False

    def place_post(self):
        """Ставит пост на текущей клетке (Залитое -> Пост)"""
        current_cell = self.grid[self.robot_y][self.robot_x]
        timestamp = time.strftime("%H:%M:%S")

        if current_cell == "filled":
            self.grid[self.robot_y][self.robot_x] = "post"

            self.mission_completed = False

            self.history.append(f"[{timestamp}] Поставлен пост в ({self.robot_x},{self.robot_y})")
            return True
        else:
            self.history.append(f"[{timestamp}] Здесь нельзя поставить пост (нужна залитая клетка)")
            return False

    def check_mission_complete(self):
        """Проверяет, выполнена ли миссия"""
        if self.mission_completed:
            return True

        if self.grid[self.robot_y][self.robot_x] != "finish":
            return False

        for y in range(5):
            for x in range(5):
                cell = self.grid[y][x]
                if cell in ["fire", "filled"]:
                    return False

        self.mission_completed = True
        return True

    def display_maze_css(self):
        """Создает CSS Grid для лабиринта"""
        css = """
        <style>
        .maze-container {
            display: grid;
            grid-template-columns: repeat(5, 80px);
            grid-template-rows: repeat(5, 80px);
            gap: 5px;
            margin: 20px auto;
            width: fit-content;
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 10px;
            border: 3px solid #333;
        }
        .maze-cell {
            width: 80px;
            height: 80px;
            border: 2px solid #666;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            font-weight: bold;
            border-radius: 5px;
            position: relative;
        }
        .cell-coords {
            position: absolute;
            bottom: 2px;
            right: 2px;
            font-size: 10px;
            color: #666;
        }
        .robot-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 45px;
            z-index: 2;
        }
        .finish-cell {
            outline: 3px solid #00FF00;
            outline-offset: -3px;
        }
        </style>
        """

        html = css + '<div class="maze-container">'

        for y in range(4, -1, -1):
            for x in range(5):
                cell_type = self.grid[y][x]
                has_robot = (x == self.robot_x and y == self.robot_y)
                is_finish = (cell_type == "finish")
                color = self.get_cell_color(cell_type)
                text = self.get_cell_text(cell_type)

                text_color = "#000000"
                if color in ["#000000", "#800080", "#FF0000"]:
                    text_color = "#FFFFFF"

                cell_class = "maze-cell"
                if is_finish:
                    cell_class += " finish-cell"

                html += f'<div class="{cell_class}" style="background-color:{color};color:{text_color}" title="{self.get_cell_name(cell_type)} ({x},{y})">{text}<div class="cell-coords">({x},{y})</div>'

                if has_robot:
                    html += f'<div class="robot-overlay">🤖</div>'

                html += '</div>'

        html += '</div>'
        return html

def main():
    st.set_page_config(
        page_title="Робот-Пожарный Лабиринт",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 Робот-Пожарный Лабиринт 5x5")

    if 'maze' not in st.session_state:
        st.session_state.maze = Maze()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Карта лабиринта")

        try:
            maze_html = st.session_state.maze.display_maze_css()
            st.markdown(maze_html, unsafe_allow_html=True)
        except:
            st.warning("Графическое отображение не поддерживается.")

        st.markdown("""
        **Легенда:**
        - 🤖 - Робот (отображается поверх клетки)
        - 🔥 - Пожар (красный) - можно тушить
        - 💧 - Залитое (оранжевый) - можно ставить пост
        - 🏁 - Финиш (зеленый) - цель миссии
        - 📯 - Пост (фиолетовый) - завершающий этап
        - ⬛ - Барьер (черный)
        - ⬜ - Дорога (белый)

        **Цель:** Дойти до 🏁 (финиша), потушить все 🔥 (пожары) и поставить 📯 (посты) на всех 💧 (залитых клетках)
        """)

    with col2:
        st.subheader("Управление")

        mission_complete = st.session_state.maze.check_mission_complete()

        finish_info = ""
        if st.session_state.maze.finish_x is not None and st.session_state.maze.finish_y is not None:
            finish_info = f"({st.session_state.maze.finish_x},{st.session_state.maze.finish_y})"

        if mission_complete:
            st.success("🎉 Миссия выполнена! Все пожары потушены и робот на финише!")
            st.balloons()

        st.markdown("**Информация:**")
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.metric("Позиция робота", f"({st.session_state.maze.robot_x},{st.session_state.maze.robot_y})")
        with col_info2:
            cell_type = st.session_state.maze.grid[st.session_state.maze.robot_y][st.session_state.maze.robot_x]
            st.metric("Тип клетки", st.session_state.maze.get_cell_name(cell_type))

        if finish_info:
            st.info(f"🏁 Финиш находится на позиции: {finish_info}")

        st.markdown("---")

        st.markdown("**Движение:**")

        col_up = st.columns(3)
        with col_up[1]:
            if st.button("↑ Вперед", key="up", disabled=mission_complete):
                st.session_state.maze.move_robot(0, 1, "Вперед")
                st.rerun()

        col_mid = st.columns(3)
        with col_mid[0]:
            if st.button("← Влево", key="left", disabled=mission_complete):
                st.session_state.maze.move_robot(-1, 0, "Влево")
                st.rerun()
        with col_mid[2]:
            if st.button("→ Вправо", key="right", disabled=mission_complete):
                st.session_state.maze.move_robot(1, 0, "Вправо")
                st.rerun()

        col_down = st.columns(3)
        with col_down[1]:
            if st.button("↓ Назад", key="down", disabled=mission_complete):
                st.session_state.maze.move_robot(0, -1, "Назад")
                st.rerun()

        st.markdown("---")

        st.markdown("**Действия:**")
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("🚒 Потушить", key="fire", disabled=mission_complete):
                st.session_state.maze.extinguish_fire()
                st.rerun()
        with col_act2:
            if st.button("📯 Пост", key="post", disabled=mission_complete):
                st.session_state.maze.place_post()
                st.rerun()

        st.markdown("---")

        st.markdown("**Управление игрой:**")
        if st.button("✅ Проверить миссию", key="check"):
            if st.session_state.maze.check_mission_complete():
                st.rerun()
            else:
                current_cell = st.session_state.maze.grid[st.session_state.maze.robot_y][st.session_state.maze.robot_x]
                on_finish = (current_cell == "finish")

                if not on_finish:
                    st.warning(
                        f"Миссия не выполнена! Робот не на финише. Текущая позиция: ({st.session_state.maze.robot_x},{st.session_state.maze.robot_y})")
                else:
                    has_fire_or_filled = False
                    for y in range(5):
                        for x in range(5):
                            cell = st.session_state.maze.grid[y][x]
                            if cell in ["fire", "filled"]:
                                has_fire_or_filled = True
                                break
                        if has_fire_or_filled:
                            break

                    if has_fire_or_filled:
                        st.warning("Миссия не выполнена! Есть непотушенные пожары или незалитые клетки.")
                    else:
                        st.warning("Миссия не выполнена! Проверьте условия.")

        col_game1, col_game2 = st.columns(2)
        with col_game1:
            if st.button("🔄 Сброс", key="reset"):
                st.session_state.maze = Maze()
                st.rerun()
        with col_game2:
            if st.button("🎲 Случайный", key="random"):
                st.session_state.maze = Maze()
                st.session_state.maze.init_random_map()
                st.rerun()

    st.markdown("---")
    st.subheader("История действий")

    if st.session_state.maze.history:
        for action in st.session_state.maze.history[-10:]:
            st.text(action)
    else:
        st.text("Действий еще нет")


if __name__ == "__main__":
    main()