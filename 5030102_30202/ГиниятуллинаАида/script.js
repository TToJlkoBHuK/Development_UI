const CELL_LABELS = {
    "Пол": "П",
    "Модуль": "М",
    "Инструмент": "И",
    "Препятствие": "Б",
    "Финиш": "Ф",
    "Контур": "К"
};

const CELL_CLASSES = {
    "Пол": "pol",
    "Модуль": "modul",
    "Инструмент": "instrument",
    "Препятствие": "prepyatstvie",
    "Финиш": "finish",
    "Контур": "kontur"
};

let intervalId = null;

function renderMaze(data) {
    const table = $('#maze');
    table.empty();
    data.forEach((row, y) => {
        const tr = $('<tr>');
        row.forEach((cell, x) => {
            const td = $('<td>')
                .addClass(CELL_CLASSES[cell.type])
                .text(CELL_LABELS[cell.type])
                .data('x', x)
                .data('y', y);
            if (cell.robot) td.addClass('robot');
            tr.append(td);
        });
        table.append(tr);
    });
}

function updateStatus(text) {
    $('#status').text(text);
}

function loadMaze() {
    $.get('/get_maze', data => {
        renderMaze(data.maze);
        updateStatus(data.status || "Готово");
    });
}

$(document).ready(() => {
    loadMaze();

    $('#maze').on('click contextmenu', 'td', function(e) {
        e.preventDefault();
        const x = $(this).data('x');
        const y = $(this).data('y');
        const button = e.type === 'contextmenu' ? 'right' : 'left';
        $.post('/click', JSON.stringify({x, y, button}), data => {
            renderMaze(data.maze);
            updateStatus(data.status || "Изменено");
        });
    });

    $('#step').click(() => {
        $.get('/step', data => {
            renderMaze(data.maze);
            updateStatus(data.status || "Шаг выполнен");
        });
    });

    $('#run').click(function() {
    if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
        $(this).text('Run');
    } else {
        $(this).text('Pause');
        intervalId = setInterval(() => {
            $.get('/step', data => {
                renderMaze(data.maze);
                updateStatus(data.status);
                if (data.finished) {
                    clearInterval(intervalId);
                    intervalId = null;
                    $('#run').text('Run');
                }
            });
        }, 400);
    }
});

    $('#reset').click(() => {
        $.get('/reset', data => {
            renderMaze(data.maze);
            updateStatus(data.status);
        });
    });

    $('#demo').click(() => {
        $.get('/demo', data => {
            renderMaze(data.maze);
            updateStatus(data.status);
        });
    });
});
