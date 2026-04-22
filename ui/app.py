import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk
import pystray
from PIL import Image, ImageDraw
import threading
import datetime

from database import DatabaseManager
from notifier import NotificationService

from ui.tab_tracker import TrackerTab
from ui.tab_calendar import CalendarTab
from ui.tab_stats import StatsTab
from ui.tab_settings import SettingsTab

class WaterTrackerApp:
    """Main application class orchestrating UI and services."""
    def __init__(self):
        self.db = DatabaseManager()
        self.root = tk.Tk()
        self.root.title("Трекер воды")
        self.root.geometry("900x750")
        self.root.minsize(800, 600)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        self._setup_header()
        
        sv_ttk.set_theme("light")
        self.is_dark_theme = False
        
        # Keyboard shortcuts
        self.root.bind("1", lambda e: self.tracker_tab.add_water(100))
        self.root.bind("2", lambda e: self.tracker_tab.add_water(200))
        self.root.bind("3", lambda e: self.tracker_tab.add_water(250))
        self.root.bind("4", lambda e: self.tracker_tab.add_water(500))
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.tracker_tab = TrackerTab(self.notebook, self)
        self.notebook.add(self.tracker_tab, text='Трекер 💧')
        
        self.calendar_tab = CalendarTab(self.notebook, self)
        self.notebook.add(self.calendar_tab, text='Календарь 📅')
        
        self.stats_tab = StatsTab(self.notebook, self)
        self.notebook.add(self.stats_tab, text='Статистика 📊')
        
        self.settings_tab = SettingsTab(self.notebook, self)
        self.notebook.add(self.settings_tab, text='Настройки ⚙️')
        
        self.tray_icon = None
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        
        self.notifier = NotificationService(self.db, self.show_custom_popup, self.show_tray_balloon)
        self.notifier.start()
        
    def _setup_header(self):
        header = ttk.Frame(self.root)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        ttk.Label(header, text="💧 Water Tracker", font=("Segoe UI", 18, "bold")).pack(side="left")
        
        self.theme_btn = ttk.Button(header, text="🌙 Темная тема", command=self.toggle_theme)
        self.theme_btn.pack(side="right")
        
    def toggle_theme(self):
        import PIL.ImageGrab
        import PIL.ImageTk
        
        # 1. Take a screenshot of the current window for a smooth crossfade
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        
        try:
            img = PIL.ImageGrab.grab(bbox=(x, y, x+w, y+h))
            self.fade_photo = PIL.ImageTk.PhotoImage(img)
            
            # Create a borderless overlay exactly on top of the root window
            overlay = tk.Toplevel(self.root)
            overlay.overrideredirect(True)
            overlay.geometry(f"{w}x{h}+{x}+{y}")
            overlay.attributes("-topmost", True)
            label = tk.Label(overlay, image=self.fade_photo, bd=0, highlightthickness=0)
            label.pack()
        except Exception:
            overlay = None # Fallback if ImageGrab fails on some OS configs
            
        # 2. Switch the actual theme underneath
        if self.is_dark_theme:
            sv_ttk.set_theme("light")
            self.theme_btn.config(text="🌙 Темная тема")
        else:
            sv_ttk.set_theme("dark")
            self.theme_btn.config(text="☀️ Светлая тема")
        self.is_dark_theme = not self.is_dark_theme
        
        # Redraw all canvases with new theme colors
        self.update_all_tabs()
        
        # 3. Fade out the overlay
        if overlay:
            self.root.update()
            
            def fade_out(alpha):
                if alpha > 0:
                    overlay.attributes("-alpha", alpha)
                    self.root.after(20, lambda: fade_out(alpha - 0.1))
                else:
                    overlay.destroy()
                    self.fade_photo = None
                    
            fade_out(1.0)
        
    def update_all_tabs(self):
        # Pass animate=False to prevent animating during theme change or history edits
        self.tracker_tab.update_display(animate=True)
        self.calendar_tab.update_calendar()
        self.stats_tab.update_stats()
        
    def show_custom_popup(self, remaining: int, today_intake: int):
        self.root.after(0, lambda: self._create_popup(remaining, today_intake))
        
    def _create_popup(self, remaining: int, today_intake: int):
        if remaining <= 0:
            msg = f"Поздравляем! Вы достигли цели!\nВыпито сегодня: {today_intake} мл"
            title = "🎉 Цель достигнута"
        else:
            msg = f"Осталось до цели: {remaining} мл\nВыпито сегодня: {today_intake} мл"
            title = "💧 Пора выпить воды!"
            
        top = tk.Toplevel(self.root)
        top.title(title)
        top.geometry("320x160")
        top.attributes("-topmost", True)
        
        x = top.winfo_screenwidth() // 2 - 160
        y = top.winfo_screenheight() // 2 - 80
        top.geometry(f"+{x}+{y}")
        
        ttk.Label(top, text=msg, font=("Segoe UI", 11), justify="center").pack(pady=15)
        
        btn_frame = ttk.Frame(top)
        btn_frame.pack(pady=10)
        
        if remaining > 0:
            ttk.Button(btn_frame, text="+250 мл", command=lambda: [self.tracker_tab.add_water(250), top.destroy()]).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="+500 мл", command=lambda: [self.tracker_tab.add_water(500), top.destroy()]).pack(side="left", padx=5)
            
        ttk.Button(btn_frame, text="Позже", command=top.destroy).pack(side="left", padx=5)
        
    def show_tray_balloon(self, title: str, msg: str):
        if self.tray_icon:
            self.tray_icon.notify(msg, title)
            
    def run(self):
        self.root.mainloop()

    def create_image(self):
        image = Image.new('RGB', (64, 64), color=(255, 255, 255))
        dc = ImageDraw.Draw(image)
        dc.ellipse([16, 16, 48, 48], fill=(70, 130, 180))
        return image

    def hide_to_tray(self):
        self.root.withdraw()
        image = self.create_image()
        menu = (
            pystray.MenuItem('Открыть', self.show_from_tray, default=True),
            pystray.MenuItem('Добавить 250мл', lambda: self._tray_add(250)),
            pystray.MenuItem('Добавить 500мл', lambda: self._tray_add(500)),
            pystray.MenuItem('Выход', self.quit_app)
        )
        self.tray_icon = pystray.Icon("name", image, "Water Tracker", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_from_tray(self, icon, item):
        icon.stop()
        self.tray_icon = None
        self.root.after(0, self.root.deiconify)
        
    def _tray_add(self, amount: int):
        self.root.after(0, lambda: self.tracker_tab.add_water(amount))
        
    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.notifier.stop()
        self.root.quit()
