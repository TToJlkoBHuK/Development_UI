import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Grid from './components/Grid';
import Controls from './components/Controls';
import './App.css';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [state, setState] = useState(null);
  const [message, setMessage] = useState('Готов к работе');
  const [isRunning, setIsRunning] = useState(false);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    loadState();
  }, []);

  const loadState = async () => {
    try {
      const response = await axios.get(`${API_URL}/state`);
      setState(response.data);
    } catch (error) {
      console.error('Ошибка загрузки состояния:', error);
      setMessage('Ошибка подключения к серверу');
    }
  };

  const handleStep = async () => {
    if (finished) return;

    try {
      const response = await axios.post(`${API_URL}/step`);
      setState(response.data.state);
      setMessage(response.data.message);

      if (response.data.finished) {
        setFinished(true);
        setIsRunning(false);
      }
    } catch (error) {
      console.error('Ошибка шага:', error);
      setMessage('Ошибка выполнения шага');
    }
  };

  const handleReset = async () => {
    try {
      const response = await axios.post(`${API_URL}/reset`);
      setState(response.data);
      setMessage('Лабиринт сброшен');
      setFinished(false);
      setIsRunning(false);
    } catch (error) {
      console.error('Ошибка сброса:', error);
      setMessage('Ошибка сброса');
    }
  };

  const handleStart = () => {
    if (finished) return;
    setIsRunning(true);
  };

  const handleStop = () => {
    setIsRunning(false);
  };

  useEffect(() => {
    let interval;
    if (isRunning && !finished) {
      interval = setInterval(() => {
        handleStep();
      }, 200);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, finished]);

  if (!state) {
    return (
      <div className="App">
        <div className="loading">Загрузка...</div>
      </div>
    );
  }

  return (
    <div className="App">
      <div className="container">
        <h1 className="title">🔧 Робот Сантехник</h1>

        <div className="info-panel">
          <div className="message">{message}</div>
          {finished && <div className="finish-badge">✅ ФИНИШ!</div>}
        </div>

        <Grid 
          grid={state.ячейки} 
          robotPosition={state.текущая_позиция}
          width={state.ширина}
          height={state.длина}
        />

        <Controls
          onStep={handleStep}
          onStart={handleStart}
          onStop={handleStop}
          onReset={handleReset}
          isRunning={isRunning}
          finished={finished}
        />

        <div className="legend">
          <h3>Легенда:</h3>
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-color empty"></div>
              <span>Пусто (П)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color pipe"></div>
              <span>Труба (Т)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color connected"></div>
              <span>Соединено (С)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color wall"></div>
              <span>Стена (■)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color water"></div>
              <span>Вода (~)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color finish"></div>
              <span>Финиш (F)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
