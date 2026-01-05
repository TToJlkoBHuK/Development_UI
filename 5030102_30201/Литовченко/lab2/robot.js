const CellType = {
    FLOOR: 0x0,
    PANEL: 0x1,
    ACTIVE: 0x2,
    SLUICE: 0x3,
    WALL: 0x4,
    BLOCK: 0x5,
    FINISH: 0x6
};

class OperatorRobotCell {
    constructor(x, y, cellValue = 0x0) {
        this.x = x;
        this.y = y;
        this.hasRobot = (cellValue & 0x8) !== 0;
        this.type = this.cellTypeFromValue(cellValue);
    }

    cellTypeFromValue(value) {
        const baseValue = value & 0x7;
        return baseValue;
    }
}

class OperatorRobotMaze {
    constructor(width = 0, height = 0, cells = null) {
        this.width = width;
        this.height = height;
        this.cells = [];

        if (cells !== null) {
            this.loadFromValues(cells);
        } else if (width > 0 && height > 0) {
            this.initializeMaze();
        }
    }

    loadFromValues(cellValues) {
        if (!cellValues || cellValues.length === 0) {
            this.height = 0;
            this.width = 0;
            this.cells = [];
            return;
        }

        this.height = cellValues.length;
        this.width = cellValues[0].length;
        this.cells = [];

        for (let y = 0; y < this.height; y++) {
            const row = [];
            for (let x = 0; x < this.width; x++) {
                const cellValue = cellValues[y][x];
                const cell = new OperatorRobotCell(x, y, cellValue);
                row.push(cell);
            }
            this.cells.push(row);
        }
    }

    initializeMaze(cellType = CellType.FLOOR) {
        this.cells = [];
        for (let y = 0; y < this.height; y++) {
            const row = [];
            for (let x = 0; x < this.width; x++) {
                const cell = new OperatorRobotCell(x, y, cellType);
                row.push(cell);
            }
            this.cells.push(row);
        }
    }

    getCell(x, y) {
        if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
            return this.cells[y][x];
        }
        return null;
    }

    isFree(x, y) {
        if (x < 0 || x >= this.width || y < 0 || y >= this.height) return false;
        const cell = this.getCell(x, y);
        return cell && cell.type !== CellType.WALL && cell.type !== CellType.BLOCK;
    }
}

class OperatorRobot {
    constructor(maze) {
        this.maze = maze;
        this.currentCell = null;

        if (maze && maze.cells) {
            for (let y = 0; y < maze.height; y++) {
                for (let x = 0; x < maze.width; x++) {
                    const cell = maze.getCell(x, y);
                    if (cell && cell.hasRobot) {
                        this.currentCell = cell;
                        return;
                    }
                }
            }
        }
    }

    moveToCell(newCell) {
        if (newCell && newCell.type !== CellType.WALL && newCell.type !== CellType.BLOCK) {
            if (this.currentCell) {
                this.currentCell.hasRobot = false;
            }
            this.currentCell = newCell;
            newCell.hasRobot = true;
            return newCell;
        }
        return null;
    }

    channelForward() {
        if (this.maze && this.currentCell) {
            const newCell = this.maze.getCell(this.currentCell.x, this.currentCell.y + 1);
            return this.moveToCell(newCell);
        }
        return null;
    }

    channelBackward() {
        if (this.maze && this.currentCell) {
            const newCell = this.maze.getCell(this.currentCell.x, this.currentCell.y - 1);
            return this.moveToCell(newCell);
        }
        return null;
    }

    channelLeft() {
        if (this.maze && this.currentCell) {
            const newCell = this.maze.getCell(this.currentCell.x - 1, this.currentCell.y);
            return this.moveToCell(newCell);
        }
        return null;
    }

    channelRight() {
        if (this.maze && this.currentCell) {
            const newCell = this.maze.getCell(this.currentCell.x + 1, this.currentCell.y);
            return this.moveToCell(newCell);
        }
        return null;
    }

    liftDiag() {
        if (this.maze && this.currentCell) {
            const newCell = this.maze.getCell(this.currentCell.x - 1, this.currentCell.y + 1);
            return this.moveToCell(newCell);
        }
        return null;
    }

    descendDiag() {
        if (this.maze && this.currentCell) {
            const newCell = this.maze.getCell(this.currentCell.x + 1, this.currentCell.y - 1);
            return this.moveToCell(newCell);
        }
        return null;
    }

    panel() {
        if (this.currentCell && this.currentCell.type === CellType.PANEL) {
            this.currentCell.type = CellType.ACTIVE;
        }
    }

    floor() {
        if (this.currentCell && this.currentCell.type === CellType.FLOOR) {
            this.currentCell.type = CellType.PANEL;
        }
    }

    findNearestTargets() {
        const targets = [];
        for (let y = 0; y < this.maze.height; y++) {
            for (let x = 0; x < this.maze.width; x++) {
                const cell = this.maze.getCell(x, y);
                if (cell && (cell.type === CellType.FLOOR || cell.type === CellType.PANEL)) {
                    targets.push([x, y]);
                }
            }
        }
        if (targets.length > 0) return targets;

        for (let y = 0; y < this.maze.height; y++) {
            for (let x = 0; x < this.maze.width; x++) {
                const cell = this.maze.getCell(x, y);
                if (cell && cell.type === CellType.FINISH) {
                    return [[x, y]];
                }
            }
        }
        return [];
    }

    bfsNextStep(start, goals) {
        const goalsSet = new Set(goals.map(g => `${g[0]},${g[1]}`));
        const queue = [[start[0], start[1]]];
        const prev = { [`${start[0]},${start[1]}`]: null };

        while (queue.length > 0) {
            const [x, y] = queue.shift();
            const key = `${x},${y}`;

            if (goalsSet.has(key)) {
                let cur = [x, y];
                let curKey = key;
                const startKey = `${start[0]},${start[1]}`;
                
                while (prev[curKey] !== null) {
                    const prevPos = prev[curKey];
                    const prevKey = `${prevPos[0]},${prevPos[1]}`;
                    if (prevKey === startKey) {
                        return cur;
                    }
                    cur = prevPos;
                    curKey = prevKey;
                }
                return null;
            }

            const neighbors = [
                [x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1],
                [x - 1, y + 1], [x + 1, y - 1]
            ];

            for (const [nx, ny] of neighbors) {
                const nKey = `${nx},${ny}`;
                if (!prev.hasOwnProperty(nKey) && this.maze.isFree(nx, ny)) {
                    prev[nKey] = [x, y];
                    queue.push([nx, ny]);
                }
            }
        }
        return null;
    }

    moveTowardsGoal() {
        const goals = this.findNearestTargets();
        if (goals.length === 0) return false;

        const nextPos = this.bfsNextStep([this.currentCell.x, this.currentCell.y], goals);
        if (!nextPos) return false;

        const [nx, ny] = nextPos;
        const newCell = this.maze.getCell(nx, ny);
        return this.moveToCell(newCell) !== null;
    }
}