import time
import datetime
import threading
import requests
from plyer import notification
from database import DatabaseManager
from models import AppSettings

class NotificationService:
    """Service to handle background reminders via Windows, Telegram, or custom UI popups."""
    
    def __init__(self, db: DatabaseManager, show_popup_callback=None, show_balloon_callback=None):
        self.db = db
        self.show_popup_callback = show_popup_callback
        self.show_balloon_callback = show_balloon_callback
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.running = False
        
    def start(self):
        self.running = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        
    def _worker(self):
        while self.running:
            settings = self.db.load_settings()
            
            today = datetime.date.today().strftime("%Y-%m-%d")
            today_intake = self.db.get_today_intake(today)
            remaining = max(0, settings.daily_goal - today_intake)
            
            if remaining > 0:
                self._dispatch_reminder(settings, remaining, today_intake)
            elif today_intake >= settings.daily_goal and settings.goal_congratulated != today:
                self._dispatch_congratulation(settings, today_intake)
                settings.goal_congratulated = today
                self.db.save_settings(settings)
                
            # Sleep while checking settings dynamically
            elapsed_seconds = 0
            while self.running:
                # Reload settings inside the loop in case the interval was changed by the user!
                current_settings = self.db.load_settings()
                target_seconds = current_settings.reminder_interval * 60
                
                if elapsed_seconds >= target_seconds:
                    break
                    
                time.sleep(1)
                elapsed_seconds += 1
            
    def _dispatch_reminder(self, settings: AppSettings, remaining: int, today_intake: int):
        msg = f"Пора выпить воды! Осталось: {remaining} мл до цели"
        title = "💧 Напоминание о воде"
        
        ntype = settings.notification_type
        if ntype in ["windows", "both"]:
            try:
                # Use Windows balloon via tray if available, fallback to plyer
                if self.show_balloon_callback:
                    self.show_balloon_callback(title, msg)
                else:
                    notification.notify(title=title, message=msg, timeout=10)
            except Exception as e:
                print(f"Windows notification error: {e}")
                
        if ntype in ["telegram", "both"] or settings.telegram_enabled:
            if settings.telegram_bot_token and settings.telegram_chat_id:
                tele_msg = (f"💧 <b>Напоминание о воде</b>\n\n"
                            f"🎯 Осталось до цели: <b>{remaining} мл</b>\n"
                            f"📊 Выпито сегодня: <b>{today_intake} мл</b>\n"
                            f"⏰ {datetime.datetime.now().strftime('%H:%M')}")
                self.send_telegram(settings.telegram_bot_token, settings.telegram_chat_id, tele_msg)
                
        if ntype == "popup" and self.show_popup_callback:
            self.show_popup_callback(remaining, today_intake)
            
    def _dispatch_congratulation(self, settings: AppSettings, today_intake: int):
        title = "🎉 Цель достигнута!"
        msg = f"Поздравляем! Вы выпили {today_intake} мл воды сегодня!"
        
        ntype = settings.notification_type
        if ntype in ["windows", "both"]:
            try:
                if self.show_balloon_callback:
                    self.show_balloon_callback(title, msg)
                else:
                    notification.notify(title=title, message=msg, timeout=15)
            except Exception as e:
                print(f"Windows notification error: {e}")
                
        if ntype in ["telegram", "both"] or settings.telegram_enabled:
            if settings.telegram_bot_token and settings.telegram_chat_id:
                tele_msg = (f"🎉 <b>Поздравляем!</b>\n\n"
                            f"✅ Вы достигли дневной цели!\n"
                            f"🎯 Цель: <b>{settings.daily_goal} мл</b>\n"
                            f"💧 Выпито: <b>{today_intake} мл</b>\n"
                            f"⭐ Отличная работа!")
                self.send_telegram(settings.telegram_bot_token, settings.telegram_chat_id, tele_msg)
                
        if ntype == "popup" and self.show_popup_callback:
            self.show_popup_callback(0, today_intake)

    @staticmethod
    def send_telegram(token: str, chat_id: str, message: str) -> bool:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False
