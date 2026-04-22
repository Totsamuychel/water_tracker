import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os

class StatsTab(ttk.Frame):
    """Statistics Tab showing overview, charts, and data export."""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        self._create_ui()
        self.update_stats()
        
    def _create_ui(self):
        self.summary_frame = ttk.Frame(self)
        self.summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        for i in range(4):
            self.summary_frame.columnconfigure(i, weight=1)
            
        self.lbl_total_days = self._create_card(self.summary_frame, "Всего дней", "0", 0)
        self.lbl_streak = self._create_card(self.summary_frame, "Текущая серия", "0", 1)
        self.lbl_best = self._create_card(self.summary_frame, "Лучший день", "0 мл", 2)
        self.lbl_avg = self._create_card(self.summary_frame, "В среднем", "0 мл", 3)
        
        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        chart_frame = ttk.LabelFrame(content_frame, text="За последние 7 дней")
        chart_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        self.chart_canvas = tk.Canvas(chart_frame, bg="white", highlightthickness=0)
        self.chart_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.bind("<Configure>", lambda e: self._draw_chart())
        
        table_frame = ttk.LabelFrame(content_frame, text="По месяцам")
        table_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        cols = ("month", "avg", "goal_days")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree.heading("month", text="Месяц")
        self.tree.heading("avg", text="Среднее (мл)")
        self.tree.heading("goal_days", text="Выполнено")
        self.tree.column("month", width=80)
        self.tree.column("avg", width=80)
        self.tree.column("goal_days", width=80)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        export_frame = ttk.Frame(self)
        export_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ttk.Button(export_frame, text="Экспорт в CSV", command=self.export_csv).pack(side="right")
        
    def _create_card(self, parent, title, initial_value, col):
        card = ttk.LabelFrame(parent, text=title)
        card.grid(row=0, column=col, sticky="nsew", padx=5)
        lbl = ttk.Label(card, text=initial_value, font=("Arial", 16, "bold"))
        lbl.pack(pady=15)
        return lbl
        
    def update_stats(self):
        streak = self.db.get_streak()
        best_date, best_amount = self.db.get_best_day()
        monthly = self.db.get_monthly_summary()
        
        total_days = sum(m[4] for m in monthly)
        total_avg = int(sum(m[2]*m[4] for m in monthly) / total_days) if total_days > 0 else 0
        
        self.lbl_total_days.config(text=str(total_days))
        self.lbl_streak.config(text=f"{streak} дней")
        self.lbl_best.config(text=f"{best_amount} мл")
        self.lbl_avg.config(text=f"{total_avg} мл")
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for row in monthly:
            year, month, avg, goal_days, m_total_days = row
            self.tree.insert("", "end", values=(
                f"{month}.{year}",
                f"{int(avg)}",
                f"{goal_days}/{m_total_days}"
            ))
            
        self._draw_chart()
        
    def _draw_chart(self):
        self.chart_canvas.delete("all")
        self.chart_canvas.update()
        w = self.chart_canvas.winfo_width()
        h = self.chart_canvas.winfo_height()
        if w <= 1 or h <= 1:
            w = 400
            h = 300
            
        bg_color = "#2b2b2b" if self.app.is_dark_theme else "white"
        self.chart_canvas.config(bg=bg_color)
        
        week_data = self.db.get_week_data(7)
        if not week_data:
            text_color = "white" if self.app.is_dark_theme else "black"
            self.chart_canvas.create_text(w/2, h/2, text="Нет данных", fill=text_color)
            return
            
        settings = self.db.load_settings()
        daily_goal = settings.daily_goal
        max_val = max(daily_goal, max(amt for _, amt in week_data))
        if max_val == 0:
            max_val = 1
            
        bar_width = w / 9
        spacing = (w - (bar_width * 7)) / 8
        
        for i, (date_str, amount) in enumerate(week_data):
            x0 = spacing + i * (bar_width + spacing)
            x1 = x0 + bar_width
            
            bar_h = (amount / max_val) * (h - 40)
            y0 = h - 20 - bar_h
            y1 = h - 20
            
            color = "#388e3c" if self.app.is_dark_theme else "#c8e6c9"
            if amount < daily_goal:
                if amount >= daily_goal * 0.5:
                    color = "#fbc02d" if self.app.is_dark_theme else "#fff9c4"
                else:
                    color = "#d32f2f" if self.app.is_dark_theme else "#ffcdd2"
                
            self.chart_canvas.create_rectangle(x0, y0, x1, y1, fill=color)
            
            day_str = date_str[-5:]
            text_color = "white" if self.app.is_dark_theme else "black"
            self.chart_canvas.create_text(x0 + bar_width/2, h - 10, text=day_str, fill=text_color, font=("Arial", 8))
            self.chart_canvas.create_text(x0 + bar_width/2, y0 - 10, text=str(amount), fill=text_color, font=("Arial", 8))
            
    def export_csv(self):
        downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        filepath = filedialog.asksaveasfilename(
            initialdir=downloads_folder,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Сохранить статистику"
        )
        
        if filepath:
            try:
                monthly = self.db.get_monthly_summary()
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Year", "Month", "Average Daily (ml)", "Days Goal Achieved", "Total Days Tracked"])
                    for row in monthly:
                        writer.writerow(row)
                messagebox.showinfo("Успех", f"Данные сохранены в {filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")
