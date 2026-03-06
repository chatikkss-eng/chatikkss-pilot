"""
Chatikkss Pilot — Конфигурация
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Основные настройки приложения."""

    # Mistral API
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_MODEL = "mistral-large-latest"

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "chatikkss-pilot-secret-key-2026")
    HOST = "127.0.0.1"
    PORT = 5000
    DEBUG = True

    # Голосовые настройки
    TTS_VOICE = "ru-RU-DmitryNeural"  # Мужской русский голос Microsoft
    TTS_RATE = "+0%"
    TTS_VOLUME = "+0%"

    # Безопасность
    LOG_FILE = "logs/actions.log"
    MAX_LOG_SIZE_MB = 50

    # Действия, которые НЕ требуют подтверждения (безопасные)
    SAFE_ACTIONS = [
        "get_time",
        "get_date",
        "get_system_info",
        "get_battery",
        "get_running_processes",
        "screenshot",
        "open_app",
        "open_url",
        "open_file",
        "scroll",
    ]

    # Полностью запрещённые команды / паттерны
    BLOCKED_PATTERNS = [
        "format c:",
        "format d:",
        "rd /s /q c:",
        "del /f /s /q c:\\windows",
        "del /f /s /q c:\\users",
        "rm -rf /",
        "rm -rf /*",
        "shutdown /s /t 0",
        "reg delete",
        "bcdedit",
        "diskpart",
        "cipher /w:",
    ]

    # Системный промпт для Mistral
    SYSTEM_PROMPT = """Ты — Chatikkss Pilot, умный и безопасный голосовой ассистент для управления компьютером.

Твои возможности:
1. Запускать программы и приложения
2. Набирать текст в любых программах
3. Управлять мышкой и клавиатурой
4. Открывать файлы и папки
5. Искать информацию в интернете
6. Управлять системными настройками
7. Делать скриншоты
8. Получать информацию о системе

ПРАВИЛА БЕЗОПАСНОСТИ:
- НИКОГДА не выполняй деструктивные команды (удаление системных файлов, форматирование дисков)
- Всегда предупреждай пользователя о потенциально опасных действиях
- Если не уверен — лучше спроси

Когда пользователь просит выполнить действие, ты должен ответить в формате JSON:
{
    "response": "Текстовый ответ пользователю",
    "actions": [
        {
            "type": "тип_действия",
            "params": { "параметры": "значение" },
            "description": "Описание действия для подтверждения",
            "risk_level": "low/medium/high"
        }
    ]
}

Типы действий (type):
- "open_app" — открыть программу. params: {"name": "имя_программы"}
- "open_url" — открыть URL. params: {"url": "ссылка"}
- "type_text" — набрать текст. params: {"text": "текст"}
- "press_key" — нажать клавишу. params: {"key": "клавиша"} (например: "enter", "ctrl+c", "alt+tab")
- "click" — клик мышкой. params: {"x": 100, "y": 200, "button": "left"}
- "move_mouse" — переместить мышку. params: {"x": 100, "y": 200}
- "screenshot" — сделать скриншот. params: {}
- "run_command" — выполнить команду. params: {"command": "команда"}
- "open_file" — открыть файл. params: {"path": "путь_к_файлу"}
- "get_system_info" — информация о системе. params: {}
- "scroll" — прокрутка. params: {"direction": "up/down", "amount": 3}
- "none" — никаких действий, просто ответ. params: {}

Если пользователь просто разговаривает и не просит выполнить действие, используй type "none".
Отвечай на русском языке, дружелюбно и кратко."""
