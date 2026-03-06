"""
Chatikkss Pilot — Модуль голоса
Распознавание речи и синтез голоса (Text-to-Speech).
"""
import os
import asyncio
import logging
import tempfile
import threading

import speech_recognition as sr
import edge_tts

from config import Config

logger = logging.getLogger("chatikkss_pilot.voice")


class VoiceEngine:
    """Движок голосового ввода/вывода."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0

        self.tts_voice = Config.TTS_VOICE
        self.tts_rate = Config.TTS_RATE
        self.tts_volume = Config.TTS_VOLUME

        self.audio_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "static", "audio"
        )
        os.makedirs(self.audio_dir, exist_ok=True)

        logger.info("VoiceEngine инициализирован")

    def recognize_from_audio(self, audio_data: bytes) -> str:
        """
        Распознаёт речь из аудио-данных (WAV/WebM).

        Args:
            audio_data: Байты аудио-файла

        Returns:
            Распознанный текст или пустая строка
        """
        try:
            # Сохраняем временный файл
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            # Распознаём
            with sr.AudioFile(tmp_path) as source:
                audio = self.recognizer.record(source)

            text = self.recognizer.recognize_google(audio, language="ru-RU")
            logger.info(f"Распознанный текст: {text}")

            return text

        except sr.UnknownValueError:
            logger.warning("Речь не распознана")
            return ""
        except sr.RequestError as e:
            logger.error(f"Ошибка сервиса распознавания: {e}")
            return ""
        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}")
            return ""
        finally:
            # Удаляем временный файл
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

    def recognize_from_mic(self) -> str:
        """Слушает системный микрофон (через PyAudio) и распознает речь."""
        try:
            with sr.Microphone() as source:
                logger.info("Калибровка микрофона (0.5 сек)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Слушаю микрофон...")
                # Ограничиваем ожидание тишины и длину фразы
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
            
            logger.info("Распознаю речь...")
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            logger.info(f"Распознанный текст: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.warning("Таймаут ожидания речи")
        except sr.UnknownValueError:
            logger.warning("Речь не распознана")
        except Exception as e:
            logger.error(f"Ошибка микрофона: {e}")
        return ""

    async def _generate_tts(self, text: str, output_path: str):
        """Генерирует аудио-файл из текста (async)."""
        communicate = edge_tts.Communicate(
            text,
            voice=self.tts_voice,
            rate=self.tts_rate,
            volume=self.tts_volume,
        )
        await communicate.save(output_path)

    def synthesize(self, text: str) -> str:
        """
        Синтезирует речь из текста.

        Args:
            text: Текст для озвучки

        Returns:
            Путь к сгенерированному аудио-файлу (MP3)
        """
        if not text.strip():
            return ""

        # Убираем эмодзи и лишние символы для озвучки
        import re
        # Оставляем: буквы (включая русские), цифры, пробелы и базовую пунктуацию
        clean_text = re.sub(r'[^\w\s\.,!\?;:\-]', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        if not clean_text:
            return ""

        # Генерируем уникальное имя файла на основе очищенного текста
        import hashlib
        text_hash = hashlib.md5(clean_text.encode()).hexdigest()[:10]
        filename = f"tts_{text_hash}.mp3"
        filepath = os.path.join(self.audio_dir, filename)

        # Если уже есть кэш — возвращаем его
        if os.path.exists(filepath):
            return filepath

        try:
            # Запускаем async TTS
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._generate_tts(clean_text, filepath))
            loop.close()

            logger.info(f"TTS сгенерирован: {filename}")
            return filepath

        except Exception as e:
            logger.error(f"Ошибка синтеза речи: {e}")
            return ""

    def get_audio_url(self, filepath: str) -> str:
        """Конвертирует путь файла в URL для веб-интерфейса."""
        if not filepath:
            return ""
        filename = os.path.basename(filepath)
        return f"/static/audio/{filename}"

    @staticmethod
    def list_available_voices() -> list:
        """Возвращает список доступных голосов (async)."""
        async def _get():
            voices = await edge_tts.list_voices()
            return [
                v for v in voices
                if v["Locale"].startswith("ru")
            ]

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_get())
        loop.close()
        return result
