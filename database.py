import sqlite3
import os
import threading
from typing import List, Dict, Tuple, Optional
from models import WaterRecord, AppSettings
import datetime

class DatabaseManager:
    """Manages SQLite database connections and queries."""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'data', 'water_tracker.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.local = threading.local()
        self.init_database()
        
    def _get_conn(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path)
        return self.local.conn
        
    def init_database(self):
        """Initialize schema and run migrations."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS water_intake (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                daily_goal INTEGER DEFAULT 2000,
                reminder_interval INTEGER DEFAULT 60,
                notifications_enabled INTEGER DEFAULT 1,
                telegram_bot_token TEXT DEFAULT '',
                telegram_chat_id TEXT DEFAULT '',
                telegram_enabled INTEGER DEFAULT 0
            )
        ''')
        
        # Migrations: add new columns if they don't exist
        try:
            cursor.execute("ALTER TABLE settings ADD COLUMN notification_type TEXT DEFAULT 'windows'")
        except sqlite3.OperationalError:
            pass  # column exists
            
        try:
            cursor.execute("ALTER TABLE settings ADD COLUMN goal_congratulated TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
            
        # Ensure default settings exist
        cursor.execute('SELECT COUNT(*) FROM settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO settings 
                (daily_goal, reminder_interval, notifications_enabled, telegram_bot_token, telegram_chat_id, telegram_enabled, notification_type, goal_congratulated) 
                VALUES (2000, 60, 1, '', '', 0, 'windows', '')
            ''')
            
        conn.commit()

    def load_settings(self) -> AppSettings:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT daily_goal, reminder_interval, notification_type, 
                   telegram_bot_token, telegram_chat_id, telegram_enabled, goal_congratulated
            FROM settings WHERE id = 1
        ''')
        row = cursor.fetchone()
        if row:
            notif_type = row[2] if row[2] else "windows"
            return AppSettings(
                daily_goal=row[0],
                reminder_interval=row[1],
                notification_type=notif_type,
                telegram_bot_token=row[3] or "",
                telegram_chat_id=row[4] or "",
                telegram_enabled=bool(row[5]),
                goal_congratulated=row[6] or ""
            )
        return AppSettings()

    def save_settings(self, settings: AppSettings):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE settings SET 
            daily_goal = ?, 
            reminder_interval = ?, 
            notification_type = ?,
            telegram_bot_token = ?,
            telegram_chat_id = ?,
            telegram_enabled = ?,
            goal_congratulated = ?
            WHERE id = 1
        ''', (settings.daily_goal, settings.reminder_interval, settings.notification_type,
              settings.telegram_bot_token, settings.telegram_chat_id, int(settings.telegram_enabled),
              settings.goal_congratulated))
        conn.commit()
        
    def add_water(self, amount: int, date: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO water_intake (date, amount) VALUES (?, ?)', (date, amount))
        conn.commit()
        
    def update_record(self, record_id: int, amount: int):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE water_intake SET amount = ? WHERE id = ?', (amount, record_id))
        conn.commit()
        
    def delete_record(self, record_id: int):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM water_intake WHERE id = ?', (record_id,))
        conn.commit()
        
    def clear_history(self, date: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM water_intake WHERE date = ?', (date,))
        conn.commit()
        
    def get_today_intake(self, date: str) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(amount) FROM water_intake WHERE date = ?', (date,))
        res = cursor.fetchone()[0]
        return res if res else 0
        
    def get_history(self, date: str) -> List[WaterRecord]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, date, amount, timestamp FROM water_intake 
            WHERE date = ? ORDER BY timestamp DESC
        ''', (date,))
        records = []
        for row in cursor.fetchall():
            records.append(WaterRecord(id=row[0], date=row[1], amount=row[2], timestamp=row[3]))
        return records

    def get_month_data(self, year: int, month: int) -> Dict[str, int]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, SUM(amount) FROM water_intake 
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY date
        ''', (str(year), f"{month:02d}"))
        return {row[0]: row[1] for row in cursor.fetchall()}

    def get_week_data(self, days: int = 7) -> List[Tuple[str, int]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT date, SUM(amount) FROM water_intake 
            WHERE date >= date('now', '-{days-1} days')
            GROUP BY date ORDER BY date ASC
        ''')
        return cursor.fetchall()

    def get_streak(self) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, SUM(amount) FROM water_intake 
            GROUP BY date ORDER BY date DESC
        ''')
        rows = cursor.fetchall()
        
        streak = 0
        today = datetime.date.today()
        
        if not rows:
            return 0
            
        first_date_str = rows[0][0]
        first_date = datetime.datetime.strptime(first_date_str, '%Y-%m-%d').date()
        
        if (today - first_date).days > 1:
            return 0
            
        current_check_date = first_date
        for row in rows:
            date_str, amount = row
            row_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            if row_date == current_check_date and amount > 0:
                streak += 1
                current_check_date -= datetime.timedelta(days=1)
            elif row_date < current_check_date:
                break
        return streak

    def get_best_day(self) -> Tuple[Optional[str], int]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, SUM(amount) as total FROM water_intake
            GROUP BY date ORDER BY total DESC LIMIT 1
        ''')
        row = cursor.fetchone()
        if row:
            return row[0], row[1]
        return None, 0

    def get_monthly_summary(self) -> List[Tuple[str, str, int, int, int]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        settings = self.load_settings()
        goal = settings.daily_goal
        
        cursor.execute('''
            SELECT strftime('%Y', date) as year, strftime('%m', date) as month,
                   AVG(daily_total),
                   SUM(CASE WHEN daily_total >= ? THEN 1 ELSE 0 END),
                   COUNT(date)
            FROM (
                SELECT date, SUM(amount) as daily_total
                FROM water_intake GROUP BY date
            )
            GROUP BY year, month
            ORDER BY year DESC, month DESC
        ''', (goal,))
        return cursor.fetchall()
