from __future__ import annotations

from enum import Enum
from typing import List, Iterator, Optional


class ТипНаправленийХимНапр(Enum):
    ВперёдX = "ВперёдX"
    НазадX = "НазадX"
    ВлевоX = "ВлевоX"
    ВправоX = "ВправоX"
    ДиагXB = "ДиагXB"
    ДиагXH = "ДиагXH"


class ТипЯчеекХимии(Enum):
    Пусто = "Пусто"
    Реактив = "Реактив"
    Обработано = "Обработано"
    Контейнер = "Контейнер"
    Опасно = "Опасно"
    Барьер = "Барьер"
    Финиш = "Финиш"


class ЯчейкаРоботХимик:
    def __init__(
            self,
            тип_ячейки: Optional[ТипЯчеекХимии] = None,
            ячейка_робота: bool = False,
            x: int = 0,
            y: int = 0,
    ) -> None:
        self.ячейка_робота: bool = ячейка_робота
        self.тип_ячейки: Optional[ТипЯчеекХимии] = тип_ячейки
        self.x: int = x
        self.y: int = y

    def __repr__(self) -> str:
        return f"Ячейка({self.x},{self.y}):{self.тип_ячейки.name if self.тип_ячейки else None}"


class ЛабиринтРоботХимик:
    def __init__(
            self,
            ширина: int = 0,
            длина: int = 0,
    ) -> None:
        self.ширина: int = ширина
        self.длина: int = длина
        self.ячейки: List[List[ЯчейкаРоботХимик]] = []

    def ПолучитьСоседнююЯчейку(
            self,
            текущая_ячейка: ЯчейкаРоботХимик,
            направление_поиска: ТипНаправленийХимНапр,
    ) -> Optional[ЯчейкаРоботХимик]:
        if текущая_ячейка is None:
            return None

        if not self.ячейки:
            return None

        x, y = текущая_ячейка.x, текущая_ячейка.y

        if направление_поиска == ТипНаправленийХимНапр.ВперёдX:
            dx, dy = (0, -1)
        elif направление_поиска == ТипНаправленийХимНапр.НазадX:
            dx, dy = (0, 1)
        elif направление_поиска == ТипНаправленийХимНапр.ВлевоX:
            dx, dy = (-1, 0)
        elif направление_поиска == ТипНаправленийХимНапр.ВправоX:
            dx, dy = (1, 0)
        elif направление_поиска == ТипНаправленийХимНапр.ДиагXB:
            dx, dy = (-1, -1)
        elif направление_поиска == ТипНаправленийХимНапр.ДиагXH:
            dx, dy = (1, 1)
        else:
            return None

        nx, ny = x + dx, y + dy

        if not (0 <= nx < self.ширина and 0 <= ny < self.длина):
            return None

        соседняя = self.ячейки[ny][nx]

        if соседняя.тип_ячейки in (ТипЯчеекХимии.Опасно, ТипЯчеекХимии.Барьер):
            return None

        return соседняя

    def ПолучитьИтератор(self) -> Iterator[ЯчейкаРоботХимик]:
        if not self.ячейки:
            return iter(())

        x = 0
        y = self.длина - 1
        direction = 1

        while True:
            yield self.ячейки[y][x]

            if direction == 1:
                if x < self.ширина - 1:
                    x += 1
                else:
                    if y == 0:
                        break
                    y -= 1
                    direction = -1
            else:  # движемся влево
                if x > 0:
                    x -= 1
                else:
                    if y == 0:
                        break
                    y -= 1
                    direction = 1

    def ИнициализироватьЛабиринт(
            self,
            тип_ячейки: ТипЯчеекХимии,
    ) -> None:
        # Создаем ячейки
        self.ячейки = []
        for y in range(self.длина):
            row = []
            for x in range(self.ширина):
                row.append(ЯчейкаРоботХимик(тип_ячейки=тип_ячейки, x=x, y=y))
            self.ячейки.append(row)


class РоботХимик:
    def __init__(self, лабиринт: ЛабиринтРоботХимик) -> None:
        self.лабиринт: ЛабиринтРоботХимик = лабиринт
        self.текущая_ячейка: Optional[ЯчейкаРоботХимик] = None

        # Находим робота в лабиринте
        for row in self.лабиринт.ячейки:
            for cell in row:
                if cell.ячейка_робота:
                    self.текущая_ячейка = cell
                    return

        # Если робот не найден, ставим его в первую доступную ячейку
        if self.текущая_ячейка is None:
            for row in self.лабиринт.ячейки:
                for cell in row:
                    if cell.тип_ячейки not in (ТипЯчеекХимии.Опасно, ТипЯчеекХимии.Барьер):
                        cell.ячейка_робота = True
                        self.текущая_ячейка = cell
                        return

    def _переместить_робота(self, направление: ТипНаправленийХимНапр) -> Optional[ЯчейкаРоботХимик]:
        if self.текущая_ячейка is None:
            return None

        цель = self.лабиринт.ПолучитьСоседнююЯчейку(self.текущая_ячейка, направление)

        if цель is None:
            return None

        # Перемещаем робота
        self.текущая_ячейка.ячейка_робота = False
        цель.ячейка_робота = True
        self.текущая_ячейка = цель

        return цель

    def ДвигВперёд(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ВперёдX)

    def Отодвинуть(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.НазадX)

    def СдвинутьВлево(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ВлевоX)

    def СдвинутьВправо(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ВправоX)

    def Подняться(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ДиагXB)

    def Спуститься(self) -> Optional[ЯчейкаРоботХимик]:
        return self._переместить_робота(ТипНаправленийХимНапр.ДиагXH)

    def Реактив(self) -> None:
        if self.текущая_ячейка is None:
            return
        self.текущая_ячейка.тип_ячейки = ТипЯчеекХимии.Обработано

    def Пусто(self) -> None:
        if self.текущая_ячейка is None:
            return

        self.текущая_ячейка.тип_ячейки = ТипЯчеекХимии.Реактив
