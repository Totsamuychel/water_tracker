# 💧 Water Tracker

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![UI](https://img.shields.io/badge/UI-Tkinter%20%2B%20sv__ttk-green.svg)
![Database](https://img.shields.io/badge/DB-SQLite-lightgrey.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)

**Water Tracker** is a lightweight, modern and beautiful desktop application for Windows, written in Python. It helps you maintain healthy hydration habits by tracking your daily water intake, reminding you to drink at regular intervals, and showing detailed analytics of your progress over time.

---

## 🌟 Features

### 💧 Tracker Tab
- Smooth **animated circular progress ring** showing your daily goal completion.
- Quick-add buttons for common amounts: **100 ml, 200 ml, 250 ml, 500 ml**.
- Custom amount input for any value.
- Keyboard shortcuts: press **`1` `2` `3` `4`** on the keyboard to instantly add water.
- Full history management for today: **edit**, **delete**, or **clear all** records.
- Emoji water level indicator: 🏜️ → 🥤 → 💧 → 🌊 → 🏆

### 📅 Calendar Tab
- Interactive **month-by-month calendar** showing your hydration history.
- **Color-coded days**: green (goal reached), yellow (partially reached), red (below 50%), grey (no data).

### 📊 Statistics Tab
- **7-day bar chart** drawn with the built-in Tkinter Canvas — no external charting libraries needed.
- **Summary cards**: current streak (days in a row), best day, and monthly average intake.
- **Export to CSV** — one click to download all your data for use in Excel or Google Sheets.

### 🔔 Smart Notifications
- Background notification thread that never blocks the UI.
- **3 notification modes** (configurable in Settings):
  1. **Windows balloon** — standard OS desktop notification.
  2. **Custom popup** — an always-on-top Tkinter window with one-click "+250 ml / +500 ml" buttons.
  3. **Telegram bot** — reminders sent directly to your phone.
- Automatically congratulates you when the daily goal is reached (once per day).
- Reminder interval is applied **live** — no restart needed after changing it in Settings.

### 🖥️ System Tray
- Closing the window **minimizes the app to the system tray** (near the clock).
- Right-click the tray icon to:
  - Re-open the app.
  - Quickly add **250 ml** or **500 ml** without opening the window.
  - Quit the application completely.

### 🌙 Themes
- Toggle between a beautiful **Dark** and **Light** theme with one click.
- Smooth **crossfade animation** when switching — the transition looks premium.

---

## 🏗️ Architecture

The project was fully refactored from a single monolithic script into a clean modular structure:

```
water_tracker/
├── main.py            # Entry point, logging setup
├── database.py        # Thread-safe SQLite DatabaseManager
├── notifier.py        # Background notification service (thread)
├── models.py          # Typed dataclasses: WaterRecord, AppSettings
├── build.spec         # PyInstaller build configuration
├── build.bat          # One-click EXE builder script
├── requirements.txt   # Python dependencies
└── ui/
    ├── app.py         # Main app window, tray logic, theme toggle
    ├── tab_tracker.py # Tracker tab with animated canvas
    ├── tab_calendar.py# Calendar tab with canvas drawing
    ├── tab_stats.py   # Statistics tab with bar chart and CSV export
    └── tab_settings.py# Settings tab
```

**Key design decisions:**
- **Thread-safe SQLite**: every thread (UI, notifier) gets its own isolated database connection via `threading.local()`.
- **Type hints** and `dataclasses` throughout the codebase.
- Logging to `water_tracker.log` for easy debugging.
- Database stored in a local `data/` folder, auto-created on first run.

---

## 🚀 Getting Started

### Option 1: Download the ready-to-run `.exe`
Go to the [Releases](https://github.com/Totsamuychel/water_tracker/releases) page and download `WaterTracker.exe`.
Run it directly — **no Python installation required**.

### Option 2: Run from source

**1. Clone the repository:**
```bash
git clone https://github.com/Totsamuychel/water_tracker.git
cd water_tracker
```

**2. Install dependencies** (a virtual environment is recommended):
```bash
pip install -r requirements.txt
```

**3. Run the app:**
```bash
python main.py
```

---

## 📦 Building the `.exe` yourself

If you want to compile the app into a standalone executable:

1. Make sure PyInstaller is installed: `pip install pyinstaller`
2. Double-click `build.bat` **or** run in the terminal:
   ```bash
   pyinstaller build.spec
   ```
3. Your executable will appear in the `dist/` folder as `WaterTracker.exe`.
4. It runs silently (no console window) and is fully self-contained.

---

## 📱 Telegram Bot Setup

To receive reminders on your phone:

1. Open Telegram and find **@BotFather**. Send `/newbot` and follow the steps.
2. Copy the **Bot Token** BotFather gives you.
3. Send any message (e.g. "Hello") to your new bot.
4. In your browser, open:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
5. Find `"chat":{"id": 123456789}` in the response — that is your **Chat ID**.
6. Paste the Token and Chat ID into the **Settings** tab of the app, select **Telegram** as the notification type, and save.

---

> **Stay hydrated! 💧**
