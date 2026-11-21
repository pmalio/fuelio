"""Constants for Fuelio."""
from datetime import timedelta

DOMAIN = "fuelio"
CONF_FILE_PATH = "file_path"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_FILE_PATH = "/config/fuelio/vehicle-1-sync.csv"
DEFAULT_SCAN_INTERVAL = 5
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 1440
PLATFORMS = ["sensor"]
UPDATE_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL)
