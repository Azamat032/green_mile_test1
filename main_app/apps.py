# main_app/apps.py
from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MainAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_app'

    def ready(self):
        # Запуск Telegram бота при старте приложения
        if not getattr(settings, 'TESTING', False):  # Не запускать в тестах
            try:
                # Проверяем наличие необходимых настроек
                if not getattr(settings, 'TELEGRAM_BOT_TOKEN', None):
                    logger.warning(
                        "TELEGRAM_BOT_TOKEN not set, skipping bot startup")
                    return

                if not getattr(settings, 'TELEGRAM_ADMIN_PASSWORD', None):
                    logger.warning(
                        "TELEGRAM_ADMIN_PASSWORD not set, skipping bot startup")
                    return

                # Импортируем здесь, чтобы избежать циклических импортов
                from .telegram_bot import start_telegram_bot
                start_telegram_bot()
                logger.info("Telegram bot started successfully")

            except Exception as e:
                logger.error(f"Failed to start Telegram bot: {e}")
