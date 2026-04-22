import tkinter as tk
from tkinter import ttk, messagebox

class SettingsTab(ttk.Frame):
    """Settings Tab for app configuration."""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self._create_ui()
        self.load_settings()
        
    def _create_ui(self):
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="n", pady=20)
        
        gen_frame = ttk.LabelFrame(container, text="Основные настройки")
        gen_frame.pack(fill="x", pady=10, padx=10)
        
        ttk.Label(gen_frame, text="Дневная норма (мл):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.goal_var = tk.StringVar()
        ttk.Entry(gen_frame, textvariable=self.goal_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(gen_frame, text="Интервал напоминаний (мин):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.interval_var = tk.StringVar()
        ttk.Entry(gen_frame, textvariable=self.interval_var, width=15).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        notif_frame = ttk.LabelFrame(container, text="Тип уведомлений")
        notif_frame.pack(fill="x", pady=10, padx=10)
        
        self.notif_type_var = tk.StringVar(value="windows")
        ttk.Radiobutton(notif_frame, text="Windows (системные)", variable=self.notif_type_var, value="windows").pack(anchor="w", padx=10, pady=2)
        ttk.Radiobutton(notif_frame, text="Всплывающее окно", variable=self.notif_type_var, value="popup").pack(anchor="w", padx=10, pady=2)
        ttk.Radiobutton(notif_frame, text="Telegram", variable=self.notif_type_var, value="telegram").pack(anchor="w", padx=10, pady=2)
        ttk.Radiobutton(notif_frame, text="Windows + Telegram", variable=self.notif_type_var, value="both").pack(anchor="w", padx=10, pady=2)
        ttk.Radiobutton(notif_frame, text="Выключить", variable=self.notif_type_var, value="none").pack(anchor="w", padx=10, pady=2)
        
        tg_frame = ttk.LabelFrame(container, text="Настройки Telegram")
        tg_frame.pack(fill="x", pady=10, padx=10)
        
        ttk.Label(tg_frame, text="Токен бота:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.tg_token_var = tk.StringVar()
        ttk.Entry(tg_frame, textvariable=self.tg_token_var, width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(tg_frame, text="Chat ID:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.tg_chat_var = tk.StringVar()
        ttk.Entry(tg_frame, textvariable=self.tg_chat_var, width=30).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Button(container, text="Сохранить настройки", command=self.save_settings).pack(pady=20)
        
    def load_settings(self):
        settings = self.db.load_settings()
        self.goal_var.set(str(settings.daily_goal))
        self.interval_var.set(str(settings.reminder_interval))
        self.notif_type_var.set(settings.notification_type)
        self.tg_token_var.set(settings.telegram_bot_token)
        self.tg_chat_var.set(settings.telegram_chat_id)
        
    def save_settings(self):
        try:
            goal = int(self.goal_var.get())
            interval = int(self.interval_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Дневная норма и интервал должны быть числами")
            return
            
        settings = self.db.load_settings()
        settings.daily_goal = goal
        settings.reminder_interval = interval
        settings.notification_type = self.notif_type_var.get()
        settings.telegram_bot_token = self.tg_token_var.get().strip()
        settings.telegram_chat_id = self.tg_chat_var.get().strip()
        
        self.db.save_settings(settings)
        self.app.update_all_tabs()
        messagebox.showinfo("Успех", "Настройки сохранены")
