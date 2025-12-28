# main.py
import tkinter as tk
from enum import Enum
from typing import Optional
import time



class ТипЯчеекСетей(Enum):
    """Типы ячеек сетки"""
    Пусто = 0
    Труба = 1
    Соединено = 2
    Подвал = 3
    Стена = 4
    Вода = 5
    Финиш = 6


class ТипНаправленийВодопровода(Enum):
    """Направления движения"""
    НаправлениеНапор = 0  # Вправо
    НаправлениеСлив = 1   # Влево
    ВлевоПоТрубе = 2      # Влево
    ВправоПоТрубе = 3     # Вправо
    ДиагСевероЗапад = 4   # Диагональ СЗ
    ДиагЮгоВосток = 5     # Диагональ ЮВ




class ЛабиринтРоботСантехник:
    """Класс лабиринта (сетки)"""
    
    def __init__(self, ширина: int, длина: int, ячейки: list):
        self.ширина = ширина
        self.длина = длина
        self.ячейки = ячейки
    
    def получить_соседнюю_ячейку(self, текущая_ячейка, направление_поиска: int):
        """Получить соседнюю ячейку в заданном направлении"""
        x, y = текущая_ячейка
        

        if направление_поиска == ТипНаправленийВодопровода.НаправлениеНапор.value:
            # Вправо
            return self.ячейки[y][x + 1] if x + 1 < self.ширина else None
        elif направление_поиска == ТипНаправленийВодопровода.НаправлениеСлив.value:
            # Влево
            return self.ячейки[y][x - 1] if x - 1 >= 0 else None
        elif направление_поиска == ТипНаправленийВодопровода.ВлевоПоТрубе.value:
            # Влево
            return self.ячейки[y][x - 1] if x - 1 >= 0 else None
        elif направление_поиска == ТипНаправленийВодопровода.ВправоПоТрубе.value:
            # Вправо
            return self.ячейки[y][x + 1] if x + 1 < self.ширина else None
        elif направление_поиска == ТипНаправленийВодопровода.ДиагСевероЗапад.value:
            # Вверх (север)
            return self.ячейки[y + 1][x] if y + 1 < self.длина else None
        elif направление_поиска == ТипНаправленийВодопровода.ДиагЮгоВосток.value:
            # Вниз (юг)
            return self.ячейки[y - 1][x] if y - 1 >= 0 else None
        
        return None
    
    def получить_итератор(self):
        """Получить итератор для обхода лабиринта"""
        return ИтераторЛабиринта(тип_ячейки=ТипЯчеекСетей.Пусто)
    
    def инициализировать_лабиринт(self, тип_ячейки):
        """Инициализировать лабиринт с заданным типом ячейки"""
        pass


class ЯчейкаРоботСантехник:
    """Класс ячейки"""
    
    def __init__(self, ячейка_робота: bool, тип_ячейки: int):
        self.ячейка_робота = ячейка_робота
        self.тип_ячейки = тип_ячейки


class ИтераторЛабиринта:
    """Итератор для обхода лабиринта зигзагом"""
    
    def __init__(self, тип_ячейки):
        self.тип_ячейки = тип_ячейки
        self.current_row = 0
        self.current_col = 0
        self.direction_right = True
    
    def __iter__(self):
        return self
    
    def __next__(self):
        pass



class РоботСантехник:
    """Главный класс робота-сантехника"""
    
    def __init__(self, лабиринт: ЛабиринтРоботСантехник):
        self.лабиринт = лабиринт
        self.ширина = лабиринт.ширина
        self.длина = лабиринт.длина
        self.ячейки = лабиринт.ячейки
        self.текущая_позиция = [0, 0] 
    
    def подвинуть_по_трубе(self):
        """Двигаться по трубе вправо"""
        if self.текущая_позиция[0] < self.ширина - 1:
            next_cell = self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0] + 1]
            if next_cell.тип_ячейки not in [ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value]:
                self.текущая_позиция[0] += 1
                return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        return None
    
    def ответил(self):
        """Проверить текущую ячейку"""
        return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
    
    def сдвинуть_влево(self):
        """Двигаться влево"""
        if self.текущая_позиция[0] > 0:
            next_cell = self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0] - 1]
            if next_cell.тип_ячейки not in [ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value]:
                self.текущая_позиция[0] -= 1
                return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        return None
    
    def сдвинуть_вправо(self):
        """Двигаться вправо"""
        if self.текущая_позиция[0] < self.ширина - 1:
            next_cell = self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0] + 1]
            if next_cell.тип_ячейки not in [ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value]:
                self.текущая_позиция[0] += 1
                return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        return None
    
    def подняться_по_диагр(self):
        """Двигаться вверх"""
        if self.текущая_позиция[1] < self.длина - 1:
            next_cell = self.ячейки[self.текущая_позиция[1] + 1][self.текущая_позиция[0]]
            if next_cell.тип_ячейки not in [ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value]:
                self.текущая_позиция[1] += 1
                return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        return None
    
    def спуститься_по_диагр(self):
        """Двигаться вниз"""
        if self.текущая_позиция[1] > 0:
            next_cell = self.ячейки[self.текущая_позиция[1] - 1][self.текущая_позиция[0]]
            if next_cell.тип_ячейки not in [ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value]:
                self.текущая_позиция[1] -= 1
                return self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        return None
    
    def пусто(self):
        """Обработка ячейки типа Пусто: Пусто → Труба"""
        current_cell = self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        if current_cell.тип_ячейки == ТипЯчеекСетей.Пусто.value:
            current_cell.тип_ячейки = ТипЯчеекСетей.Труба.value
    
    def труба(self):
        """Обработка ячейки типа Труба: Труба → Соединено"""
        current_cell = self.ячейки[self.текущая_позиция[1]][self.текущая_позиция[0]]
        if current_cell.тип_ячейки == ТипЯчеекСетей.Труба.value:
            current_cell.тип_ячейки = ТипЯчеекСетей.Соединено.value




class РоботВизуализатор:
    """Класс для визуализации работы робота через tkinter"""
    
    def __init__(self, робот: РоботСантехник, размер_ячейки=60):
        self.робот = робот
        self.размер_ячейки = размер_ячейки
        
        self.root = tk.Tk()
        self.root.title("Робот Сантехник")
        

        self.цвета = {
            ТипЯчеекСетей.Пусто.value: "white",
            ТипЯчеекСетей.Труба.value: "lightblue",
            ТипЯчеекСетей.Соединено.value: "green",
            ТипЯчеекСетей.Подвал.value: "gray",
            ТипЯчеекСетей.Стена.value: "black",
            ТипЯчеекСетей.Вода.value: "blue",
            ТипЯчеекСетей.Финиш.value: "gold"
        }
        

        canvas_width = робот.ширина * размер_ячейки
        canvas_height = робот.длина * размер_ячейки
        self.canvas = tk.Canvas(self.root, width=canvas_width, height=canvas_height, bg="white")
        self.canvas.pack(padx=10, pady=10)
        

        self.info_label = tk.Label(self.root, text="Готов к работе", font=("Arial", 12))
        self.info_label.pack(pady=5)
        
 
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)
        
        self.start_button = tk.Button(button_frame, text="Начать работу", command=self.начать_работу)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.step_button = tk.Button(button_frame, text="Один шаг", command=self.сделать_шаг)
        self.step_button.pack(side=tk.LEFT, padx=5)
        

        self.робот_маркер = None
        
        self.отрисовать_сетку()
    
    def отрисовать_сетку(self):
        """Отрисовать сетку"""
        self.canvas.delete("all")
        

        for y in range(self.робот.длина):
            for x in range(self.робот.ширина):

                display_y = self.робот.длина - 1 - y
                
                ячейка = self.робот.ячейки[y][x]
                цвет = self.цвета.get(ячейка.тип_ячейки, "white")
                
                x1 = x * self.размер_ячейки
                y1 = display_y * self.размер_ячейки
                x2 = x1 + self.размер_ячейки
                y2 = y1 + self.размер_ячейки
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=цвет, outline="gray")
                

                text = ""
                if ячейка.тип_ячейки == ТипЯчеекСетей.Пусто.value:
                    text = "П"
                elif ячейка.тип_ячейки == ТипЯчеекСетей.Труба.value:
                    text = "Т"
                elif ячейка.тип_ячейки == ТипЯчеекСетей.Соединено.value:
                    text = "С"
                elif ячейка.тип_ячейки == ТипЯчеекСетей.Стена.value:
                    text = "■"
                elif ячейка.тип_ячейки == ТипЯчеекСетей.Вода.value:
                    text = "~"
                elif ячейка.тип_ячейки == ТипЯчеекСетей.Финиш.value:
                    text = "F"
                
                if text:
                    self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, font=("Arial", 10))
        

        self.отрисовать_робота()
    
    def отрисовать_робота(self):
        """Отрисовать робота на текущей позиции"""
        if self.робот_маркер:
            self.canvas.delete(self.робот_маркер)
        
        x, y = self.робот.текущая_позиция
        display_y = self.робот.длина - 1 - y
        
        x_center = x * self.размер_ячейки + self.размер_ячейки / 2
        y_center = display_y * self.размер_ячейки + self.размер_ячейки / 2
        radius = self.размер_ячейки / 3
        
        self.робот_маркер = self.canvas.create_oval(
            x_center - radius, y_center - radius,
            x_center + radius, y_center + radius,
            fill="red", outline="darkred", width=2
        )
        
        self.canvas.create_text(x_center, y_center, text="R", font=("Arial", 14, "bold"), fill="white")
    
    def обновить_информацию(self, текст):
        """Обновить информационную панель"""
        self.info_label.config(text=текст)

    def _свободна(self, xn, yn):
        if not (0 <= xn < self.робот.ширина and 0 <= yn < self.робот.длина):
            return False
        t = self.робот.ячейки[yn][xn].тип_ячейки
        return t not in (ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value)

    def _найти_ближайшую_цель(self):

        targets = []
        for y in range(self.робот.длина):
            for x in range(self.робот.ширина):
                t = self.робот.ячейки[y][x].тип_ячейки
                if t in (ТипЯчеекСетей.Пусто.value, ТипЯчеекСетей.Труба.value):
                    targets.append((x, y))
        if targets:
            return targets
        for y in range(self.робот.длина):
            for x in range(self.робот.ширина):
                if self.робот.ячейки[y][x].тип_ячейки == ТипЯчеекСетей.Финиш.value:
                    return [(x, y)]
        return []

    def _bfs_следующий_шаг(self, start, goals):
        from collections import deque
        goals = set(goals)

        q = deque([start])
        prev = {start: None}

        while q:
            x, y = q.popleft()
            if (x, y) in goals:
                cur = (x, y)
                while prev[cur] is not None and prev[cur] != start:
                    cur = prev[cur]
                return cur if cur != start else None

            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in prev and self._свободна(nx, ny):
                    prev[(nx, ny)] = (x, y)
                    q.append((nx, ny))

        return None

    def переместить_робота(self):
        x, y = self.робот.текущая_позиция
        goals = self._найти_ближайшую_цель()
        if not goals:
            self.обновить_информацию("Целей нет (нет Пусто/Труба и не найден Финиш)")
            return False

        nxt = self._bfs_следующий_шаг((x, y), goals)
        if nxt is None:
            self.обновить_информацию("Путь к цели не найден (всё перекрыто стенами/водой)")
            return False

        nx, ny = nxt
        if nx == x + 1:
            return self.робот.сдвинуть_вправо() is not None
        if nx == x - 1:
            return self.робот.сдвинуть_влево() is not None
        if ny == y + 1:
            return self.робот.подняться_по_диагр() is not None
        if ny == y - 1:
            return self.робот.спуститься_по_диагр() is not None

        return False

    
    def сделать_шаг(self):
        """Сделать один шаг работы"""
        current_cell = self.робот.ответил()
        x, y = self.робот.текущая_позиция
        
        # Обработка текущей ячейки
        if current_cell.тип_ячейки == ТипЯчеекСетей.Пусто.value:
            self.робот.пусто()
            self.обновить_информацию(f"Позиция ({x}, {y}): Пусто → Труба")
        elif current_cell.тип_ячейки == ТипЯчеекСетей.Труба.value:
            self.робот.труба()
            self.обновить_информацию(f"Позиция ({x}, {y}): Труба → Соединено")
        elif current_cell.тип_ячейки == ТипЯчеекСетей.Финиш.value:
            self.обновить_информацию(f"Позиция ({x}, {y}): ФИНИШ! Работа завершена!")
            self.отрисовать_сетку()
            return
        else:
            self.обновить_информацию(f"Позиция ({x}, {y}): Ячейка не требует обработки")
        
        # Перемещение (простой алгоритм зигзага)
        self.переместить_робота()
        
        self.отрисовать_сетку()
        self.root.update()
    
    def переместить_робота_зигзаг(self):
        """Зигзаг: вправо ↑ влево ↑ с обходом, но с приоритетом подъёма на границе"""
        x, y = self.робот.текущая_позиция

        def в_границах(xn, yn):
            return 0 <= xn < self.робот.ширина and 0 <= yn < self.робот.длина

        def свободна(xn, yn):
            if not в_границах(xn, yn):
                return False
            t = self.робот.ячейки[yn][xn].тип_ячейки
            return t not in (ТипЯчеекСетей.Стена.value, ТипЯчеекСетей.Вода.value)


        на_правом_краю = (x == self.робот.ширина - 1)
        на_левом_краю = (x == 0)


        if свободна(x, y + 1):
            if (y % 2 == 0 and на_правом_краю) or (y % 2 == 1 and на_левом_краю):
                self.робот.подняться_по_диагр()
                return


        dx = 1 if y % 2 == 0 else -1


        nx = x + dx
        if свободна(nx, y):
            if dx == 1:
                self.робот.сдвинуть_вправо()
            else:
                self.робот.сдвинуть_влево()
            return


        ближайшая_свободная = None
        лучшая_дистанция = None


        for xx in range(x + 1, self.робот.ширина):
            if свободна(xx, y):
                dist = abs(xx - x)
                ближайшая_свободная = xx
                лучшая_дистанция = dist
                break

    
        for xx in range(x - 1, -1, -1):
            if свободна(xx, y):
                dist = abs(xx - x)
                if лучшая_дистанция is None or dist < лучшая_дистанция:
                    ближайшая_свободная = xx
                    лучшая_дистанция = dist
                break


        dist_до_конца = (self.робот.ширина - 1 - x) if dx == 1 else x


        if ближайшая_свободная is None or лучшая_дистанция >= dist_до_конца:
            if свободна(x, y + 1):
                self.робот.подняться_по_диагр()
            else:
                self.обновить_информацию("Нет доступных ходов, робот остановлен")
            return


        if ближайшая_свободная > x:

            if свободна(x + 1, y):
                self.робот.сдвинуть_вправо()
            else:
                self.робот.текущая_позиция[0] = ближайшая_свободная
        elif ближайшая_свободная < x:
            if свободна(x - 1, y):
                self.робот.сдвинуть_влево()
            else:
                self.робот.текущая_позиция[0] = ближайшая_свободная


    
    def начать_работу(self):
        """Начать автоматическую работу робота"""
        self.start_button.config(state=tk.DISABLED)
        self.автоматическая_работа()
    
    def автоматическая_работа(self):
        """Автоматическое выполнение работы с задержкой"""
        current_cell = self.робот.ответил()
        
        if current_cell.тип_ячейки == ТипЯчеекСетей.Финиш.value:
            self.обновить_информацию("РАБОТА ЗАВЕРШЕНА! Робот достиг финиша!")
            self.start_button.config(state=tk.NORMAL)
            return
        
        self.сделать_шаг()
        

        self.root.after(100, self.автоматическая_работа)
    
    def запустить(self):
        """Запустить GUI"""
        self.root.mainloop()



def создать_тестовую_сетку(ширина, длина):
    """Создать тестовую сетку"""
    ячейки = []
    
    for y in range(длина):
        строка = []
        for x in range(ширина):

            if x == 0 and y == 0:

                строка.append(ЯчейкаРоботСантехник(True, ТипЯчеекСетей.Пусто.value))
            elif x == ширина - 1 and y == длина - 1:
    
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Финиш.value))
            elif (x == 2 and y == 1) or (x == 3 and y == 2):
            
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Стена.value))
            elif x == 1 and y == 2:
               
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Вода.value))
            elif (x + y) % 3 == 0:
                
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Труба.value))
            else:
  
                строка.append(ЯчейкаРоботСантехник(False, ТипЯчеекСетей.Пусто.value))
        
        ячейки.append(строка)
    
    return ячейки


def main():

    ширина = 7
    длина = 5
    
    ячейки = создать_тестовую_сетку(ширина, длина)
    лабиринт = ЛабиринтРоботСантехник(ширина, длина, ячейки)
    робот = РоботСантехник(лабиринт)
    визуализатор = РоботВизуализатор(робот)
    визуализатор.запустить()


if __name__ == "__main__":
    main()
