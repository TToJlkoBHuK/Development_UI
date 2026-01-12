const WIDTH = 7;
const HEIGHT = 5;

let maze;
let robot;
let isWorking = false;

function createTestGrid(width, height) {
    const cellValues = [];
    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            let cellValue;
            if (x === 0 && y === 0) {
                cellValue = CellType.FLOOR | 0x8;
            } else if (x === width - 1 && y === height - 1) {
                cellValue = CellType.FINISH;
            } else if ((x === 2 && y === 1) || (x === 3 && y === 2)) {
                cellValue = CellType.WALL;
            } else if (x === 1 && y === 2) {
                cellValue = CellType.BLOCK;
            } else if ((x + y) % 3 === 0) {
                cellValue = CellType.PANEL;
            } else {
                cellValue = CellType.FLOOR;
            }
            row.push(cellValue);
        }
        cellValues.push(row);
    }
    return cellValues;
}

function drawGrid() {
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    grid.style.gridTemplateColumns = `repeat(${WIDTH}, 70px)`;

    for (let y = HEIGHT - 1; y >= 0; y--) {
        for (let x = 0; x < WIDTH; x++) {
            const cell = maze.getCell(x, y);
            const cellDiv = document.createElement('div');
            cellDiv.className = 'cell';
            
            const typeNames = ['floor', 'panel', 'active', 'sluice', 'wall', 'block', 'finish'];
            const labels = ['П', 'Пн', 'А', 'Ш', '■', '▓', 'F'];
            
            cellDiv.classList.add(typeNames[cell.type] || 'floor');
            cellDiv.textContent = labels[cell.type] || '';

            if (cell.hasRobot) {
                const robotDiv = document.createElement('div');
                robotDiv.className = 'robot';
                robotDiv.textContent = 'R';
                cellDiv.appendChild(robotDiv);
            }

            grid.appendChild(cellDiv);
        }
    }
}

function updateInfo(text) {
    document.getElementById('info').textContent = text;
}

function makeStep() {
    const cell = robot.currentCell;
    if (!cell) return;
    
    if (cell.type === CellType.FINISH) {
        updateInfo('Работа завершена');
        isWorking = false;
        document.getElementById('startBtn').disabled = false;
        drawGrid();
        return;
    }

    if (cell.type === CellType.FLOOR) {
        robot.floor();
        updateInfo(`Позиция (${robot.currentCell.x}, ${robot.currentCell.y}): Пол → Панель`);
        drawGrid();
        return;
    } else if (cell.type === CellType.PANEL) {
        robot.panel();
        updateInfo(`Позиция (${robot.currentCell.x}, ${robot.currentCell.y}): Панель → Активно`);
        drawGrid();
        return;
    }

    const moved = robot.moveTowardsGoal();
    if (!moved) {
        updateInfo('Нет доступного пути к целям');
        isWorking = false;
        document.getElementById('startBtn').disabled = false;
    } else {
        updateInfo(`Движение к позиции (${robot.currentCell.x}, ${robot.currentCell.y})`);
    }
    drawGrid();
}

function startWork() {
    isWorking = true;
    document.getElementById('startBtn').disabled = true;
    automaticWork();
}

function automaticWork() {
    if (!isWorking) {
        document.getElementById('startBtn').disabled = false;
        return;
    }

    const cell = robot.currentCell;
    
    if (cell && cell.type === CellType.FINISH) {
        updateInfo('Работа завершена');
        isWorking = false;
        document.getElementById('startBtn').disabled = false;
        return;
    }

    makeStep();
    
    if (isWorking) {
        setTimeout(automaticWork, 200);
    }
}

function resetGame() {
    isWorking = false;
    document.getElementById('startBtn').disabled = false;
    
    const cellValues = createTestGrid(WIDTH, HEIGHT);
    maze = new OperatorRobotMaze(WIDTH, HEIGHT, cellValues);
    robot = new OperatorRobot(maze);
    
    drawGrid();
    updateInfo('Готов к работе');
}

const cellValues = createTestGrid(WIDTH, HEIGHT);
maze = new OperatorRobotMaze(WIDTH, HEIGHT, cellValues);
robot = new OperatorRobot(maze);
drawGrid();