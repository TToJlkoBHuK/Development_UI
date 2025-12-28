async function moveRobot(direction) {
    showLoading();
    try {
        const response = await fetch(`/move/${direction}`, {
            method: 'POST'
        });
        const data = await response.json();
        updateInterface(data);
        showNotification(data.message, data.success ? 'success' : 'error');
    } catch (error) {
        showNotification("Ошибка соединения с сервером", "error");
    }
}

async function repairDetail() {
    showLoading();
    try {
        const response = await fetch('/repair', {
            method: 'POST'
        });
        const data = await response.json();
        updateInterface(data);
        showNotification(data.message, data.success ? 'success' : 'info');
    } catch (error) {
        showNotification("Ошибка соединения с сервером", "error");
    }
}

async function executeTask() {
    showLoading();
    try {
        const response = await fetch('/execute_task', {
            method: 'POST'
        });
        const data = await response.json();
        updateInterface(data);
        showNotification(data.message, 'success');
    } catch (error) {
        showNotification("Ошибка соединения с сервером", "error");
    }
}

async function resetField() {
    showLoading();
    try {
        const response = await fetch('/reset', {
            method: 'POST'
        });
        const data = await response.json();
        updateInterface(data);
        showNotification("Поле успешно сброшено!", 'success');
    } catch (error) {
        showNotification("Ошибка соединения с сервером", "error");
    }
}

function updateInterface(data) {
    document.getElementById('workshop-field').innerHTML = data.svg;
    document.getElementById('robot-position').textContent = `(${data.robot_position.x}, ${data.robot_position.y})`;
    document.getElementById('cell-type').textContent = data.cell_type;
}

function showNotification(message, type) {
    const container = document.getElementById('notification-container');
    
    const notification = document.createElement('div');
    notification.className = `notification p-4 rounded-xl mb-3 shadow-lg text-white font-bold ${
        type === 'success' ? 'bg-green-600' :
        type === 'error' ? 'bg-red-600' :
        'bg-blue-600'
    }`;
    
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${
                type === 'success' ? 'fa-check-circle' :
                type === 'error' ? 'fa-exclamation-triangle' :
                'fa-info-circle'
            } text-2xl mr-3"></i>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (container.contains(notification)) {
                container.removeChild(notification);
            }
        }, 500);
    }, 3000);
}

function showLoading() {
    document.getElementById('workshop-field').innerHTML = `
        <div class="flex justify-center items-center h-96">
            <div class="animate-spin rounded-full h-24 w-24 border-t-4 border-b-4 border-robot"></div>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', function() {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.8s ease-in-out';
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
});