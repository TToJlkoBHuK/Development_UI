import React from 'react';
import './Controls.css';

function Controls({ onStep, onStart, onStop, onReset, isRunning, finished }) {
  return (
    <div className="controls">
      <button 
        onClick={onStep} 
        disabled={isRunning || finished}
        className="btn btn-step"
      >
        ▶️ Один шаг
      </button>
      
      {!isRunning ? (
        <button 
          onClick={onStart} 
          disabled={finished}
          className="btn btn-start"
        >
          ⏩ Начать работу
        </button>
      ) : (
        <button 
          onClick={onStop}
          className="btn btn-stop"
        >
          ⏸️ Остановить
        </button>
      )}
      
      <button 
        onClick={onReset}
        className="btn btn-reset"
      >
        🔄 Сбросить
      </button>
    </div>
  );
}

export default Controls;
