import tkinter as tk
from tkinter import ttk
import calendar
import datetime

class CalendarTab(ttk.Frame):
    """Calendar Tab showing monthly overview of water intake."""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.db
        
        self.current_year = datetime.datetime.now().year
        self.current_month = datetime.datetime.now().month
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        self._create_ui()
        self.update_calendar()
        
    def _create_ui(self):
        controls_frame = ttk.Frame(self)
        controls_frame.grid(row=0, column=0, pady=10)
        
        ttk.Button(controls_frame, text="< Пред", command=self.prev_month).grid(row=0, column=0, padx=10)
        self.month_label = ttk.Label(controls_frame, text="", font=("Arial", 14, "bold"))
        self.month_label.grid(row=0, column=1, padx=20)
        ttk.Button(controls_frame, text="След >", command=self.next_month).grid(row=0, column=2, padx=10)
        
        self.calendar_canvas = tk.Canvas(self, bg='white', highlightthickness=1, highlightbackground="#cccccc")
        self.calendar_canvas.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.bind("<Configure>", lambda e: self.update_calendar())

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar()
        
    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar()
        
    def update_calendar(self):
        self.calendar_canvas.delete("all")
        
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                      "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        self.month_label.config(text=f"{month_names[self.current_month-1]} {self.current_year}")
        
        self.calendar_canvas.update()
        width = self.calendar_canvas.winfo_width()
        height = self.calendar_canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            width = 800
            height = 500
            
        bg_color = "#1c1c1c" if self.app.is_dark_theme else "white"
        self.calendar_canvas.config(bg=bg_color)
            
        cell_width = width / 7
        cell_height = height / 7
        
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        header_bg = "#333333" if self.app.is_dark_theme else "#f0f0f0"
        header_fg = "white" if self.app.is_dark_theme else "black"
        
        for i, day in enumerate(days):
            x = i * cell_width
            self.calendar_canvas.create_rectangle(x, 0, x + cell_width, cell_height, fill=header_bg, outline="")
            self.calendar_canvas.create_text(x + cell_width/2, cell_height/2, text=day, font=("Segoe UI", 12, "bold"), fill=header_fg)
            
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        month_data = self.db.get_month_data(self.current_year, self.current_month)
        settings = self.db.load_settings()
        daily_goal = settings.daily_goal
        
        for row, week in enumerate(cal):
            for col, day in enumerate(week):
                if day == 0:
                    continue
                    
                x = col * cell_width
                y = (row + 1) * cell_height
                
                # Default empty cell color
                color = "#2b2b2b" if self.app.is_dark_theme else "white"
                
                amount = month_data.get(f"{self.current_year}-{self.current_month:02d}-{day:02d}", 0)
                if amount > 0:
                    if amount >= daily_goal:
                        color = "#388e3c" if self.app.is_dark_theme else "#c8e6c9"
                    elif amount >= daily_goal * 0.5:
                        color = "#fbc02d" if self.app.is_dark_theme else "#fff9c4"
                    else:
                        color = "#d32f2f" if self.app.is_dark_theme else "#ffcdd2"
                        
                border_color = "#444444" if self.app.is_dark_theme else "#eeeeee"
                self.calendar_canvas.create_rectangle(x, y, x + cell_width, y + cell_height, fill=color, outline=border_color)
                
                text_color = "white" if self.app.is_dark_theme else "black"
                self.calendar_canvas.create_text(x + 10, y + 10, text=str(day), anchor="nw", 
                                                 font=("Segoe UI", 10), fill=text_color)
                
                if amount > 0:
                    self.calendar_canvas.create_text(x + cell_width/2, y + cell_height/2,
                                                     text=f"{amount} мл", font=("Segoe UI", 10),
                                                     fill=text_color)
