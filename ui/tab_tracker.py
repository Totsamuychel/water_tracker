import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime

class TrackerTab(ttk.Frame):
    """Tracker Tab for adding and managing today's water intake."""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        
        self.history_map = {}
        self.last_intake = 0  # Store last known intake for animation
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        
        self._create_ui()
        # Initial draw
        settings = self.db.load_settings()
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.last_intake = self.db.get_today_intake(today)
        self.update_display(animate=False)
        
    def _create_ui(self):
        # Progress Frame
        progress_frame = ttk.LabelFrame(self, text="Ваш прогресс")
        progress_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        progress_frame.columnconfigure(0, weight=1)
        
        self.canvas = tk.Canvas(progress_frame, width=200, height=200, highlightthickness=0)
        self.canvas.pack(pady=20, anchor="center")
        
        self.status_label = ttk.Label(progress_frame, text="", font=("Segoe UI", 12))
        self.status_label.pack(pady=5)
        
        self.emoji_label = ttk.Label(progress_frame, text="", font=("Segoe UI Emoji", 28))
        self.emoji_label.pack(pady=5)
        
        # Controls Frame
        controls_frame = ttk.Frame(self)
        controls_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.rowconfigure(1, weight=1)
        
        btn_frame = ttk.LabelFrame(controls_frame, text="Быстрое добавление")
        btn_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Grid layout for buttons for better look
        amounts = [(100, "100 мл"), (200, "200 мл"), (250, "250 мл"), (500, "500 мл")]
        for i, (amount, text) in enumerate(amounts):
            btn_frame.columnconfigure(i, weight=1)
            ttk.Button(btn_frame, text=text, command=lambda a=amount: self.add_water(a)).grid(row=0, column=i, padx=5, pady=10, sticky="ew")
            
        custom_frame = ttk.Frame(btn_frame)
        custom_frame.grid(row=1, column=0, columnspan=4, pady=5, padx=5, sticky="ew")
        ttk.Label(custom_frame, text="Свой объем (мл):").pack(side="left")
        self.custom_entry = ttk.Entry(custom_frame, width=12)
        self.custom_entry.pack(side="left", padx=5)
        ttk.Button(custom_frame, text="Добавить", command=self.add_custom_water).pack(side="left")
        
        # History
        history_frame = ttk.LabelFrame(controls_frame, text="История за сегодня")
        history_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        
        self.history_list = tk.Listbox(history_frame, font=("Segoe UI", 11), borderwidth=0, highlightthickness=0)
        self.history_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.history_list.config(yscrollcommand=scrollbar.set)
        
        action_frame = ttk.Frame(controls_frame)
        action_frame.grid(row=2, column=0, sticky="ew", pady=5)
        for i in range(3):
            action_frame.columnconfigure(i, weight=1)
            
        ttk.Button(action_frame, text="Изменить", command=self.edit_record).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(action_frame, text="Удалить", command=self.delete_record).grid(row=0, column=1, padx=2, sticky="ew")
        ttk.Button(action_frame, text="Очистить", command=self.clear_history).grid(row=0, column=2, padx=2, sticky="ew")
        
    def _draw_progress_circle(self, current: float, total: int):
        self.canvas.delete("all")
        bg_color = "#1c1c1c" if self.app.is_dark_theme else "#fafafa"
        self.canvas.config(bg=bg_color)
        
        outline_color = "#333333" if self.app.is_dark_theme else "#e0e0e0"
        self.canvas.create_oval(10, 10, 190, 190, outline=outline_color, width=15)
        
        if total > 0:
            percentage = min(current / total, 1.0)
            extent = - (percentage * 360)
            
            arc_color = "#4da6ff"
            if percentage >= 1.0:
                arc_color = "#4caf50" # Green
                
            if percentage > 0:
                self.canvas.create_arc(10, 10, 190, 190, start=90, extent=extent, 
                                       outline=arc_color, style="arc", width=15)
                                       
            text_color = "white" if self.app.is_dark_theme else "black"
            self.canvas.create_text(100, 95, text=f"{int(percentage*100)}%", font=("Segoe UI", 26, "bold"), fill=text_color)
            self.canvas.create_text(100, 135, text=f"{int(current)} / {total} мл", font=("Segoe UI", 10), fill="gray")
            
    def animate_progress(self, start_val, end_val, total, steps=20, delay=15):
        if hasattr(self, '_anim_id') and self._anim_id:
            self.after_cancel(self._anim_id)
            
        def step(current_step):
            if current_step <= steps:
                val = start_val + (end_val - start_val) * (current_step / steps)
                self._draw_progress_circle(val, total)
                self._anim_id = self.after(delay, lambda: step(current_step + 1))
            else:
                self._draw_progress_circle(end_val, total)
                self._anim_id = None
                
        step(1)
            
    def update_display(self, animate=True):
        settings = self.db.load_settings()
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        today_intake = self.db.get_today_intake(today)
        
        if animate and today_intake != self.last_intake:
            self.animate_progress(self.last_intake, today_intake, settings.daily_goal)
        else:
            self._draw_progress_circle(today_intake, settings.daily_goal)
            
        self.last_intake = today_intake
        
        remaining = max(0, settings.daily_goal - today_intake)
        if remaining > 0:
            self.status_label.config(text=f"Осталось: {remaining} мл до цели")
        else:
            self.status_label.config(text="Цель достигнута! Отличная работа 🎉")
            
        if settings.daily_goal > 0:
            pct = today_intake / settings.daily_goal
            if pct == 0:
                emoji = "🏜️"
            elif pct <= 0.33:
                emoji = "🥤"
            elif pct <= 0.66:
                emoji = "💧"
            elif pct < 1.0:
                emoji = "🌊"
            else:
                emoji = "🏆"
            self.emoji_label.config(text=emoji)
            
        self.update_history_list()
        
    def update_history_list(self):
        self.history_list.delete(0, tk.END)
        self.history_map.clear()
        today = datetime.date.today().strftime("%Y-%m-%d")
        records = self.db.get_history(today)
        
        # Apply theme to listbox
        bg_color = "#2b2b2b" if self.app.is_dark_theme else "white"
        fg_color = "white" if self.app.is_dark_theme else "black"
        self.history_list.config(bg=bg_color, fg=fg_color, selectbackground="#4da6ff")
        
        for idx, record in enumerate(records):
            time_str = ""
            if record.timestamp:
                try:
                    dt = datetime.datetime.strptime(record.timestamp, '%Y-%m-%d %H:%M:%S')
                    time_str = dt.strftime('%H:%M')
                except ValueError:
                    time_str = "..."
            self.history_list.insert(tk.END, f"  🕒 {time_str}   |   💧 {record.amount} мл")
            self.history_map[idx] = record.id

    def add_water(self, amount: int):
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.db.add_water(amount, today)
        self.app.update_all_tabs()
        
    def add_custom_water(self):
        val = self.custom_entry.get().strip()
        if val.isdigit() and int(val) > 0:
            self.add_water(int(val))
            self.custom_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Ошибка", "Введите корректное число больше нуля")
            
    def edit_record(self):
        selection = self.history_list.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите запись для изменения")
            return
            
        idx = selection[0]
        record_id = self.history_map.get(idx)
        if record_id is None:
            return
            
        new_amount = simpledialog.askinteger("Изменить", "Введите новый объем (мл):", 
                                             parent=self, minvalue=1)
        if new_amount is not None:
            self.db.update_record(record_id, new_amount)
            self.app.update_all_tabs()

    def delete_record(self):
        selection = self.history_list.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
            
        if messagebox.askyesno("Удаление", "Вы уверены, что хотите удалить эту запись?"):
            idx = selection[0]
            record_id = self.history_map.get(idx)
            if record_id is not None:
                self.db.delete_record(record_id)
                self.app.update_all_tabs()

    def clear_history(self):
        if messagebox.askyesno("Очистка", "Вы уверены, что хотите очистить всю историю за сегодня?"):
            today = datetime.date.today().strftime("%Y-%m-%d")
            self.db.clear_history(today)
            self.app.update_all_tabs()
