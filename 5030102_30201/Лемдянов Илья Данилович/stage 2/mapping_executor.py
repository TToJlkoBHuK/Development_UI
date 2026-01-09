# mapping_executor.py (patched)
import yaml
import time
from typing import Dict, List, Any, Callable, Optional
import os

_ALLOWED_METHODS = {
    'go_forward','go_backward','move_left','move_right',
    'move_up_left','move_down_left','process_ore','process_path'
}

def _normalize_key(s: str) -> str:
    return ''.join(s.split()).replace("_", "").casefold()

def _extract_mappings_recursive(obj: Any, allowed_methods: set, out: Dict[str, str]):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and isinstance(v, str):
                vv = v.strip()
                if vv in allowed_methods:
                    out[_normalize_key(k)] = vv
            if isinstance(v, (dict, list)):
                _extract_mappings_recursive(v, allowed_methods, out)
            if isinstance(k, (dict, list)):
                _extract_mappings_recursive(k, allowed_methods, out)
    elif isinstance(obj, list):
        for item in obj:
            _extract_mappings_recursive(item, allowed_methods, out)

def load_mapping(path: str, allowed_methods: Optional[List[str]] = None) -> Dict[str, str]:
    if allowed_methods is None:
        allowed = set(_ALLOWED_METHODS)
    else:
        allowed = set(allowed_methods)

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if data is None:
        return {}

    mapping: Dict[str, str] = {}

    # collect simple pairs at top-level
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str) and isinstance(v, str):
                kv = v.strip()
                if kv in allowed:
                    mapping[_normalize_key(k.strip())] = kv

    # collect recursively
    _extract_mappings_recursive(data, allowed, mapping)

    # fallback: try to include string->string pairs even if method not in allowed (useful for custom mappings)
    if not mapping and isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str) and isinstance(v, str):
                mapping[_normalize_key(k.strip())] = v.strip()

    return mapping

def translate_commands_text(commands_text: str, mapping: Dict[str,str]) -> str:
    """
    Преобразует текст команд в валидный python-скрипт, вставляя вызовы методов и __step__().
    Сохраняет отступы, пустые строки и все конструкции Python (for/if/while).
    """
    out_lines: List[str] = []
    lines = commands_text.splitlines()
    for raw in lines:
        # сохраняем ведущие пробелы/табуляции
        stripped = raw.lstrip('\t ')
        leading = raw[:len(raw)-len(stripped)]
        key = stripped.strip()
        if not key:
            out_lines.append("")  # пустая строка
            continue

        found = None
        # сначала прямое совпадение по нормализованному ключу
        nk = _normalize_key(key)
        if nk in mapping:
            found = mapping[nk]

        if found:
            out_lines.append(f"{leading}{found}()")
            out_lines.append(f"{leading}__step__()")
        else:
            # оставляем строчку как есть (на случай for/if/вложенные блоки)
            out_lines.append(raw)
    return "\n".join(out_lines)

def build_exec_env(robot, delay: float = 0.25, on_step: Optional[Callable[[], None]] = None) -> dict:
    """
    Возвращает словарь окружения (globals) для exec.
    """
    env = {}

    # пробиндим разрешённые методы робота в env (обёртки, чтобы метод вызывался без args)
    for name in _ALLOWED_METHODS:
        if hasattr(robot, name):
            method = getattr(robot, name)
            env[name] = (lambda m: (lambda *a, **kw: m()))(method)

    # полезные встроенные
    env['range'] = range
    env['len'] = len
    env['print'] = print
    env['int'] = int
    env['str'] = str
    env['enumerate'] = enumerate
    env['time'] = time

    # функция, вызываемая после каждого шага (включает delay и on_step callback)
    def __step__():
        try:
            if on_step:
                try:
                    on_step()
                except Exception:
                    pass
        finally:
            if delay and delay > 0:
                time.sleep(delay)

    env['__step__'] = __step__
    env['robot'] = robot

    # обязательно дать доступ к builtins, иначе некоторые конструкции могут не работать
    env['__builtins__'] = __builtins__

    return env

def translate_and_exec(commands_text: str, mapping_path: str, robot, delay: float = 0.25, on_step: Optional[Callable[[], None]] = None, debug: bool = False) -> str:
    """
    Переводит и выполняет команды. Возвращает сгенерированный python-код (полезно для логов).
    debug=True -> печатает скрипт и не подавляет исключения.
    """
    mapping = load_mapping(mapping_path)
    if not mapping:
        raise RuntimeError(f"No mapping entries found in '{mapping_path}'")

    script = translate_commands_text(commands_text, mapping)

    if debug:
        print("=== GENERATED SCRIPT ===")
        print(script)
        print("========================")

    env = build_exec_env(robot, delay=delay, on_step=on_step)

    # Выполнение: используем единое globals (env). Не передаём пустой locals — это ломало for/if scope.
    try:
        exec(script, env)
    except Exception as e:
        # добавим информацию о сгенерированном коде для удобства отладки
        raise RuntimeError(f"Error executing user script: {e}\n--- generated script ---\n{script}") from e

    return script


# # mapping_executor.py
# import yaml
# import time
# from typing import Dict, List, Any, Callable
#
# _ALLOWED_METHODS = {
#     'go_forward','go_backward','move_left','move_right',
#     'move_up_left','move_down_left','process_ore','process_path'
# }
#
# def _extract_mappings_recursive(obj: Any, allowed_methods: set, out: Dict[str, str]):
#     if isinstance(obj, dict):
#         for k, v in obj.items():
#             if isinstance(k, str) and isinstance(v, str):
#                 vv = v.strip()
#                 if vv in allowed_methods:
#                     out[k.strip()] = vv
#             if isinstance(v, (dict, list)):
#                 _extract_mappings_recursive(v, allowed_methods, out)
#             if isinstance(k, (dict, list)):
#                 _extract_mappings_recursive(k, allowed_methods, out)
#     elif isinstance(obj, list):
#         for item in obj:
#             _extract_mappings_recursive(item, allowed_methods, out)
#
# def load_mapping(path: str, allowed_methods: List[str] = None) -> Dict[str, str]:
#     if allowed_methods is None:
#         allowed = set(_ALLOWED_METHODS)
#     else:
#         allowed = set(allowed_methods)
#
#     with open(path, 'r', encoding='utf-8') as f:
#         data = yaml.safe_load(f)
#
#     if data is None:
#         return {}
#
#     mapping: Dict[str, str] = {}
#
#     if isinstance(data, dict):
#         simple_pairs = {}
#         for k, v in data.items():
#             if isinstance(k, str) and isinstance(v, str):
#                 simple_pairs[k.strip()] = v.strip()
#         for k, v in simple_pairs.items():
#             if v in allowed:
#                 mapping[k] = v
#
#     _extract_mappings_recursive(data, allowed, mapping)
#
#     if not mapping and isinstance(data, dict):
#         for k, v in data.items():
#             if isinstance(k, str) and isinstance(v, str):
#                 mapping[k.strip()] = v.strip()
#
#     return mapping
#
# def translate_commands_text(commands_text: str, mapping: Dict[str,str]) -> str:
#     out_lines: List[str] = []
#     lines = commands_text.splitlines()
#     for raw in lines:
#         stripped = raw.lstrip('\t ')
#         leading = raw[:len(raw)-len(stripped)]
#         key = stripped.strip()
#         if not key:
#             out_lines.append("")
#             continue
#         found = None
#         if key in mapping:
#             found = mapping[key]
#         else:
#             k_norm = key.lower().replace(" ", "").replace("_","")
#             for mk, mv in mapping.items():
#                 if mk.lower().replace(" ", "").replace("_","") == k_norm:
#                     found = mv
#                     break
#         if found:
#             out_lines.append(f"{leading}{found}()")
#             out_lines.append(f"{leading}__step__()")
#         else:
#             out_lines.append(raw)
#     return "\n".join(out_lines)
#
# def build_exec_env(robot, delay: float = 0.25, on_step: Callable[[], None] = None) -> dict:
#
#     env = {}
#     for name in _ALLOWED_METHODS:
#         if hasattr(robot, name):
#             method = getattr(robot, name)
#             env[name] = (lambda m: (lambda *a, **kw: m()))(method)
#
#     def __step__():
#         try:
#             if on_step:
#                 on_step()
#         finally:
#             if delay and delay > 0:
#                 time.sleep(delay)
#
#     env['__step__'] = __step__
#     env['robot'] = robot
#     env['range'] = range
#     return env
#
# def translate_and_exec(commands_text: str, mapping_path: str, robot, delay: float = 0.25, on_step: Callable[[], None] = None) -> None:
#     mapping = load_mapping(mapping_path)
#     if not mapping:
#         raise RuntimeError(f"No mapping entries found in '{mapping_path}'")
#     script = translate_commands_text(commands_text, mapping)
#     env = build_exec_env(robot, delay=delay, on_step=on_step)
#     exec(script, env, {})
