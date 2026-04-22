import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime
import threading
import time
import os
import requests
from plyer import notification
import calendar


class WaterTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Трекер воды")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f8ff')
        
        # Database initialization
        self.init_database()
        
        # Load settings
        self.load_settings()
        
        # Create UI
        self.create_interface()
        
        # Start notification thread
        self.start_notification_thread()
        
    def init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('water_tracker.db')
        self.cursor = self.conn.cursor()
        
        # Create table for water intake records
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS water_intake (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create table for settings
        self.cursor.execute('''
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
        
        # Insert default settings if table is empty
        self.cursor.execute('SELECT COUNT(*) FROM settings')
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO settings 
                (daily_goal, reminder_interval, notifications_enabled, telegram_bot_token, telegram_chat_id, telegram_enabled) 
                VALUES (2000, 60, 1, '', '', 0)
            ''')
        
        self.conn.commit()
    
    def load_settings(self):
        """Load settings from database"""
        self.cursor.execute('''
            SELECT daily_goal, reminder_interval, notifications_enabled, 
                   telegram_bot_token, telegram_chat_id, telegram_enabled 
            FROM settings WHERE id = 1
        ''')
        result = self.cursor.fetchone()
        if result:
            self.daily_goal = result[0]
            self.reminder_interval = result[1]
            self.notifications_enabled = bool(result[2])
            self.telegram_bot_token = result[3] or ""
            self.telegram_chat_id = result[4] or ""
            self.telegram_enabled = bool(result[5])
        else:
            self.daily_goal = 2000
            self.reminder_interval = 60
            self.notifications_enabled = True
            self.telegram_bot_token = ""
            self.telegram_chat_id = ""
            self.telegram_enabled = False
    
    def save_settings(self):
        """Save settings to database"""
        self.cursor.execute('''
            UPDATE settings SET 
            daily_goal = ?, 
            reminder_interval = ?, 
            notifications_enabled = ?,
            telegram_bot_token = ?,
            telegram_chat_id = ?,
            telegram_enabled = ?
            WHERE id = 1
        ''', (self.daily_goal, self.reminder_interval, int(self.notifications_enabled),
              self.telegram_bot_token, self.telegram_chat_id, int(self.telegram_enabled)))
        self.conn.commit()
    
    def create_interface(self):
        """Create graphical user interface"""
        # Create tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Main tracker tab
        self.main_frame = ttk.Frame(notebook)
        notebook.add(self.main_frame, text='Трекер')
        self.create_main_tab()
        
        # Calendar tab
        self.calendar_frame = ttk.Frame(notebook)
        notebook.add(self.calendar_frame, text='Календарь')
        self.create_calendar_tab()
        
        # Settings tab
        self.settings_frame = ttk.Frame(notebook)
        notebook.add(self.settings_frame, text='Настройки')
        self.create_settings_tab()
        
    def create_main_tab(self):
        """Create main tracker tab"""
        # Title
        title_label = tk.Label(self.main_frame, text="💧 Трекер воды", 
                              font=('Arial', 20, 'bold'), bg='#f0f8ff', fg='#4682b4')
        title_label.pack(pady=20)
        
        # Current date
        today = datetime.date.today().strftime("%d.%m.%Y")
        date_label = tk.Label(self.main_frame, text=f"Сегодня: {today}", 
                             font=('Arial', 12), bg='#f0f8ff')
        date_label.pack(pady=5)
        
        # Progress bar
        self.progress_frame = tk.Frame(self.main_frame, bg='#f0f8ff')
        self.progress_frame.pack(pady=20)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, length=400, 
                                           variable=self.progress_var, maximum=100)
        self.progress_bar.pack()
        
        self.progress_label = tk.Label(self.progress_frame, text="", 
                                      font=('Arial', 12), bg='#f0f8ff')
        self.progress_label.pack(pady=5)
        
        # Water addition buttons
        buttons_frame = tk.Frame(self.main_frame, bg='#f0f8ff')
        buttons_frame.pack(pady=20)
        
        amounts = [100, 200, 250, 500]
        for amount in amounts:
            btn = tk.Button(buttons_frame, text=f"+{amount} мл", 
                          command=lambda a=amount: self.add_water(a),
                          font=('Arial', 12), bg='#87ceeb', fg='white',
                          padx=15, pady=5)
            btn.pack(side='left', padx=5)
        
        # Custom amount input
        custom_frame = tk.Frame(self.main_frame, bg='#f0f8ff')
        custom_frame.pack(pady=10)
        
        tk.Label(custom_frame, text="Другое количество:", 
                font=('Arial', 10), bg='#f0f8ff').pack(side='left')
        
        self.custom_entry = tk.Entry(custom_frame, width=10, font=('Arial', 10))
        self.custom_entry.pack(side='left', padx=5)
        
        custom_btn = tk.Button(custom_frame, text="Добавить", 
                              command=self.add_custom_water,
                              font=('Arial', 10), bg='#4682b4', fg='white')
        custom_btn.pack(side='left', padx=5)
        
        # Today's history
        history_frame = tk.LabelFrame(self.main_frame, text="История за сегодня", 
                                     font=('Arial', 12), bg='#f0f8ff')
        history_frame.pack(pady=20, fill='both', expand=True, padx=20)
        
        # Frame for history list and control buttons
        history_content = tk.Frame(history_frame, bg='#f0f8ff')
        history_content.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Selectable history listbox
        self.history_listbox = tk.Listbox(history_content, font=('Arial', 10), height=8)
        history_scrollbar = tk.Scrollbar(history_content, orient="vertical", 
                                       command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_listbox.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")
        
        # History management buttons
        history_buttons = tk.Frame(self.main_frame, bg='#f0f8ff')
        history_buttons.pack(pady=10)
        
        edit_btn = tk.Button(history_buttons, text="Редактировать", 
                           command=self.edit_selected_entry,
                           font=('Arial', 10), bg='#FFA500', fg='white', padx=10)
        edit_btn.pack(side='left', padx=5)
        
        delete_btn = tk.Button(history_buttons, text="Удалить", 
                             command=self.delete_selected_entry,
                             font=('Arial', 10), bg='#FF6B6B', fg='white', padx=10)
        delete_btn.pack(side='left', padx=5)
        
        clear_btn = tk.Button(history_buttons, text="Очистить всё за сегодня", 
                            command=self.clear_today_history,
                            font=('Arial', 10), bg='#DC143C', fg='white', padx=10)
        clear_btn.pack(side='left', padx=5)
        
        # Initial display update
        self.update_display()
    
    def create_calendar_tab(self):
        """Create calendar tab"""
        tk.Label(self.calendar_frame, text="📅 Календарь потребления воды", 
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Month navigation
        nav_frame = tk.Frame(self.calendar_frame)
        nav_frame.pack(pady=10)
        
        self.current_month = datetime.date.today().month
        self.current_year = datetime.date.today().year
        
        tk.Button(nav_frame, text="<", command=self.prev_month).pack(side='left')
        self.month_label = tk.Label(nav_frame, text="", font=('Arial', 12, 'bold'))
        self.month_label.pack(side='left', padx=20)
        tk.Button(nav_frame, text=">", command=self.next_month).pack(side='left')
        
        # Calendar canvas
        self.calendar_canvas = tk.Canvas(self.calendar_frame, width=700, height=400, bg='white')
        self.calendar_canvas.pack(pady=20)
        
        self.update_calendar()
    
    def create_settings_tab(self):
        """Create settings tab"""
        tk.Label(self.settings_frame, text="⚙️ Настройки", 
                font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(self.settings_frame, bg='#f0f8ff')
        scrollbar = ttk.Scrollbar(self.settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Main settings
        main_settings = tk.LabelFrame(scrollable_frame, text="Основные настройки", 
                                     font=('Arial', 12, 'bold'))
        main_settings.pack(pady=10, fill='x', padx=20)
        
        # Daily goal
        goal_frame = tk.Frame(main_settings)
        goal_frame.pack(pady=10, fill='x', padx=10)
        
        tk.Label(goal_frame, text="Дневная цель (мл):", font=('Arial', 12)).pack(side='left')
        self.goal_var = tk.StringVar(value=str(self.daily_goal))
        goal_entry = tk.Entry(goal_frame, textvariable=self.goal_var, width=10, font=('Arial', 12))
        goal_entry.pack(side='right')
        
        # Reminder interval
        reminder_frame = tk.Frame(main_settings)
        reminder_frame.pack(pady=10, fill='x', padx=10)
        
        tk.Label(reminder_frame, text="Интервал напоминаний (мин):", font=('Arial', 12)).pack(side='left')
        self.reminder_var = tk.StringVar(value=str(self.reminder_interval))
        reminder_entry = tk.Entry(reminder_frame, textvariable=self.reminder_var, width=10, font=('Arial', 12))
        reminder_entry.pack(side='right')
        
        # Notification settings
        notifications_frame = tk.LabelFrame(scrollable_frame, text="Уведомления", 
                                          font=('Arial', 12, 'bold'))
        notifications_frame.pack(pady=10, fill='x', padx=20)
        
        # System notifications (Windows)
        self.notifications_var = tk.BooleanVar(value=self.notifications_enabled)
        notifications_check = tk.Checkbutton(notifications_frame, 
                                           text="Системные уведомления Windows", 
                                           variable=self.notifications_var,
                                           font=('Arial', 11))
        notifications_check.pack(pady=5, anchor='w', padx=10)
        
        # Telegram notifications
        self.telegram_var = tk.BooleanVar(value=self.telegram_enabled)
        telegram_check = tk.Checkbutton(notifications_frame, 
                                      text="Уведомления в Telegram", 
                                      variable=self.telegram_var,
                                      font=('Arial', 11))
        telegram_check.pack(pady=5, anchor='w', padx=10)
        
        # Bot token
        token_frame = tk.Frame(notifications_frame)
        token_frame.pack(pady=5, fill='x', padx=10)
        
        tk.Label(token_frame, text="Токен бота:", font=('Arial', 10)).pack(anchor='w')
        self.token_var = tk.StringVar(value=self.telegram_bot_token)
        token_entry = tk.Entry(token_frame, textvariable=self.token_var, 
                             width=50, font=('Arial', 9), show='*')
        token_entry.pack(fill='x', pady=2)
        
        # Chat ID
        chat_frame = tk.Frame(notifications_frame)
        chat_frame.pack(pady=5, fill='x', padx=10)
        
        tk.Label(chat_frame, text="Chat ID:", font=('Arial', 10)).pack(anchor='w')
        self.chat_var = tk.StringVar(value=self.telegram_chat_id)
        chat_entry = tk.Entry(chat_frame, textvariable=self.chat_var, 
                            width=30, font=('Arial', 10))
        chat_entry.pack(fill='x', pady=2)
        
        # Telegram action buttons
        telegram_buttons = tk.Frame(notifications_frame)
        telegram_buttons.pack(pady=10, padx=10)
        
        test_btn = tk.Button(telegram_buttons, text="Тест уведомления", 
                           command=self.test_telegram,
                           font=('Arial', 10), bg='#4CAF50', fg='white', padx=10)
        test_btn.pack(side='left', padx=5)
        
        help_btn = tk.Button(telegram_buttons, text="Как настроить?", 
                           command=self.show_telegram_help,
                           font=('Arial', 10), bg='#2196F3', fg='white', padx=10)
        help_btn.pack(side='left', padx=5)
        
        # Save button
        save_btn = tk.Button(scrollable_frame, text="Сохранить настройки", 
                           command=self.save_settings_gui,
                           font=('Arial', 12), bg='#4682b4', fg='white',
                           padx=20, pady=10)
        save_btn.pack(pady=20)
        
        # Statistics frame
        stats_frame = tk.LabelFrame(scrollable_frame, text="Статистика", font=('Arial', 12))
        stats_frame.pack(pady=20, fill='both', expand=True, padx=20)
        
        self.stats_text = tk.Text(stats_frame, height=10, width=50, font=('Arial', 10))
        self.stats_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.update_stats()
    
    def add_water(self, amount):
        """Add water intake to database"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.cursor.execute('INSERT INTO water_intake (date, amount) VALUES (?, ?)', 
                           (today, amount))
        self.conn.commit()
        self.update_display()
        
    def add_custom_water(self):
        """Add custom amount of water"""
        try:
            amount = int(self.custom_entry.get())
            if amount > 0:
                self.add_water(amount)
                self.custom_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Ошибка", "Введите положительное число")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число")
    
    def get_today_intake(self):
        """Get today's total water intake"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.cursor.execute('SELECT SUM(amount) FROM water_intake WHERE date = ?', (today,))
        result = self.cursor.fetchone()[0]
        return result if result else 0
    
    def update_display(self):
        """Update main display with progress"""
        today_intake = self.get_today_intake()
        percentage = min((today_intake / self.daily_goal) * 100, 100)
        
        self.progress_var.set(percentage)
        self.progress_label.config(text=f"{today_intake} мл / {self.daily_goal} мл ({percentage:.1f}%)")
        
        # Update history listbox
        self.update_history()
    
    def update_history(self):
        """Update today's history listbox"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.cursor.execute('''
            SELECT id, amount, timestamp FROM water_intake 
            WHERE date = ? ORDER BY timestamp DESC
        ''', (today,))
        
        records = self.cursor.fetchall()
        
        self.history_listbox.delete(0, tk.END)
        if records:
            for record_id, amount, timestamp in records:
                time_str = timestamp.split()[1][:5]  # Format: HH:MM
                display_text = f"{time_str} - {amount} мл"
                self.history_listbox.insert(tk.END, display_text)
                
                # Store record IDs in a corresponding list
                if not hasattr(self, 'history_ids'):
                    self.history_ids = []
                if len(self.history_ids) <= self.history_listbox.size() - 1:
                    self.history_ids.append(record_id)
                else:
                    self.history_ids[self.history_listbox.size() - 1] = record_id
        else:
            self.history_listbox.insert(tk.END, "Сегодня вода еще не добавлялась")
            self.history_ids = []
    
    def edit_selected_entry(self):
        """Edit selected history entry"""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите запись для редактирования")
            return
        
        if not hasattr(self, 'history_ids') or not self.history_ids:
            messagebox.showwarning("Предупреждение", "Нет записей для редактирования")
            return
        
        try:
            index = selection[0]
            record_id = self.history_ids[index]
            
            # Fetch current amount
            self.cursor.execute('SELECT amount FROM water_intake WHERE id = ?', (record_id,))
            current_amount = self.cursor.fetchone()[0]
            
            # Ask for new amount
            new_amount = simpledialog.askinteger("Редактирование", 
                                               f"Новое количество воды (текущее: {current_amount} мл):",
                                               initialvalue=current_amount,
                                               minvalue=1, maxvalue=5000)
            
            if new_amount is not None:
                self.cursor.execute('UPDATE water_intake SET amount = ? WHERE id = ?', 
                                  (new_amount, record_id))
                self.conn.commit()
                self.update_display()
                messagebox.showinfo("Успех", f"Запись изменена на {new_amount} мл")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить запись: {str(e)}")
    
    def delete_selected_entry(self):
        """Delete selected history entry"""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
        
        if not hasattr(self, 'history_ids') or not self.history_ids:
            messagebox.showwarning("Предупреждение", "Нет записей для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            try:
                index = selection[0]
                record_id = self.history_ids[index]
                
                self.cursor.execute('DELETE FROM water_intake WHERE id = ?', (record_id,))
                self.conn.commit()
                self.update_display()
                messagebox.showinfo("Успех", "Запись удалена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить запись: {str(e)}")
    
    def clear_today_history(self):
        """Clear all history entries for today"""
        if messagebox.askyesno("Подтверждение", "Удалить ВСЕ записи за сегодня?"):
            try:
                today = datetime.date.today().strftime("%Y-%m-%d")
                self.cursor.execute('DELETE FROM water_intake WHERE date = ?', (today,))
                self.conn.commit()
                self.update_display()
                messagebox.showinfo("Успех", "Вся история за сегодня очищена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить историю: {str(e)}")
    
    def send_telegram_message(self, message):
        """Send a message via Telegram bot"""
        if not self.telegram_enabled or not self.telegram_bot_token or not self.telegram_chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False
    
    def test_telegram(self):
        """Test Telegram notification settings"""
        if not self.token_var.get() or not self.chat_var.get():
            messagebox.showerror("Ошибка", "Заполните токен бота и Chat ID")
            return
        
        # Temporarily save settings for the test
        old_token = self.telegram_bot_token
        old_chat = self.telegram_chat_id
        old_enabled = self.telegram_enabled
        
        self.telegram_bot_token = self.token_var.get()
        self.telegram_chat_id = self.chat_var.get()
        self.telegram_enabled = True
        
        success = self.send_telegram_message("🧪 <b>Тестовое сообщение</b>\\n\\nТрекер воды успешно подключен к Telegram!")
        
        # Restore original settings
        self.telegram_bot_token = old_token
        self.telegram_chat_id = old_chat
        self.telegram_enabled = old_enabled
        
        if success:
            messagebox.showinfo("Успех", "Тестовое сообщение отправлено!")
        else:
            messagebox.showerror("Ошибка", "Не удалось отправить сообщение. Проверьте настройки.")
    
    def show_telegram_help(self):
        """Show instructions for setting up Telegram"""
        help_text = """🤖 Как настроить Telegram уведомления:\n\n1️⃣ Создайте бота:\n   • Напишите @BotFather в Telegram\n   • Отправьте команду /newbot\n   • Следуйте инструкциям\n   • Скопируйте токен бота\n\n2️⃣ Получите Chat ID:\n   • Напишите своему боту любое сообщение\n   • Перейдите по ссылке:\n     https://api.telegram.org/bot[ВАШ_ТОКЕН]/getUpdates\n   • Найдите "chat":{"id": ЧИСЛО}\n   • Это число и есть ваш Chat ID\n\n3️⃣ Введите данные в настройках и нажмите "Тест"\n\n❗ Важно: Chat ID может быть отрицательным числом!"""
        
        messagebox.showinfo("Справка по Telegram", help_text)
    
    def prev_month(self):
        """Switch to previous month in calendar"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_calendar()
    
    def next_month(self):
        """Switch to next month in calendar"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_calendar()
    
    def update_calendar(self):
        """Update the calendar display"""
        # Clear canvas
        self.calendar_canvas.delete("all")
        
        # Display month name
        month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        self.month_label.config(text=f"{month_names[self.current_month-1]} {self.current_year}")
        
        # Get data for the month
        month_data = self.get_month_data(self.current_year, self.current_month)
        
        # Draw calendar structure
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        # Weekday headers
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for i, day in enumerate(days):
            x = 50 + i * 90
            self.calendar_canvas.create_text(x, 30, text=day, font=('Arial', 12, 'bold'))
        
        # Draw month days
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                    
                x = 50 + day_num * 90
                y = 60 + week_num * 50
                
                date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                intake = month_data.get(date_str, 0)
                
                # Assign color based on goal completion
                if intake >= self.daily_goal:
                    color = '#90EE90'  # Light green (Goal met)
                elif intake > 0:
                    color = '#FFE4B5'  # Beige (Partially met)
                else:
                    color = '#FFB6C1'  # Light pink (Missed)
                
                # Draw day rectangle
                self.calendar_canvas.create_rectangle(x-25, y-15, x+25, y+15, 
                                                    fill=color, outline='black')
                self.calendar_canvas.create_text(x, y-5, text=str(day), font=('Arial', 10, 'bold'))
                
                if intake > 0:
                    self.calendar_canvas.create_text(x, y+5, text=f"{intake}мл", 
                                                   font=('Arial', 8))
        
        # Draw legend
        legend_y = 350
        self.calendar_canvas.create_rectangle(50, legend_y, 70, legend_y+15, 
                                            fill='#90EE90', outline='black')
        self.calendar_canvas.create_text(80, legend_y+7, text='Цель достигнута', 
                                       font=('Arial', 10), anchor='w')
        
        self.calendar_canvas.create_rectangle(200, legend_y, 220, legend_y+15, 
                                            fill='#FFE4B5', outline='black')
        self.calendar_canvas.create_text(230, legend_y+7, text='Частично выполнено', 
                                       font=('Arial', 10), anchor='w')
        
        self.calendar_canvas.create_rectangle(380, legend_y, 400, legend_y+15, 
                                            fill='#FFB6C1', outline='black')
        self.calendar_canvas.create_text(410, legend_y+7, text='Пропущено', 
                                       font=('Arial', 10), anchor='w')
    
    def get_month_data(self, year, month):
        """Get water intake data for a specific month"""
        self.cursor.execute('''
            SELECT date, SUM(amount) FROM water_intake 
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY date
        ''', (str(year), f"{month:02d}"))
        
        return {date: amount for date, amount in self.cursor.fetchall()}
    
    def save_settings_gui(self):
        """Save settings updated via GUI"""
        try:
            self.daily_goal = int(self.goal_var.get())
            self.reminder_interval = int(self.reminder_var.get())
            self.notifications_enabled = self.notifications_var.get()
            self.telegram_bot_token = self.token_var.get()
            self.telegram_chat_id = self.chat_var.get()
            self.telegram_enabled = self.telegram_var.get()
            
            self.save_settings()
            self.update_display()
            self.update_stats()
            messagebox.showinfo("Успех", "Настройки сохранены!")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые значения")
    
    def update_stats(self):
        """Update the statistics text area"""
        # Fetch stats for the last 7 days
        self.cursor.execute('''
            SELECT date, SUM(amount) FROM water_intake 
            WHERE date >= date('now', '-7 days')
            GROUP BY date ORDER BY date DESC
        ''')
        
        week_data = self.cursor.fetchall()
        
        # Fetch overall statistics
        self.cursor.execute('SELECT COUNT(DISTINCT date) FROM water_intake')
        total_days = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT AVG(daily_total) FROM (SELECT SUM(amount) as daily_total FROM water_intake GROUP BY date)')
        avg_daily = self.cursor.fetchone()[0] or 0
        
        # Count days where daily goal was met
        self.cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT SUM(amount) as daily_total FROM water_intake 
                GROUP BY date HAVING daily_total >= ?
            )
        ''', (self.daily_goal,))
        goal_days = self.cursor.fetchone()[0]
        
        stats_text = f"📊 Общая статистика:\\n"
        stats_text += f"Дней с записями: {total_days}\\n"
        stats_text += f"Дней с достигнутой целью: {goal_days}\\n"
        stats_text += f"Среднее потребление: {avg_daily:.0f} мл/день\\n\\n"
        stats_text += "📅 Последние 7 дней:\\n"
        
        for date, amount in week_data:
            date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
            date_str = date_obj.strftime('%d.%m.%Y')
            percentage = (amount / self.daily_goal) * 100
            status = "✅" if amount >= self.daily_goal else "⚠️" if amount > 0 else "❌"
            stats_text += f"{status} {date_str}: {amount} мл ({percentage:.0f}%)\\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def start_notification_thread(self):
        """Start a background thread for handling notifications"""
        def notification_worker():
            while True:
                if self.notifications_enabled or self.telegram_enabled:
                    try:
                        today_intake = self.get_today_intake()
                        remaining = max(0, self.daily_goal - today_intake)
                        
                        if remaining > 0:
                            # Windows system notifications
                            if self.notifications_enabled:
                                notification.notify(
                                    title="💧 Напоминание о воде",
                                    message=f"Пора выпить воды! Осталось: {remaining} мл до цели",
                                    timeout=10
                                )
                            
                            # Telegram notifications
                            if self.telegram_enabled:
                                telegram_message = f"💧 <b>Напоминание о воде</b>\\n\\n"
                                telegram_message += f"🎯 Осталось до цели: <b>{remaining} мл</b>\\n"
                                telegram_message += f"📊 Выпито сегодня: <b>{today_intake} мл</b>\\n"
                                telegram_message += f"⏰ {datetime.datetime.now().strftime('%H:%M')}"
                                
                                self.send_telegram_message(telegram_message)
                        
                        # Congratulation upon reaching the goal
                        elif today_intake >= self.daily_goal and remaining == 0:
                            # Check if congratulation was already sent today
                            today = datetime.date.today().strftime("%Y-%m-%d")
                            congratulation_file = f"congratulation_{today}.flag"
                            
                            if not os.path.exists(congratulation_file):
                                if self.notifications_enabled:
                                    notification.notify(
                                        title="🎉 Цель достигнута!",
                                        message=f"Поздравляем! Вы выпили {today_intake} мл воды сегодня!",
                                        timeout=15
                                    )
                                
                                if self.telegram_enabled:
                                    telegram_congratulation = f"🎉 <b>Поздравляем!</b>\\n\\n"
                                    telegram_congratulation += f"✅ Вы достигли дневной цели!\\n"
                                    telegram_congratulation += f"🎯 Цель: <b>{self.daily_goal} мл</b>\\n"
                                    telegram_congratulation += f"💧 Выпито: <b>{today_intake} мл</b>\\n"
                                    telegram_congratulation += f"⭐ Отличная работа!"
                                    
                                    self.send_telegram_message(telegram_congratulation)
                                
                                # Create flag file to avoid spamming congratulations
                                with open(congratulation_file, 'w') as f:
                                    f.write("congratulated")
                    
                    except Exception as e:
                        print(f"Notification error: {e}")
                
                time.sleep(self.reminder_interval * 60)  # Convert minutes to seconds
        
        notification_thread = threading.Thread(target=notification_worker, daemon=True)
        notification_thread.start()
        
        # Cleanup old congratulation flags (files older than 1 day)
        def cleanup_congratulation_flags():
            try:
                for filename in os.listdir('.'):
                    if filename.startswith('congratulation_') and filename.endswith('.flag'):
                        file_path = os.path.join('.', filename)
                        if os.path.getmtime(file_path) < time.time() - 86400:  # 24 hours
                            os.remove(file_path)
            except Exception as e:
                print(f"Error cleaning up flags: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_congratulation_flags, daemon=True)
        cleanup_thread.start()
    
    def run(self):
        """Launch the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application closing event"""
        self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    # Check and prompt for required dependencies
    required_packages = ['plyer', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Необходимо установить следующие библиотеки:")
        for package in missing_packages:
            print(f"pip install {package}")
        print("\\nИли установите все сразу:")
        print(f"pip install {' '.join(missing_packages)}")
        exit(1)
    
    app = WaterTracker()
    app.run()