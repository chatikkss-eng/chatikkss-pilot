"""
Chatikkss Pilot — Система безопасности
Проверка, подтверждение и логирование всех действий.
"""
import os
import re
import logging
import datetime
from config import Config

logger = logging.getLogger("chatikkss_pilot.security")


class SecurityManager:
    """Менеджер безопасности — фильтрует и логирует все действия."""

    def __init__(self):
        self.log_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "logs"
        )
        os.makedirs(self.log_dir, exist_ok=True)

        self.log_file = os.path.join(self.log_dir, "actions.log")
        self._pending_actions = {}  # ID ожидающих подтверждения действий
        self._action_counter = 0
        self.confirm_all = False

        logger.info("SecurityManager инициализирован")

    def check_action(self, action: dict) -> dict:
        """
        Проверяет действие на безопасность.

        Returns:
            dict с ключами:
                - allowed: bool — разрешено ли вообще
                - needs_confirmation: bool — нужно ли подтверждение
                - risk_level: str — уровень риска
                - reason: str — причина блокировки (если заблокировано)
        """
        action_type = action.get("type", "none")
        params = action.get("params", {})

        # Действие "none" всегда разрешено
        if action_type == "none":
            return {
                "allowed": True,
                "needs_confirmation": False,
                "risk_level": "none",
                "reason": "",
            }

        # Проверяем на заблокированные паттерны
        block_check = self._check_blocked(action)
        if block_check:
            self._log_action(action, "BLOCKED", block_check)
            return {
                "allowed": False,
                "needs_confirmation": False,
                "risk_level": "critical",
                "reason": block_check,
            }

        # Определяем уровень риска
        risk = self._assess_risk(action)

        # Безопасные действия не требуют подтверждения (если не включено confirm_all)
        needs_confirmation = self.confirm_all or (action_type not in Config.SAFE_ACTIONS)

        return {
            "allowed": True,
            "needs_confirmation": needs_confirmation,
            "risk_level": risk,
            "reason": "",
        }

    def _check_blocked(self, action: dict) -> str:
        """Проверяет, не заблокировано ли действие."""
        action_type = action.get("type", "")
        params = action.get("params", {})

        # Проверяем команды на заблокированные паттерны
        if action_type == "run_command":
            command = params.get("command", "").lower()
            for pattern in Config.BLOCKED_PATTERNS:
                if pattern.lower() in command:
                    return (
                        f"🚫 Команда заблокирована: содержит запрещённый "
                        f"паттерн '{pattern}'"
                    )

        # Проверяем файловые операции
        if action_type == "open_file":
            path = params.get("path", "").lower()
            dangerous_paths = [
                "c:\\windows\\system32",
                "c:\\windows\\syswow64",
                "/etc/",
                "/usr/bin/",
            ]
            for dp in dangerous_paths:
                if path.startswith(dp):
                    return (
                        f"🚫 Доступ к системной директории заблокирован: {dp}"
                    )

        return ""

    def _assess_risk(self, action: dict) -> str:
        """Оценивает уровень риска действия."""
        action_type = action.get("type", "")

        high_risk = ["run_command"]
        medium_risk = [
            "open_app", "type_text", "press_key", "click",
            "open_file", "move_mouse"
        ]
        low_risk = [
            "open_url", "screenshot", "get_system_info",
            "scroll", "none"
        ]

        if action_type in high_risk:
            return "high"
        elif action_type in medium_risk:
            return "medium"
        elif action_type in low_risk:
            return "low"
        return "medium"

    def register_pending_action(self, action: dict) -> str:
        """
        Регистрирует действие, ожидающее подтверждения.

        Returns:
            str — ID действия
        """
        self._action_counter += 1
        action_id = f"action_{self._action_counter}"
        self._pending_actions[action_id] = {
            "action": action,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        logger.info(
            f"Действие зарегистрировано для подтверждения: {action_id}"
        )
        return action_id

    def confirm_action(self, action_id: str) -> dict:
        """Подтверждает действие и возвращает его."""
        if action_id not in self._pending_actions:
            return None

        pending = self._pending_actions.pop(action_id)
        action = pending["action"]
        self._log_action(action, "CONFIRMED")
        return action

    def deny_action(self, action_id: str) -> bool:
        """Отклоняет действие."""
        if action_id not in self._pending_actions:
            return False

        pending = self._pending_actions.pop(action_id)
        self._log_action(pending["action"], "DENIED")
        return True

    def _log_action(self, action: dict, status: str, reason: str = ""):
        """Записывает действие в журнал."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action_type = action.get("type", "unknown")
        description = action.get("description", "")
        params = action.get("params", {})

        log_entry = (
            f"[{timestamp}] [{status}] "
            f"Type: {action_type} | "
            f"Desc: {description} | "
            f"Params: {params}"
        )
        if reason:
            log_entry += f" | Reason: {reason}"

        log_entry += "\n"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Ошибка записи в журнал: {e}")

    def get_pending_actions(self) -> dict:
        """Возвращает все действия, ожидающие подтверждения."""
        return dict(self._pending_actions)
