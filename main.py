import logging
from ui import WaterTrackerApp

def setup_logging():
    logging.basicConfig(
        filename='water_tracker.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

if __name__ == "__main__":
    setup_logging()
    app = WaterTrackerApp()
    app.run()
