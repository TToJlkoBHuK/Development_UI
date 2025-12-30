// Application state
let state = {
    maze: null,
    robot: null,
    iterator: null,
    isRunning: false,
    isPaused: false,
    cellSize: 30,
    canvas: null,
    ctx: null,
    robotPosition: { x: 0, y: 0 },
    currentCell: null,
    animationState: 'idle', // idle, moving, transforming
    moveProgress: 0, // 0-1
    transformProgress: 0, // 0-1
    transformationQueue: [],
    transformationTimer: 0,
    MOVE_DURATION: 0.5, // seconds
    TRANSFORM_DURATION: 0.3, // seconds per transformation
    cellTransformations: {}, // tracks transformations applied to each cell
    currentStep: 0,
    totalSteps: 0,
    lastFrameTime: Date.now(),
};

// Cell type enum
const CellType = {
    'Water': 0,
    'Shore': 1,
    'Sample': 2,
    'Network': 3,
    'Barrier': 4,
    'Finish': 5,
    'Channel': 6
};

// Cell colors
const CellColors = {
    'Water': '#4682b4',
    'Shore': '#d2b48c',
    'Sample': '#ff8c00',
    'Network': '#90ee90',
    'Barrier': '#8b4513',
    'Finish': '#32cd32',
    'Channel': '#708090'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    state.canvas = document.getElementById('mazeCanvas');
    state.ctx = state.canvas.getContext('2d');
    
    // Set canvas size
    state.canvas.width = 700;
    state.canvas.height = 600;
    
    // Event listeners
    document.getElementById('sampleMazeBtn').addEventListener('click', createSampleMaze);
    document.getElementById('randomMazeBtn').addEventListener('click', createRandomMaze);
    document.getElementById('playBtn').addEventListener('click', playAnimation);
    document.getElementById('pauseBtn').addEventListener('click', pauseAnimation);
    document.getElementById('resetBtn').addEventListener('click', resetAnimation);
    
    // Start animation loop
    gameLoop();
    
    updateStatus('Ready to create maze');
});

async function createSampleMaze() {
    try {
        updateStatus('Creating sample maze...');
        const response = await fetch('/api/create_maze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'sample' })
        });
        const data = await response.json();
        state.maze = data.maze;
        const height = data.maze.length;
        const width = data.maze[0].length;
        // Robot starts at bottom-left corner
        state.robot = { x: 0, y: height - 1 };
        state.cellTransformations = {};
        state.iterator = null;
        state.isRunning = false;
        state.isPaused = false;
        state.currentStep = 0;
        state.animationState = 'idle';
        state.transformationQueue = [];
        updateStatus('Sample maze created (12x10). Press Play to start animation.');
        updateUI();
    } catch (error) {
        updateStatus('Error creating maze: ' + error.message);
    }
}

async function createRandomMaze() {
    try {
        const inputWidth = parseInt(document.getElementById('widthInput').value) || 15;
        const inputHeight = parseInt(document.getElementById('heightInput').value) || 15;
        
        if (inputWidth < 5 || inputWidth > 30 || inputHeight < 5 || inputHeight > 30) {
            updateStatus('Maze dimensions must be between 5 and 30');
            return;
        }
        
        updateStatus('Creating random maze...');
        const response = await fetch('/api/create_maze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'random', width: inputWidth, height: inputHeight })
        });
        const data = await response.json();
        state.maze = data.maze;
        const mazeHeight = data.maze.length;
        const mazeWidth = data.maze[0].length;
        // Robot starts at bottom-left corner
        state.robot = { x: 0, y: mazeHeight - 1 };
        state.cellTransformations = {};
        state.iterator = null;
        state.isRunning = false;
        state.isPaused = false;
        state.currentStep = 0;
        state.animationState = 'idle';
        state.transformationQueue = [];
        updateStatus(`Random maze created (${mazeWidth}x${mazeHeight}). Press Play to start animation.`);
        updateUI();
    } catch (error) {
        updateStatus('Error creating maze: ' + error.message);
    }
}

async function playAnimation() {
    if (!state.maze) {
        updateStatus('Create a maze first');
        return;
    }
    
    if (!state.iterator) {
        try {
            updateStatus('Getting traversal path...');
            const response = await fetch('/api/get_iterator', { method: 'GET' });
            const data = await response.json();
            state.iterator = data.iterator;
            state.totalSteps = state.iterator.length;
            state.currentStep = 0;
            
            if (state.iterator.length === 0) {
                updateStatus('No cells to visit in this maze');
                return;
            }
        } catch (error) {
            updateStatus('Error getting iterator: ' + error.message);
            return;
        }
    }
    
    state.isRunning = true;
    state.isPaused = false;
    document.getElementById('playBtn').disabled = true;
    document.getElementById('pauseBtn').disabled = false;
    updateStatus('Animation running...');
}

function pauseAnimation() {
    state.isPaused = !state.isPaused;
    const btn = document.getElementById('pauseBtn');
    if (state.isPaused) {
        btn.textContent = 'Resume';
        btn.classList.remove('btn-warning');
        btn.classList.add('btn-success');
        updateStatus('Animation paused');
    } else {
        btn.textContent = 'Pause';
        btn.classList.remove('btn-success');
        btn.classList.add('btn-warning');
        updateStatus('Animation resumed');
    }
}

function resetAnimation() {
    state.isRunning = false;
    state.isPaused = false;
    state.animationState = 'idle';
    state.moveProgress = 0;
    state.transformProgress = 0;
    state.transformationQueue = [];
    state.transformationTimer = 0;
    state.currentStep = 0;
    state.iterator = null;
    
    document.getElementById('playBtn').disabled = false;
    document.getElementById('pauseBtn').disabled = true;
    document.getElementById('pauseBtn').textContent = 'Pause';
    document.getElementById('pauseBtn').classList.remove('btn-success');
    document.getElementById('pauseBtn').classList.add('btn-warning');
    
    updateStatus('Animation reset. Press Play to start.');
    updateUI();
}

function gameLoop() {
    const now = Date.now();
    const dt = (now - state.lastFrameTime) / 1000;
    state.lastFrameTime = now;
    
    if (state.isRunning && !state.isPaused && state.iterator) {
        updateAnimation(dt);
    }
    
    draw();
    requestAnimationFrame(gameLoop);
}

function updateAnimation(dt) {
    if (state.animationState === 'idle') {
        // Move to next cell
        if (state.currentStep < state.iterator.length) {
            const nextCellIndex = state.iterator[state.currentStep];
            const maze = state.maze;
            const width = maze[0].length;
            state.currentCell = {
                x: nextCellIndex % width,
                y: Math.floor(nextCellIndex / width)
            };
            state.animationState = 'moving';
            state.moveProgress = 0;
        } else {
            // Animation finished
            state.isRunning = false;
            document.getElementById('playBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = true;
            updateStatus('Animation finished!');
        }
    }
    
    if (state.animationState === 'moving') {
        state.moveProgress += dt / state.MOVE_DURATION;
        
        if (state.moveProgress >= 1.0) {
            state.moveProgress = 1.0;
            state.robot = state.currentCell;
            state.animationState = 'transforming';
            
            // Queue transformations based on cell type
            const cellType = Object.keys(CellType).find(
                key => CellType[key] === state.maze[state.robot.y][state.robot.x]
            );
            
            state.transformationQueue = [];
            
            if (cellType === 'Shore') {
                state.transformationQueue.push('Shore');
                state.transformationQueue.push('Water');
            } else if (cellType === 'Water') {
                state.transformationQueue.push('Water');
            }
            
            state.transformProgress = 0;
            state.transformationTimer = 0;
        }
    }
    
    if (state.animationState === 'transforming') {
        if (state.transformationQueue.length > 0) {
            state.transformationTimer += dt;
            
            if (state.transformationTimer >= state.TRANSFORM_DURATION) {
                // Apply the transformation
                const transformation = state.transformationQueue.shift();
                const cellKey = `${state.robot.x},${state.robot.y}`;
                
                if (!state.cellTransformations[cellKey]) {
                    state.cellTransformations[cellKey] = [];
                }
                state.cellTransformations[cellKey].push(transformation);
                
                // Update maze
                if (transformation === 'Shore') {
                    state.maze[state.robot.y][state.robot.x] = CellType['Water'];
                } else if (transformation === 'Water') {
                    state.maze[state.robot.y][state.robot.x] = CellType['Sample'];
                }
                
                state.transformationTimer = 0;
            }
        } else {
            // No more transformations, move to next cell
            state.currentStep++;
            state.animationState = 'idle';
            state.moveProgress = 0;
        }
    }
}

function draw() {
    state.ctx.fillStyle = '#f5f5f5';
    state.ctx.fillRect(0, 0, state.canvas.width, state.canvas.height);
    
    if (!state.maze) {
        state.ctx.fillStyle = '#999';
        state.ctx.font = '16px Arial';
        state.ctx.textAlign = 'center';
        state.ctx.fillText('Create a maze to begin', state.canvas.width / 2, state.canvas.height / 2);
        return;
    }
    
    // Calculate cell size to fit maze
    const mazeWidth = state.maze[0].length;
    const mazeHeight = state.maze.length;
    state.cellSize = Math.min(
        (state.canvas.width - 20) / mazeWidth,
        (state.canvas.height - 20) / mazeHeight
    );
    
    const startX = (state.canvas.width - mazeWidth * state.cellSize) / 2;
    const startY = (state.canvas.height - mazeHeight * state.cellSize) / 2;
    
    // Draw maze
    for (let y = 0; y < mazeHeight; y++) {
        for (let x = 0; x < mazeWidth; x++) {
            const cellType = state.maze[y][x];
            const typeName = Object.keys(CellType).find(key => CellType[key] === cellType);
            const px = startX + x * state.cellSize;
            const py = startY + y * state.cellSize;
            
            state.ctx.fillStyle = CellColors[typeName] || '#ccc';
            state.ctx.fillRect(px, py, state.cellSize, state.cellSize);
            
            state.ctx.strokeStyle = '#aaa';
            state.ctx.lineWidth = 1;
            state.ctx.strokeRect(px, py, state.cellSize, state.cellSize);
        }
    }
    
    // Draw robot with animation
    if (state.robot) {
        const targetX = startX + state.robot.x * state.cellSize;
        const targetY = startY + state.robot.y * state.cellSize;
        
        let drawX = targetX;
        let drawY = targetY;
        
        // Interpolate position during movement
        if (state.animationState === 'moving' && state.currentCell) {
            const startCellX = startX + (state.robot.x || state.currentCell.x) * state.cellSize;
            const startCellY = startY + (state.robot.y || state.currentCell.y) * state.cellSize;
            const endCellX = startX + state.currentCell.x * state.cellSize;
            const endCellY = startY + state.currentCell.y * state.cellSize;
            
            drawX = startCellX + (endCellX - startCellX) * state.moveProgress;
            drawY = startCellY + (endCellY - startCellY) * state.moveProgress;
        }
        
        // Draw robot
        state.ctx.fillStyle = '#ff0000';
        state.ctx.beginPath();
        state.ctx.arc(
            drawX + state.cellSize / 2,
            drawY + state.cellSize / 2,
            state.cellSize / 3,
            0,
            Math.PI * 2
        );
        state.ctx.fill();
        
        state.ctx.strokeStyle = '#cc0000';
        state.ctx.lineWidth = 2;
        state.ctx.stroke();
    }
}

function updateUI() {
    const canvas = state.canvas;
    canvas.width = 700;
    canvas.height = 600;
}

function updateStatus(message) {
    document.getElementById('statusText').textContent = message;
}

function updateMessage(message) {
    document.getElementById('messageText').textContent = message;
}
