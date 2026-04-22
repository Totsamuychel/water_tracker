from dataclasses import dataclass
from typing import Optional

@dataclass
class WaterRecord:
    """Represents a single water intake record."""
    amount: int
    date: str
    id: Optional[int] = None
    timestamp: Optional[str] = None

@dataclass
class AppSettings:
    """Represents the application settings."""
    id: int = 1
    daily_goal: int = 2000
    reminder_interval: int = 60
    notification_type: str = "windows"  # options: "windows", "popup", "telegram", "both"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_enabled: bool = False
    goal_congratulated: str = ""  # format: 'YYYY-MM-DD'
