"""
Chatikkss Pilot — Клиент Mistral API
Обработка запросов к Mistral Large для понимания команд пользователя.
"""
import json
import logging
from mistralai import Mistral
from config import Config

logger = logging.getLogger("chatikkss_pilot.mistral")


class MistralClient:
    """Клиент для работы с Mistral Large API."""

    def __init__(self):
        if not Config.MISTRAL_API_KEY:
            raise ValueError(
                "MISTRAL_API_KEY не установлен! Добавь его в файл .env"
            )

        self.client = Mistral(api_key=Config.MISTRAL_API_KEY)
        self.model = Config.MISTRAL_MODEL
        self.conversation_history = []

        # Добавляем системный промпт
        self.conversation_history.append({
            "role": "system",
            "content": Config.SYSTEM_PROMPT
        })

        logger.info(f"MistralClient инициализирован. Модель: {self.model}")

    def process_message(self, user_message: str) -> dict:
        """
        Отправляет сообщение пользователя в Mistral и получает ответ.

        Args:
            user_message: Текст сообщения пользователя

        Returns:
            dict с ключами 'response' и 'actions'
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            assistant_message = response.choices[0].message.content
            logger.info(f"Ответ Mistral: {assistant_message[:200]}...")

            # Сохраняем ответ в историю
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            # Ограничиваем длину истории (системный промпт + 20 последних сообщений)
            if len(self.conversation_history) > 21:
                self.conversation_history = (
                    [self.conversation_history[0]]
                    + self.conversation_history[-20:]
                )

            # Парсим JSON-ответ
            parsed = self._parse_response(assistant_message)
            return parsed

        except Exception as e:
            logger.error(f"Ошибка при обращении к Mistral API: {e}")
            return {
                "response": f"Произошла ошибка при обращении к ИИ: {str(e)}",
                "actions": []
            }

    def _parse_response(self, raw_response: str) -> dict:
        """Парсит JSON-ответ от Mistral."""
        try:
            data = json.loads(raw_response)

            # Проверяем наличие необходимых полей
            if "response" not in data:
                data["response"] = "Готово!"
            if "actions" not in data:
                data["actions"] = []

            # Валидируем каждое действие
            validated_actions = []
            for action in data["actions"]:
                if "type" in action:
                    if "params" not in action:
                        action["params"] = {}
                    if "description" not in action:
                        action["description"] = f"Действие: {action['type']}"
                    if "risk_level" not in action:
                        action["risk_level"] = "medium"
                    validated_actions.append(action)

            data["actions"] = validated_actions
            return data

        except json.JSONDecodeError:
            logger.warning(f"Не удалось распарсить JSON: {raw_response[:200]}")
            return {
                "response": raw_response,
                "actions": []
            }

    def clear_history(self):
        """Очищает историю диалога, оставляя системный промпт."""
        self.conversation_history = [self.conversation_history[0]]
        logger.info("История диалога очищена")
