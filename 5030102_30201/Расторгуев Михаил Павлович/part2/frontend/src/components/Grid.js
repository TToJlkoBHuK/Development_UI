import React from 'react';
import './Grid.css';

const CELL_TYPES = {
  0: { name: 'Пусто', symbol: 'П', className: 'empty' },
  1: { name: 'Труба', symbol: 'Т', className: 'pipe' },
  2: { name: 'Соединено', symbol: 'С', className: 'connected' },
  3: { name: 'Подвал', symbol: 'Подв', className: 'basement' },
  4: { name: 'Стена', symbol: '■', className: 'wall' },
  5: { name: 'Вода', symbol: '~', className: 'water' },
  6: { name: 'Финиш', symbol: 'F', className: 'finish' }
};

function Grid({ grid, robotPosition, width, height }) {
  const renderCell = (cell, x, y) => {
    const cellType = CELL_TYPES[cell.тип_ячейки] || CELL_TYPES[0];
    const isRobot = robotPosition[0] === x && robotPosition[1] === y;
    
    return (
      <div
        key={`${x}-${y}`}
        className={`cell ${cellType.className} ${isRobot ? 'robot' : ''}`}
      >
        <span className="cell-symbol">{cellType.symbol}</span>
        {isRobot && <div className="robot-marker">R</div>}
      </div>
    );
  };

  return (
    <div className="grid-container">
      <div 
        className="grid"
        style={{
          gridTemplateColumns: `repeat(${width}, 60px)`,
          gridTemplateRows: `repeat(${height}, 60px)`
        }}
      >
        {[...Array(height)].map((_, y) => {
          const displayY = height - 1 - y;
          return [...Array(width)].map((_, x) => 
            renderCell(grid[displayY][x], x, displayY)
          );
        })}
      </div>
    </div>
  );
}

export default Grid;
