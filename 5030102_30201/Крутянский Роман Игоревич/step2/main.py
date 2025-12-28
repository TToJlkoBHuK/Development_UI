import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from enum import Enum, auto
from typing import Optional, Iterator, List

class WorkshopCellType(Enum):
    Floor = auto()
    Detail = auto()
    Repaired = auto()
    Tool = auto()
    Obstacle = auto()
    Oil = auto()
    Finish = auto()

class BaseDirection(Enum):
    N = auto()
    S = auto()
    W = auto()
    E = auto()
    NW = auto()
    SE = auto()

class WorkDirection(Enum):
    Forward = auto()
    Backward = auto()
    Left = auto()
    Right = auto()
    DiagUp = auto()
    DiagDown = auto()

class SideDirection:
    def __init__(self, side: BaseDirection, direction: WorkDirection):
        self.side = side
        self.direction = direction

SIDE_DIRECTION_1 = SideDirection(BaseDirection.N, WorkDirection.Forward)
SIDE_DIRECTION_2 = SideDirection(BaseDirection.S, WorkDirection.Backward)
SIDE_DIRECTION_3 = SideDirection(BaseDirection.W, WorkDirection.Left)
SIDE_DIRECTION_4 = SideDirection(BaseDirection.E, WorkDirection.Right)
SIDE_DIRECTION_5 = SideDirection(BaseDirection.NW, WorkDirection.DiagUp)
SIDE_DIRECTION_6 = SideDirection(BaseDirection.SE, WorkDirection.DiagDown)

class MethodDirection:
    def __init__(self, method_id: str, direction_value: int):
        self.method_id = method_id
        self.direction_value = direction_value

METHOD_DIRECTION_1 = MethodDirection("ЕхатьКРаботе", WorkDirection.Forward.value)
METHOD_DIRECTION_2 = MethodDirection("Отойти", WorkDirection.Backward.value)
METHOD_DIRECTION_3 = MethodDirection("СместитьВлево", WorkDirection.Left.value)
METHOD_DIRECTION_4 = MethodDirection("СместитьВправо", WorkDirection.Right.value)
METHOD_DIRECTION_5 = MethodDirection("ПоднятьсяДиаг", WorkDirection.DiagUp.value)
METHOD_DIRECTION_6 = MethodDirection("СпуститьсяДиаг", WorkDirection.DiagDown.value)

class WorkshopCell:
    def __init__(self, cell_type: WorkshopCellType, has_robot: bool = False, x: int = 0, y: int = 0):
        self.cell_type = cell_type
        self.has_robot = has_robot
        self.x = x
        self.y = y

class Workshop:
    def __init__(self, width: int, height: int,
                cells: Optional[List[List[WorkshopCell]]] = None):
        self.width = width
        self.height = height
        if cells is None:
            self.cells = [[WorkshopCell(WorkshopCellType.Floor, False, x, y) for y in range(self.height)] for x in range(self.width)]
        else:
            self.cells = cells

    def initialize_workshop(self, cell_type: WorkshopCellType):
        for x in range(self.width):
            for y in range(self.height):
                cell = self.cells[x][y]
                cell.x = x
                cell.y = y
                cell.cell_type = cell_type

    def get_adjacent_cell(self, current_cell: WorkshopCell, direction_value: int) -> Optional[WorkshopCell]:
        direction = WorkDirection(direction_value)

        dx, dy = 0, 0
        if direction == WorkDirection.Forward:
            dy = 1
        elif direction == WorkDirection.Backward:
            dy = -1
        elif direction == WorkDirection.Left:
            dx = -1
        elif direction == WorkDirection.Right:
            dx = 1
        elif direction == WorkDirection.DiagUp:
            dx = -1
            dy = 1
        elif direction == WorkDirection.DiagDown:
            dx = 1
            dy = -1

        nx = current_cell.x + dx
        ny = current_cell.y + dy

        if 0 <= nx < self.width and 0 <= ny < self.height:
            return self.cells[nx][ny]
        return None

    def get_snake_iterator(self) -> Iterator[WorkshopCell]:
        return SnakeIterator(self)

class SnakeIterator:
    def __init__(self, workshop: Workshop):
        self.width = workshop.width
        self.height = workshop.height
        self.workshop = workshop
        self.x = 0
        self.y = 0
        self.direction = "right"
        self.first = True

    def __iter__(self):
        return self

    def __next__(self) -> WorkshopCell:
        if self.first:
            self.first = False
            return self.workshop.cells[self.x][self.y]
        if self.direction == "right":
            if self.x + 1 < self.width:
                self.x += 1
            else:
                if self.y + 1 >= self.height:
                    raise StopIteration
                self.y += 1
                self.direction = "left"
        else:  # "left"
            if self.x - 1 >= 0:
                self.x -= 1
            else:
                if self.y + 1 >= self.height:
                    raise StopIteration
                self.y += 1
                self.direction = "right"
        return self.workshop.cells[self.x][self.y]

class RobotMechanic:
    def __init__(self, workshop: Workshop):
        self.workshop = workshop
        self.current_cell = self._find_robot_cell()

    def _find_robot_cell(self) -> WorkshopCell:
        for x in range(self.workshop.width):
            for y in range(self.workshop.height):
                cell = self.workshop.cells[x][y]
                if cell.has_robot:
                    return cell
        start_cell = self.workshop.cells[0][0]
        start_cell.has_robot = True
        return start_cell

    def move_forward(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_1.direction_value)

    def move_backward(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_2.direction_value)

    def move_left(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_3.direction_value)

    def move_right(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_4.direction_value)

    def move_diag_up(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_5.direction_value)

    def move_diag_down(self) -> Optional[WorkshopCell]:
        return self._move_by_direction_value(METHOD_DIRECTION_6.direction_value)

    def repair_detail(self):
        if self.current_cell.cell_type == WorkshopCellType.Detail:
            self.current_cell.cell_type = WorkshopCellType.Repaired

    def _move_by_direction_value(self, direction_value: int) -> Optional[WorkshopCell]:
        next_cell = self.workshop.get_adjacent_cell(self.current_cell, direction_value)
        if next_cell is None:
            return None
        if next_cell.cell_type in (WorkshopCellType.Obstacle, WorkshopCellType.Oil):
            return None

        self.current_cell.has_robot = False
        next_cell.has_robot = True
        self.current_cell = next_cell
        return next_cell

    def execute_task(self):
        iterator = self.workshop.get_snake_iterator()
        for cell in iterator:
            self.current_cell.has_robot = False
            cell.has_robot = True
            self.current_cell = cell

            if cell.cell_type == WorkshopCellType.Detail:
                self.repair_detail()

            if cell.cell_type == WorkshopCellType.Finish:
                return

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

workshop = Workshop(7, 6)
robot = RobotMechanic(workshop)

def init_demo_field():
    global workshop, robot
    workshop = Workshop(7, 6)
    
    workshop.cells[0][0].has_robot = True
    workshop.cells[1][0].cell_type = WorkshopCellType.Detail
    workshop.cells[2][1].cell_type = WorkshopCellType.Detail
    workshop.cells[4][0].cell_type = WorkshopCellType.Obstacle
    workshop.cells[3][2].cell_type = WorkshopCellType.Oil
    workshop.cells[5][1].cell_type = WorkshopCellType.Tool
    workshop.cells[6][5].cell_type = WorkshopCellType.Finish
    
    workshop.cells[3][4].cell_type = WorkshopCellType.Detail
    workshop.cells[5][3].cell_type = WorkshopCellType.Detail
    
    robot = RobotMechanic(workshop)

init_demo_field()

def generate_svg_field(workshop: Workshop) -> str:
    cell_size = 60
    width = workshop.width * cell_size + 20
    height = workshop.height * cell_size + 20
    offset = 10
    
    svg_elements = []
    
    for x in range(workshop.width + 1):
        svg_elements.append(
            f'<line x1="{offset + x * cell_size}" y1="{offset}" '
            f'x2="{offset + x * cell_size}" y2="{offset + workshop.height * cell_size}" '
            f'stroke="#d1d5db" stroke-width="1"/>'
        )
    
    for y in range(workshop.height + 1):
        svg_elements.append(
            f'<line x1="{offset}" y1="{offset + y * cell_size}" '
            f'x2="{offset + workshop.width * cell_size}" y2="{offset + y * cell_size}" '
            f'stroke="#d1d5db" stroke-width="1"/>'
        )
    
    colors = {
        WorkshopCellType.Floor.name: "#e0e0e0",
        WorkshopCellType.Detail.name: "#ffdd44",
        WorkshopCellType.Repaired.name: "#4caf50",
        WorkshopCellType.Tool.name: "#2196f3",
        WorkshopCellType.Obstacle.name: "#757575",
        WorkshopCellType.Oil.name: "#8d6e63",
        WorkshopCellType.Finish.name: "#ff9800"
    }
    
    for x in range(workshop.width):
        for y in range(workshop.height):
            cell = workshop.cells[x][y]
            model_y = workshop.height - 1 - y
            
            x1 = offset + x * cell_size
            y1 = offset + model_y * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            color = colors.get(cell.cell_type.name, "#ffffff")
            
            svg_elements.append(
                f'<rect x="{x1}" y="{y1}" width="{cell_size}" height="{cell_size}" '
                f'fill="{color}" stroke="#9e9e9e" stroke-width="1" rx="4"/>'
            )
            
            if cell.cell_type in [WorkshopCellType.Detail, WorkshopCellType.Finish]:
                text = "D" if cell.cell_type == WorkshopCellType.Detail else "F"
                svg_elements.append(
                    f'<text x="{(x1+x2)//2}" y="{(y1+y2)//2 + 6}" '
                    f'font-family="Arial" font-size="20" font-weight="bold" '
                    f'text-anchor="middle" fill="black">{text}</text>'
                )
            
            if cell.has_robot:
                svg_elements.append(
                    f'<circle cx="{(x1+x2)//2}" cy="{(y1+y2)//2}" r="{cell_size//3}" '
                    f'fill="#f44336" stroke="#d32f2f" stroke-width="2"/>'
                )
                svg_elements.append(
                    f'<text x="{(x1+x2)//2}" y="{(y1+y2)//2 + 6}" '
                    f'font-family="Arial" font-size="16" font-weight="bold" '
                    f'text-anchor="middle" fill="white">R</text>'
                )
    
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        + "\n".join(svg_elements) +
        '</svg>'
    )

class MoveResponse(BaseModel):
    success: bool
    message: str
    svg: str
    robot_position: dict
    cell_type: str

@app.get("/", response_class=HTMLResponse)
async def get_lab_interface(request: Request):
    svg = generate_svg_field(workshop)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "svg": svg,
        "robot_position": {"x": robot.current_cell.x, "y": robot.current_cell.y},
        "cell_type": robot.current_cell.cell_type.name
    })

@app.post("/move/{direction}")
async def move_robot(direction: str):
    move_methods = {
        "forward": robot.move_forward,
        "backward": robot.move_backward,
        "left": robot.move_left,
        "right": robot.move_right,
        "diag_up": robot.move_diag_up,
        "diag_down": robot.move_diag_down
    }
    
    if direction not in move_methods:
        return MoveResponse(
            success=False,
            message="Неверное направление",
            svg=generate_svg_field(workshop),
            robot_position={"x": robot.current_cell.x, "y": robot.current_cell.y},
            cell_type=robot.current_cell.cell_type.name
        )
    
    result = move_methods[direction]()
    success = result is not None
    
    message = "Успешное перемещение" if success else "Невозможно переместиться: препятствие или граница поля"
    
    return MoveResponse(
        success=success,
        message=message,
        svg=generate_svg_field(workshop),
        robot_position={"x": robot.current_cell.x, "y": robot.current_cell.y},
        cell_type=robot.current_cell.cell_type.name
    )

@app.post("/repair")
async def repair_detail():
    prev_type = robot.current_cell.cell_type
    robot.repair_detail()
    
    success = prev_type == WorkshopCellType.Detail
    message = "Деталь успешно отремонтирована!" if success else "Нечего ремонтировать в этой ячейке"
    
    return MoveResponse(
        success=success,
        message=message,
        svg=generate_svg_field(workshop),
        robot_position={"x": robot.current_cell.x, "y": robot.current_cell.y},
        cell_type=robot.current_cell.cell_type.name
    )

@app.post("/execute_task")
async def execute_full_task():
    robot.execute_task()
    return MoveResponse(
        success=True,
        message="Робот успешно выполнил обход по змейке!",
        svg=generate_svg_field(workshop),
        robot_position={"x": robot.current_cell.x, "y": robot.current_cell.y},
        cell_type=robot.current_cell.cell_type.name
    )

@app.post("/reset")
async def reset_field():
    init_demo_field()
    svg = generate_svg_field(workshop)
    return {
        "success": True,
        "message": "Поле успешно сброшено",
        "svg": svg,
        "robot_position": {"x": robot.current_cell.x, "y": robot.current_cell.y},
        "cell_type": robot.current_cell.cell_type.name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)