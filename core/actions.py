"""
Chatikkss Pilot — Модуль действий
Выполнение действий на компьютере пользователя.
"""
import os
import subprocess
import logging
import datetime
import webbrowser
import platform
import shutil

import pyautogui
import psutil

logger = logging.getLogger("chatikkss_pilot.actions")

# Отключаем failsafe pyautogui (пользователь может быстро двинуть мышь в угол для остановки)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


class ActionExecutor:
    """Выполняет действия на компьютере."""

    def __init__(self):
        self.screenshots_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "screenshots"
        )
        os.makedirs(self.screenshots_dir, exist_ok=True)
        logger.info("ActionExecutor инициализирован")

    def execute(self, action: dict) -> dict:
        """
        Выполняет одно действие.

        Args:
            action: Словарь с type, params, description

        Returns:
            dict с результатом выполнения
        """
        action_type = action.get("type", "none")
        params = action.get("params", {})

        handlers = {
            "none": self._action_none,
            "open_app": self._action_open_app,
            "open_url": self._action_open_url,
            "type_text": self._action_type_text,
            "press_key": self._action_press_key,
            "click": self._action_click,
            "move_mouse": self._action_move_mouse,
            "screenshot": self._action_screenshot,
            "run_command": self._action_run_command,
            "open_file": self._action_open_file,
            "get_system_info": self._action_system_info,
            "scroll": self._action_scroll,
        }

        handler = handlers.get(action_type)
        if not handler:
            return {
                "success": False,
                "message": f"Неизвестный тип действия: {action_type}"
            }

        try:
            result = handler(params)
            logger.info(
                f"Действие '{action_type}' выполнено: {result.get('message', 'OK')}"
            )
            return result
        except Exception as e:
            logger.error(f"Ошибка при выполнении '{action_type}': {e}")
            return {
                "success": False,
                "message": f"Ошибка: {str(e)}"
            }

    # ─── Обработчики действий ────────────────────────────────────────

    def _action_none(self, params: dict) -> dict:
        """Нет действий — просто ответ."""
        return {"success": True, "message": "Нет действий для выполнения"}

    def _action_open_app(self, params: dict) -> dict:
        """Открывает приложение."""
        app_name = params.get("name", "")
        if not app_name:
            return {"success": False, "message": "Не указано имя приложения"}

        # Маппинг популярных приложений
        app_map = {
            "блокнот": "notepad.exe",
            "notepad": "notepad.exe",
            "калькулятор": "calc.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "пэйнт": "mspaint.exe",
            "проводник": "explorer.exe",
            "explorer": "explorer.exe",
            "командная строка": "cmd.exe",
            "cmd": "cmd.exe",
            "терминал": "wt.exe",
            "terminal": "wt.exe",
            "powershell": "powershell.exe",
            "диспетчер задач": "taskmgr.exe",
            "task manager": "taskmgr.exe",
            "настройки": "ms-settings:",
            "settings": "ms-settings:",
            "chrome": "chrome.exe",
            "хром": "chrome.exe",
            "firefox": "firefox.exe",
            "фаерфокс": "firefox.exe",
            "vscode": "code",
            "код": "code",
            "visual studio code": "code",
            "telegram": "telegram.exe",
            "телеграм": "telegram.exe",
            "discord": "discord.exe",
            "дискорд": "discord.exe",
            "spotify": "spotify.exe",
            "спотифай": "spotify.exe",
        }

        executable = app_map.get(app_name.lower(), app_name)

        try:
            if executable.startswith("ms-"):
                os.system(f"start {executable}")
            else:
                subprocess.Popen(
                    executable,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return {
                "success": True,
                "message": f"Приложение '{app_name}' запущено"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Приложение '{app_name}' не найдено"
            }

    def _action_open_url(self, params: dict) -> dict:
        """Открывает URL в браузере."""
        url = params.get("url", "")
        if not url:
            return {"success": False, "message": "URL не указан"}

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        webbrowser.open(url)
        return {"success": True, "message": f"Открыт URL: {url}"}

    def _action_type_text(self, params: dict) -> dict:
        """Набирает текст с клавиатуры."""
        text = params.get("text", "")
        if not text:
            return {"success": False, "message": "Текст не указан"}

        # Используем pyperclip + Ctrl+V для поддержки кириллицы
        import pyperclip
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")

        return {"success": True, "message": f"Набран текст: {text[:50]}..."}

    def _action_press_key(self, params: dict) -> dict:
        """Нажимает клавишу или комбинацию клавиш."""
        key = params.get("key", "")
        if not key:
            return {"success": False, "message": "Клавиша не указана"}

        # Поддержка комбинаций типа "ctrl+c"
        keys = [k.strip() for k in key.lower().split("+")]

        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)

        return {"success": True, "message": f"Нажата клавиша: {key}"}

    def _action_click(self, params: dict) -> dict:
        """Клик мышкой."""
        x = params.get("x")
        y = params.get("y")
        button = params.get("button", "left")

        if x is not None and y is not None:
            pyautogui.click(x=int(x), y=int(y), button=button)
            return {
                "success": True,
                "message": f"Клик ({button}) по ({x}, {y})"
            }
        else:
            pyautogui.click(button=button)
            return {
                "success": True,
                "message": f"Клик ({button}) в текущей позиции"
            }

    def _action_move_mouse(self, params: dict) -> dict:
        """Перемещает курсор мыши."""
        x = params.get("x", 0)
        y = params.get("y", 0)

        pyautogui.moveTo(int(x), int(y), duration=0.3)
        return {"success": True, "message": f"Мышка перемещена в ({x}, {y})"}

    def _action_screenshot(self, params: dict) -> dict:
        """Делает скриншот."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)

        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)

        return {
            "success": True,
            "message": f"Скриншот сохранён: {filename}",
            "data": {"path": filepath}
        }

    def _action_run_command(self, params: dict) -> dict:
        """Выполняет команду в терминале."""
        command = params.get("command", "")
        if not command:
            return {"success": False, "message": "Команда не указана"}

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )

            output = result.stdout.strip() if result.stdout else ""
            error = result.stderr.strip() if result.stderr else ""

            return {
                "success": result.returncode == 0,
                "message": f"Команда выполнена (код: {result.returncode})",
                "data": {
                    "stdout": output[:2000],
                    "stderr": error[:500],
                    "return_code": result.returncode,
                },
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Команда превысила время ожидания (30 сек)"
            }

    def _action_open_file(self, params: dict) -> dict:
        """Открывает файл стандартной программой."""
        path = params.get("path", "")
        if not path:
            return {"success": False, "message": "Путь не указан"}

        if not os.path.exists(path):
            return {"success": False, "message": f"Файл не найден: {path}"}

        os.startfile(path)
        return {"success": True, "message": f"Файл открыт: {path}"}

    def _action_system_info(self, params: dict) -> dict:
        """Возвращает информацию о системе."""
        info = {
            "os": f"{platform.system()} {platform.release()}",
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_total_gb": round(
                psutil.virtual_memory().total / (1024**3), 2
            ),
            "ram_used_percent": psutil.virtual_memory().percent,
        }

        # Информация о дисках
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_percent": round(usage.percent, 1),
                })
            except PermissionError:
                pass

        info["disks"] = disks

        # Батарея (если есть)
        battery = psutil.sensors_battery()
        if battery:
            info["battery_percent"] = battery.percent
            info["battery_plugged"] = battery.power_plugged

        return {
            "success": True,
            "message": "Информация о системе получена",
            "data": info,
        }

    def _action_scroll(self, params: dict) -> dict:
        """Прокрутка колёсиком мыши."""
        direction = params.get("direction", "down")
        amount = int(params.get("amount", 3))

        clicks = amount if direction == "up" else -amount
        pyautogui.scroll(clicks)

        return {
            "success": True,
            "message": f"Прокрутка {direction} на {amount}"
        }
