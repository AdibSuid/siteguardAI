"""
Telegram Notification Module
Sends alerts to Telegram channels when violations are detected.
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
import json
from loguru import logger


class TelegramNotifier:
    """
    Telegram notification service for sending violation alerts.
    """

    def __init__(self, bot_token: str, channel_id: str):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token from @BotFather
            channel_id: Telegram channel ID (e.g., @channelname or -1001234567890)
        """
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_violation_alert(
        self,
        violations: List[Dict],
        location: str = "Industrial Site",
        site_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Send violation alert to Telegram channel.

        Args:
            violations: List of violation dictionaries
            location: Location where violation occurred
            site_id: Site identifier
            timestamp: Timestamp of violation

        Returns:
            bool: True if message sent successfully
        """
        if not violations:
            return False

        if not timestamp:
            timestamp = datetime.now().isoformat()

        # Create message
        message = self._format_violation_message(violations, location, site_id, timestamp)

        try:
            # Send message to channel
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.channel_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                },
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Telegram alert sent for {len(violations)} violations")
                return True
            else:
                logger.error(f"❌ Failed to send Telegram alert: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending Telegram alert: {e}")
            return False

    def _format_violation_message(
        self,
        violations: List[Dict],
        location: str,
        site_id: Optional[str],
        timestamp: str
    ) -> str:
        """
        Format violation details into Telegram message.

        Args:
            violations: List of violation dictionaries
            location: Location name
            site_id: Site identifier
            timestamp: Timestamp

        Returns:
            str: Formatted message
        """
        # Header
        message = "🚨 *SAFETY VIOLATION ALERT*\n\n"

        # Location and time
        message += f"📍 *Location:* {location}\n"
        if site_id:
            message += f"🏭 *Site ID:* {site_id}\n"
        message += f"🕐 *Time:* {datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Violation details
        message += f"⚠️ *Violations Detected: {len(violations)}*\n\n"

        for i, violation in enumerate(violations, 1):
            vtype = violation.get('type', 'unknown').replace('_', ' ').title()
            severity = violation.get('severity', 'medium').upper()
            description = violation.get('description', 'Safety violation detected')
            osha_standard = violation.get('osha_standard', '')

            message += f"{i}. *{vtype}*\n"
            message += f"   🔴 Severity: {severity}\n"
            message += f"   📝 Description: {description}\n"
            if osha_standard:
                message += f"   📋 OSHA Standard: {osha_standard}\n"
            message += "\n"

        # Footer
        message += "🔍 *SiteGuard AI Monitoring System*\n"
        message += "⚡ Immediate action required!"

        return message

    def test_connection(self) -> bool:
        """
        Test Telegram bot connection.

        Returns:
            bool: True if connection successful
        """
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"✅ Telegram bot connected: @{bot_info['result']['username']}")
                return True
            else:
                logger.error(f"❌ Telegram bot connection failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error testing Telegram connection: {e}")
            return False


def create_telegram_notifier(config) -> Optional[TelegramNotifier]:
    """
    Create Telegram notifier from configuration.

    Args:
        config: Configuration object

    Returns:
        TelegramNotifier instance or None if not configured
    """
    bot_token = config.get('telegram.bot_token', '')
    channel_id = config.get('telegram.channel_id', '')
    enabled = config.get('telegram.enabled', False)

    if not enabled or not bot_token or not channel_id:
        logger.info("📱 Telegram notifications disabled or not configured")
        return None

    notifier = TelegramNotifier(bot_token, channel_id)

    # Test connection
    if notifier.test_connection():
        logger.info("📱 Telegram notifier initialized successfully")
        return notifier
    else:
        logger.error("❌ Failed to initialize Telegram notifier")
        return None