# 💧 Water Tracker (Трекер воды)

A lightweight Desktop application built with Python and Tkinter to help you maintain healthy hydration habits. It tracks your daily water intake, provides a visual calendar of your progress, and reminds you to drink water via Windows desktop notifications and Telegram bot messages.

## 🌟 Features
- **Daily Goal Tracking:** Set your daily water intake goal (e.g., 2000 ml) and track it with a visual progress bar.
- **Customizable Intake:** Add water using quick buttons (+100ml, +250ml, etc.) or input a custom amount.
- **History Management:** View, edit, or delete today's water intake records.
- **Visual Calendar:** A built-in interactive calendar showing your hydration success (Goal Achieved, Partially Achieved, Missed).
- **Smart Notifications:** 
  - Windows Desktop Notifications to remind you to drink.
  - Integration with Telegram to send you reminders directly to your phone.
- **Statistics:** View average daily intake, total tracked days, and a 7-day history overview.
- **SQLite Database:** All data is securely stored locally in an SQLite database (`water_tracker.db`).

## ⚙️ How It Works
The app consists of three main tabs:
1. **Tracker:** The main dashboard for adding water and tracking today's progress.
2. **Calendar:** A visual representation of your hydration history.
3. **Settings:** Configure your daily goal, reminder intervals, and Telegram integration.

Background threads manage notifications so they don't block the UI, triggering alerts based on your configured interval.

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Totsamuychel/water_tracker.git
cd water_tracker
```

### 2. Install Dependencies
It's highly recommended to use a virtual environment. Install the required external libraries:
```bash
pip install -r requirements.txt
```
*(The main requirements are `plyer` for desktop notifications and `requests` for the Telegram API).*

### 3. Run the App
Launch the graphical interface:
```bash
python water_tracker_.py
```

## 📱 Telegram Bot Setup
To receive reminders on your phone:
1. Message **@BotFather** in Telegram and send `/newbot` to create your own bot.
2. Copy the **Bot Token** provided by BotFather.
3. Send any message to your newly created bot.
4. Go to `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` to find your `chat_id`.
5. Enter the Token and Chat ID in the **Settings** tab of the app and click **Test Notification**.

## 🛠 Refactoring & Structure
- All code comments and docstrings are written in English for developer accessibility.
- Standardized PEP8 formatting applied to the codebase.
- Data and settings are automatically managed by the `WaterTracker` class with local SQLite storage.
