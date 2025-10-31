# main_app/telegram_bot.py
import logging
from typing import Dict, Set
import requests
import time
from datetime import datetime
from threading import Thread
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot with authentication system"""

    def __init__(self, bot_token: str, admin_password: str):
        self.bot_token = bot_token
        self.admin_password = admin_password
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        # Store chat_ids of authorized users
        self.authorized_users: Set[str] = set()
        self.last_update_id = 0

    def start_polling(self):
        """Start polling for messages"""
        logger.info("Starting Telegram bot polling...")
        while True:
            try:
                self._process_updates()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(5)

    def _process_updates(self):
        """Process incoming updates"""
        url = f"{self.api_url}/getUpdates"
        params = {
            'offset': self.last_update_id + 1,
            'timeout': 30
        }

        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                for update in data.get('result', []):
                    self._handle_update(update)
                    self.last_update_id = update['update_id']

    def _handle_update(self, update):
        """Handle a single update"""
        if 'message' in update:
            message = update['message']
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()

            if text.startswith('/start'):
                self._handle_start_command(chat_id, text)
            elif chat_id in self.authorized_users:
                self._handle_authorized_message(chat_id, text)
            else:
                self._send_message(
                    chat_id, "⚠️ Вы не авторизованы. Используйте /start <пароль>")

    def _handle_start_command(self, chat_id: str, text: str):
        """Handle /start command with password"""
        parts = text.split()
        if len(parts) == 2:
            password = parts[1]
            if password == self.admin_password:
                self.authorized_users.add(chat_id)
                self._send_message(
                    chat_id,
                    "✅ Авторизация успешна! Теперь вы будете получать уведомления о заказах."
                )
                logger.info(f"User {chat_id} authorized successfully")
            else:
                self._send_message(chat_id, "❌ Неверный пароль")
        else:
            self._send_message(
                chat_id,
                "🔐 Для доступа к уведомлениям используйте:\n/start <пароль>"
            )

    def _handle_authorized_message(self, chat_id: str, text: str):
        """Handle messages from authorized users"""
        if text == '/status':
            self._send_message(
                chat_id, "🤖 Бот активен. Вы авторизованы для получения уведомлений.")
        elif text == '/help':
            self._send_help(chat_id)
        else:
            self._send_message(
                chat_id, "ℹ️ Используйте /help для списка команд")

    def _send_help(self, chat_id: str):
        """Send help message"""
        help_text = """
📋 Доступные команды:

/status - Проверить статус бота
/help - Показать эту справку

🤖 Этот бот отправляет уведомления о:
• Новых заказах сертификатов
• Заявках волонтеров
• Заявках организаторов
• Контактных формах
"""
        self._send_message(chat_id, help_text)

    def _send_message(self, chat_id: str, text: str, parse_mode: str = 'HTML'):
        """Send message to Telegram chat"""
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }

        try:
            response = requests.post(url, data=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def broadcast_to_authorized(self, message: str):
        """Send message to all authorized users"""
        for chat_id in self.authorized_users:
            self._send_message(chat_id, message)

    def get_authorized_users_count(self) -> int:
        """Get number of authorized users"""
        return len(self.authorized_users)


class TelegramNotifier:
    """Telegram notification service integrated with bot"""

    def __init__(self, telegram_bot: TelegramBot):
        self.bot = telegram_bot
        self.notification_types = {
            'order': '🛍️ НОВЫЙ ЗАКАЗ',
            'contact': '📞 КОНТАКТНАЯ ФОРМА',
            'volunteer': '👥 ЗАЯВКА ВОЛОНТЕРА',
            'organizer': '🏢 ЗАЯВКА ОРГАНИЗАТОРА'
        }

    def send_order_notification(self, order_data: Dict):
        """Send order notification to all authorized users"""
        try:
            message = self._format_order_message(order_data)
            return self.bot.broadcast_to_authorized(message)
        except Exception as e:
            logger.error(f"Failed to send order notification: {e}")
            return False

    def send_contact_notification(self, contact_data: Dict):
        """Send contact form notification to all authorized users"""
        try:
            message = self._format_contact_message(contact_data)
            return self.bot.broadcast_to_authorized(message)
        except Exception as e:
            logger.error(f"Failed to send contact notification: {e}")
            return False

    def send_volunteer_notification(self, volunteer_data: Dict):
        """Send volunteer application notification to all authorized users"""
        try:
            message = self._format_volunteer_message(volunteer_data)
            return self.bot.broadcast_to_authorized(message)
        except Exception as e:
            logger.error(f"Failed to send volunteer notification: {e}")
            return False

    def send_organizer_notification(self, organizer_data: Dict):
        """Send organizer application notification to all authorized users"""
        try:
            message = self._format_organizer_message(organizer_data)
            return self.bot.broadcast_to_authorized(message)
        except Exception as e:
            logger.error(f"Failed to send organizer notification: {e}")
            return False

    def _format_order_message(self, data: Dict) -> str:
        """Format order data into Telegram message"""
        message = f"""
<b>{self.notification_types['order']}</b>

📋 <b>Детали заказа:</b>
• ID: <code>{data.get('orderId', 'N/A')}</code>
• Дата: <code>{datetime.now().strftime('%d.%m.%Y %H:%M')}</code>

👤 <b>Информация о клиенте:</b>
• Имя: <code>{data.get('customerName', 'N/A')}</code>
• Email: <code>{data.get('customerEmail', 'N/A')}</code>
• Телефон: <code>{data.get('customerPhone', 'N/A') or 'Не указан'}</code>

🎯 <b>Детали сертификата:</b>
• Получатель: <code>{data.get('recipientName', 'N/A')}</code>
• Деревьев: <code>{data.get('treeCount', 'N/A')}</code>
• Дизайн: <code>{data.get('selectedDesign', 'N/A')}</code>

💰 <b>Платежная информация:</b>
• Сумма: <code>{data.get('totalAmount', 'N/A')} {data.get('currency', 'KZT')}</code>
• Статус: <code>{data.get('status', 'pending').upper()}</code>

🌱 <b>Экологический вклад:</b>
• Поглощение CO₂: ~<code>{int(data.get('treeCount', 0)) * 22} кг/год</code>
• Производство O₂: ~<code>{int(data.get('treeCount', 0)) * 16} кг/год</code>
"""
        return message.strip()

    def _format_contact_message(self, data: Dict) -> str:
        """Format contact form data into Telegram message"""
        message = f"""
<b>{self.notification_types['contact']}</b>

📋 <b>Детали:</b>
• Имя: <code>{data.get('name', 'N/A')}</code>
• Email: <code>{data.get('email', 'N/A')}</code>
• Тема: <code>{data.get('subject', 'Без темы')}</code>
• Время: <code>{data.get('submitted_at', datetime.now().strftime('%d.%m.%Y %H:%M'))}</code>

💬 <b>Сообщение:</b>
<code>{data.get('message', 'N/A')[:300]}{'...' if len(data.get('message', '')) > 300 else ''}</code>
"""
        return message.strip()

    def _format_volunteer_message(self, data: Dict) -> str:
        """Format volunteer application into Telegram message"""
        dates = data.get('dates', '').replace(',', ', ')
        message = f"""
<b>{self.notification_types['volunteer']}</b>

👤 <b>Информация о волонтере:</b>
• Имя: <code>{data.get('name', 'N/A')}</code>
• Email: <code>{data.get('email', 'N/A')}</code>
• Телефон: <code>{data.get('phone', '—')}</code>
• Регион: <code>{data.get('region', 'N/A')}</code>
• Даты: <code>{dates or '—'}</code>

📝 <b>Опыт:</b>
<code>{data.get('experience', '—')[:200]}{'...' if len(data.get('experience', '')) > 200 else ''}</code>

⏰ <b>Отправлено:</b> <code>{data.get('submitted', datetime.now().strftime('%d.%m.%Y %H:%M'))}</code>
"""
        return message.strip()

    def _format_organizer_message(self, data: Dict) -> str:
        """Format organizer application into Telegram message"""
        message = f"""
<b>{self.notification_types['organizer']}</b>

👤 <b>Информация об организаторе:</b>
• Имя: <code>{data.get('name', 'N/A')}</code>
• Email: <code>{data.get('email', 'N/A')}</code>
• Телефон: <code>{data.get('phone', 'N/A')}</code>
• Организация: <code>{data.get('organization', '—')}</code>
• Регион: <code>{data.get('region', 'N/A')}</code>

📋 <b>План мероприятий:</b>
<code>{data.get('plan', '—')[:300]}{'...' if len(data.get('plan', '')) > 300 else ''}</code>

⏰ <b>Отправлено:</b> <code>{data.get('submitted', datetime.now().strftime('%d.%m.%Y %H:%M'))}</code>
"""
        return message.strip()


# Глобальные переменные для бота и нотификатора
telegram_bot = None
telegram_notifier = None


def start_telegram_bot():
    """Start Telegram bot in background thread"""
    global telegram_bot, telegram_notifier

    telegram_bot = TelegramBot(
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        admin_password=settings.TELEGRAM_ADMIN_PASSWORD
    )

    telegram_notifier = TelegramNotifier(telegram_bot)

    # Запуск бота в отдельном потоке
    bot_thread = Thread(target=telegram_bot.start_polling, daemon=True)
    bot_thread.start()
    logger.info("Telegram bot started successfully")


def get_telegram_notifier():
    """Get the global telegram notifier instance"""
    global telegram_notifier
    return telegram_notifier
