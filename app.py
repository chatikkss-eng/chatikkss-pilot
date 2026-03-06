"""
Chatikkss Pilot — Главный сервер приложения
Flask + SocketIO для реал-тайм взаимодействия.
"""
import os
import sys
import json
import logging
import tempfile
import base64

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

from config import Config
from core.mistral_client import MistralClient
from core.actions import ActionExecutor
from core.security import SecurityManager
from core.voice import VoiceEngine

# ─── Настройка логирования ───────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("chatikkss_pilot")

# ─── Инициализация Flask ─────────────────────────────────────────────

if getattr(sys, "frozen", False):
    # Путь при запуске из .exe
    base_dir = sys._MEIPASS
    template_folder = os.path.join(base_dir, "templates")
    static_folder = os.path.join(base_dir, "static")
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    # Обычный запуск
    app = Flask(__name__)

app.config["SECRET_KEY"] = Config.SECRET_KEY

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
logger.info("SocketIO инициализирован (режим: threading)")

# ─── Инициализация компонентов ───────────────────────────────────────

mistral_client = None
action_executor = ActionExecutor()
security_manager = SecurityManager()
voice_engine = VoiceEngine()


def init_mistral():
    """Инициализация клиента Mistral (ленивая загрузка)."""
    global mistral_client
    if mistral_client is None:
        try:
            mistral_client = MistralClient()
            logger.info("Mistral клиент успешно инициализирован")
        except ValueError as e:
            logger.error(f"Ошибка инициализации Mistral: {e}")
            return False
    return True


# ─── Маршруты ────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Главная страница."""
    return render_template("index.html")


@app.route("/static/audio/<path:filename>")
def serve_audio(filename):
    """Отдаёт аудио-файлы TTS."""
    audio_dir = os.path.join(app.root_path, "static", "audio")
    return send_from_directory(audio_dir, filename)


# ─── WebSocket события ───────────────────────────────────────────────

@socketio.on("connect")
def handle_connect():
    """Клиент подключился."""
    logger.info("Клиент подключился к WebSocket")
    emit("status", {"message": "Подключено к Chatikkss Pilot!", "type": "success"})


@socketio.on("disconnect")
def handle_disconnect():
    """Клиент отключился."""
    logger.info("Клиент отключился")


@socketio.on("send_message")
def handle_message(data):
    """Обработка текстового сообщения от пользователя."""
    message = data.get("message", "").strip()
    if not message:
        return

    logger.info(f"Получено сообщение: {message}")

    # Инициализируем Mistral при первом запросе
    if not init_mistral():
        emit("response", {
            "text": "❌ API ключ Mistral не настроен! Добавь его в файл .env",
            "actions": [],
            "error": True,
        })
        return

    # Отправляем запрос в Mistral
    emit("thinking", {"status": True})

    try:
        result = mistral_client.process_message(message)
    except Exception as e:
        logger.error(f"Ошибка Mistral: {e}")
        emit("thinking", {"status": False})
        emit("response", {
            "text": f"❌ Ошибка ИИ: {str(e)}",
            "actions": [],
            "error": True,
        })
        return

    emit("thinking", {"status": False})

    response_text = result.get("response", "")
    actions = result.get("actions", [])

    # Проверяем действия через систему безопасности
    processed_actions = []
    for action in actions:
        if action.get("type") == "none":
            continue

        security_check = security_manager.check_action(action)

        if not security_check["allowed"]:
            # Действие заблокировано
            processed_actions.append({
                **action,
                "status": "blocked",
                "reason": security_check["reason"],
            })
            continue

        if security_check["needs_confirmation"]:
            # Нужно подтверждение
            action_id = security_manager.register_pending_action(action)
            processed_actions.append({
                **action,
                "status": "pending",
                "action_id": action_id,
                "risk_level": security_check["risk_level"],
            })
        else:
            # Безопасное действие — выполняем сразу
            exec_result = action_executor.execute(action)
            processed_actions.append({
                **action,
                "status": "executed",
                "result": exec_result,
            })

    # Генерируем голосовой ответ
    audio_url = ""
    if response_text:
        audio_path = voice_engine.synthesize(response_text)
        audio_url = voice_engine.get_audio_url(audio_path)

    emit("response", {
        "text": response_text,
        "actions": processed_actions,
        "audio_url": audio_url,
        "error": False,
    })


@socketio.on("confirm_action")
def handle_confirm(data):
    """Подтверждение действия пользователем."""
    action_id = data.get("action_id", "")

    action = security_manager.confirm_action(action_id)
    if not action:
        emit("action_result", {
            "action_id": action_id,
            "success": False,
            "message": "Действие не найдено или уже выполнено",
        })
        return

    # Выполняем подтверждённое действие
    result = action_executor.execute(action)

    emit("action_result", {
        "action_id": action_id,
        "success": result.get("success", False),
        "message": result.get("message", ""),
        "data": result.get("data"),
    })


@socketio.on("deny_action")
def handle_deny(data):
    """Отклонение действия пользователем."""
    action_id = data.get("action_id", "")

    success = security_manager.deny_action(action_id)
    emit("action_result", {
        "action_id": action_id,
        "success": True,
        "message": "Действие отклонено" if success else "Действие не найдено",
        "denied": True,
    })


@socketio.on("start_voice")
def handle_start_voice():
    """Слушает звук с системного микрофона и возвращает текст клиенту."""
    emit("status", {"message": "Говорите...", "type": "info"})
    
    def listen_task():
        text = voice_engine.recognize_from_mic()
        if text:
            socketio.emit("voice_recognized", {"text": text})
        else:
            socketio.emit("status", {"message": "Не удалось распознать речь", "type": "warning"})
            socketio.emit("voice_stop")

    # Запускаем в фоне, чтобы не блокировать WebSocket
    import threading
    threading.Thread(target=listen_task).start()


@socketio.on("clear_history")
def handle_clear():
    """Очистка истории диалога."""
    if mistral_client:
        mistral_client.clear_history()


@socketio.on("set_name")
def handle_set_name(data):
    """Устанавливает имя пользователя в контексте Mistral."""
    name = data.get("name", "").strip()
    if not name:
        return

    if init_mistral():
        # Обновляем системный промпт с именем
        name_addition = f"\n\nИмя пользователя: {name}. Обращайся к нему по имени."
        base_prompt = Config.SYSTEM_PROMPT
        mistral_client.conversation_history[0] = {
            "role": "system",
            "content": base_prompt + name_addition,
        }
        logger.info(f"Имя пользователя установлено: {name}")


@socketio.on("replay_message")
def handle_replay(data):
    """Восстановление контекста при загрузке истории чата."""
    role = data.get("role", "")
    content = data.get("content", "")
    if not role or not content:
        return

    if init_mistral():
        mistral_client.conversation_history.append({
            "role": role,
            "content": content,
        })


@socketio.on("update_settings")
def handle_update_settings(data):
    """Синхронизация клиентских настроек с сервером."""
    if "confirm_all" in data:
        security_manager.confirm_all = bool(data["confirm_all"])
        logger.info(f"Настройки безопасности обновлены. Подтверждать всё: {security_manager.confirm_all}")

    if "voice" in data:
        voice_engine.tts_voice = str(data["voice"])
        logger.info(f"Голос изменён на: {voice_engine.tts_voice}")


# ─── Запуск ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(r"""
   ______ __          __  _ __    __             ____  _ __      __ 
  / ____// /_  ____ _/ /_(_) /__ / /__ _____    / __ \(_) /___  / /_
 / /    / __ \/ __ `/ __/ / //_// //_// ___/   / /_/ / / / __ \/ __/
/ /___ / / / / /_/ / /_/ / ,<  / ,<  (__  )   / ____/ / / /_/ / /_  
\____//_/ /_/\__,_/\__/_/_/|_|/_/|_|/____/   /_/   /_/_/\____/\__/  
                                                                     
    🚀 Chatikkss Pilot — Голосовой ассистент для управления ПК
    📡 Сервер запущен на http://{host}:{port}
    """.format(host=Config.HOST, port=Config.PORT))

    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True,
    )
