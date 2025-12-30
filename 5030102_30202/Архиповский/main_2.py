import enum
import streamlit as st
from typing import Optional, List

# Enums
class CellType(enum.Enum):
    RASCOP = "Раскоп"
    ARTEFACT = "Артефакт"
    PESOC = "Песок"
    KLADKA = "Кладка"
    BARRIER = "Барьер"
    FINISH = "Финиш"
    RUINS = "Руины"

class Direction(enum.Enum):
    STEP_RASCOP = "ШагРаскоп"
    STEP_BACK = "ШагНазад"
    STEP_LEFT = "ШагВлево"
    STEP_RIGHT = "ШагВправо"
    DIAG_ARCH_V = "ДиагАрхВ"
    DIAG_ARCH_N = "ДиагАрхН"

# Classes
class RobotCell:
    def __init__(self, cell_type: CellType):
        self.cell_type: CellType = cell_type
        self.has_robot: bool = False

class RobotLabyrinth:
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height
        self.cells: List[RobotCell] = []

    def initialize_labyrinth(self, cell_types_flat: List[CellType]):
        if len(cell_types_flat) != self.width * self.height:
            raise ValueError("Размер данных не соответствует размерам")
        self.cells = [RobotCell(cell_type) for cell_type in cell_types_flat]
        
        start_cell = self._get_cell_at(0, 0)
        if start_cell:
            start_cell.has_robot = True

    def _get_cell_at(self, x: int, y: int) -> Optional[RobotCell]:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[y * self.width + x]
        return None

    def _get_coords_from_cell(self, cell: RobotCell) -> Optional[tuple[int, int]]:
        try:
            index = self.cells.index(cell)
            y = index // self.width
            x = index % self.width
            return x, y
        except ValueError:
            return None

    def get_neighbor_cell(self, current_cell: RobotCell, direction_value: str) -> Optional[RobotCell]:
        coords = self._get_coords_from_cell(current_cell)
        if not coords: return None
        x, y = coords
        
        if direction_value == Direction.STEP_RIGHT.value:      x += 1
        elif direction_value == Direction.STEP_LEFT.value:     x -= 1
        elif direction_value == Direction.DIAG_ARCH_V.value:   y += 1
        elif direction_value == Direction.STEP_BACK.value:     y -= 1
        elif direction_value == Direction.DIAG_ARCH_N.value:   y -= 1
        elif direction_value == Direction.STEP_RASCOP.value:   pass
        
        return self._get_cell_at(x, y)

class RobotArcheolog:
    def __init__(self, labyrinth: RobotLabyrinth):
        self.labyrinth: RobotLabyrinth = labyrinth
        self.current_cell: Optional[RobotCell] = self._find_robot()

    def _find_robot(self) -> Optional[RobotCell]:
        for cell in self.labyrinth.cells:
            if cell.has_robot: return cell
        return None

    def _move_robot(self, direction_value: str) -> Optional[RobotCell]:
        if not self.current_cell: return None
        target_cell = self.labyrinth.get_neighbor_cell(self.current_cell, direction_value)
        
        if not target_cell: return None 
        if target_cell.cell_type in (CellType.KLADKA, CellType.BARRIER): return None
        
        self.current_cell.has_robot = False
        target_cell.has_robot = True
        self.current_cell = target_cell
        return self.current_cell

    def smestitsia_vpravo(self): return self._move_robot(Direction.STEP_RIGHT.value)
    def smestitsia_vlevo(self): return self._move_robot(Direction.STEP_LEFT.value)
    def podniatsia(self): return self._move_robot(Direction.DIAG_ARCH_V.value)

    def dig(self):
        if self.current_cell and self.current_cell.cell_type == CellType.RASCOP:
            self.current_cell.cell_type = CellType.ARTEFACT

    def clear_sand(self):
        if self.current_cell and self.current_cell.cell_type == CellType.PESOC:
            self.current_cell.cell_type = CellType.RASCOP

    def process_current_cell_log(self) -> List[str]:
        logs = []

        while self.current_cell and self.current_cell.cell_type == CellType.PESOC:
            self.clear_sand()
            logs.append("🌪️ Очистка песка -> Раскоп")

        if self.current_cell and self.current_cell.cell_type == CellType.RASCOP:
            self.dig()
            logs.append("⛏️ Раскопки -> Артефакт")
            
        return logs

class WebInterface:

    COLORS = {
        CellType.RASCOP.value: "#D2691E",
        CellType.ARTEFACT.value: "#FFD700",
        CellType.PESOC.value: "#F0E68C",
        CellType.KLADKA.value: "#8B0000",
        CellType.BARRIER.value: "#000000",
        CellType.FINISH.value: "#32CD32",
        CellType.RUINS.value: "#A9A9A9",
    }

    ICONS = {
        CellType.RASCOP.value: "🟫",
        CellType.ARTEFACT.value: "🏆",
        CellType.PESOC.value: "🟨",
        CellType.KLADKA.value: "🧱",
        CellType.BARRIER.value: "⛔",
        CellType.FINISH.value: "🏁",
        CellType.RUINS.value: "🏚️",
    }

    def __init__(self):
        st.set_page_config(page_title="Робот Археолог", layout="centered")
        st.title("🤖 Робот Археолог: Web Версия")
        self._init_session_state()

    def _init_session_state(self):
        if 'robot' not in st.session_state:
            width, height = 4, 3
            cell_data = [
                CellType.PESOC, CellType.RASCOP, CellType.RUINS, CellType.PESOC,
                CellType.RASCOP, CellType.RUINS, CellType.RASCOP, CellType.PESOC,
                CellType.RUINS, CellType.PESOC, CellType.RUINS, CellType.FINISH
            ]
            
            lab = RobotLabyrinth(width, height)
            lab.initialize_labyrinth(cell_data)
            st.session_state['robot'] = RobotArcheolog(lab)
            
            st.session_state['fsm_state'] = "MoveRight"
            st.session_state['last_move_dir'] = None
            st.session_state['logs'] = []
            st.session_state['finished'] = False

    def render_grid(self):
        robot = st.session_state['robot']
        lab = robot.labyrinth
        
        st.write("### Карта участка")
        
        for y in range(lab.height - 1, -1, -1):
            cols = st.columns(lab.width)
            
            for x in range(lab.width):
                cell = lab._get_cell_at(x, y)
                cell_key = cell.cell_type.value 
                color = self.COLORS.get(cell_key, "#FFFFFF")
                icon = self.ICONS.get(cell_key, "❓")
                
                with cols[x]:
                    border_color = "blue" if cell.has_robot else "gray"
                    border_width = "4px" if cell.has_robot else "1px"
                    
                    st.markdown(f"""
                        <div style="
                            background-color: {color};
                            border: {border_width} solid {border_color};
                            border-radius: 5px;
                            height: 60px;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            font-size: 24px;
                            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                        ">
                            {icon}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    coord_text = f"({x},{y})"
                    if cell.has_robot:
                        st.caption(f"**{coord_text}** ⬆️ **BOT**")
                    else:
                        st.caption(f"_{coord_text}_")

    def logic_step(self):
        if st.session_state['finished']:
            return

        robot: RobotArcheolog = st.session_state['robot']
        logs = st.session_state['logs']

        actions = robot.process_current_cell_log()
        for action in actions:
            logs.append(f"Действие: {action}")

        if robot.current_cell and robot.current_cell.cell_type == CellType.FINISH:
            logs.append("🏁 ФИНИШ ДОСТИГНУТ!")
            st.session_state['finished'] = True
            return

        coords = robot.labyrinth._get_coords_from_cell(robot.current_cell)
        if not coords: return
        x, y = coords
        state = st.session_state['fsm_state']
        
        moved = False
        new_pos_log = ""

        if state == "MoveRight":
            if x == robot.labyrinth.width - 1:
                st.session_state['fsm_state'] = "MoveUp"
                st.session_state['last_move_dir'] = "right"
                new_pos_log = "Конец ряда -> Смена на Вверх"
            else:
                if robot.smestitsia_vpravo():
                    moved = True
                    new_pos_log = "Смещение Вправо"
                else:
                    logs.append("❌ Блок справа")

        elif state == "MoveLeft":
            if x == 0:
                st.session_state['fsm_state'] = "MoveUp"
                st.session_state['last_move_dir'] = "left"
                new_pos_log = "Начало ряда -> Смена на Вверх"
            else:
                if robot.smestitsia_vlevo():
                    moved = True
                    new_pos_log = "Смещение Влево"
                else:
                    logs.append("❌ Блок слева")

        elif state == "MoveUp":
            if y == robot.labyrinth.height - 1:
                logs.append("⚠️ Верхний предел")
                st.session_state['finished'] = True
            else:
                if robot.podniatsia():
                    moved = True
                    new_pos_log = "Подъем Вверх"
                    last = st.session_state['last_move_dir']
                    st.session_state['fsm_state'] = "MoveLeft" if last == "right" else "MoveRight"
                else:
                    logs.append("❌ Блок сверху")

        if moved or new_pos_log:
            logs.append(f"Ход: {new_pos_log}")

    def render_controls(self):
        st.divider()
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Управление")
            if st.button("👣 Сделать шаг", disabled=st.session_state['finished'], use_container_width=True):
                self.logic_step()
                st.rerun()

            if st.button("🔄 Заново", use_container_width=True):
                del st.session_state['robot']
                st.rerun()
                
            st.info("🟨 Песок | 🟫 Раскоп | 🏚️ Руины | 🏆 Артефакт")

        with col2:
            st.subheader("Журнал событий")
            with st.container(height=300):
                reversed_logs = st.session_state['logs'][::-1]
                for log in reversed_logs:
                    st.text(log)
            
            if st.session_state['finished']:
                st.success("Миссия завершена!")

if __name__ == "__main__":
    app = WebInterface()
    app.render_grid()
    app.render_controls()
