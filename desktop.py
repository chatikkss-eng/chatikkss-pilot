"""
Chatikkss Pilot — Десктопное приложение
Компактное окно в стиле J.A.R.V.I.S.
"""
import sys
import os
import threading
import logging
import webview

from app import app, socketio
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("chatikkss_pilot.desktop")


def start_server():
    """Запускает Flask-сервер в фоновом потоке."""
    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=False,
        allow_unsafe_werkzeug=True,
        use_reloader=False,
    )


if __name__ == "__main__":
    # Исправление кодировки для Windows терминалов
    if os.name == "nt":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    print(r"""
    ╔═══════════════════════════════════════╗
    ║       CHATIKKSS PILOT v1.0           ║
    ║    AI Desktop Assistant · JARVIS     ║
    ╚═══════════════════════════════════════╝
    """)

    # Запускаем Flask-сервер в отдельном потоке
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Компактное окно в стиле ассистента
    window = webview.create_window(
        title="Chatikkss Pilot",
        url=f"http://{Config.HOST}:{Config.PORT}",
        width=420,
        height=680,
        min_size=(380, 550),
        resizable=True,
        text_select=True,
        on_top=True,           # Всегда поверх окон
        confirm_close=False,
        background_color="#030810",
    )

    # Запускаем GUI
    webview.start(
        debug=False,
        gui="edgechromium",
        private_mode=False,
    )

    sys.exit(0)
