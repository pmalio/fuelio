# Fuelio – Home Assistant integration

Custom Home Assistant integration for reading Fuelio CSV exports.

- Choose between a local CSV file and a Google Drive-synchronized CSV file.
- Google Drive is accessed through an external sync process (for example rclone + SMB); the integration itself does not authenticate to Google.
- Local polling with configurable refresh interval.
- Sensors for odometer, refuelling, fuel costs, consumption and service reminders.
- No telemetry: the CSV is read locally by Home Assistant.

See [README_PL.md](README_PL.md) for Polish installation and configuration instructions.
