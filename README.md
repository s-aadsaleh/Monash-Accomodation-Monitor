# Monash Accommodation Monitor

A simple tool to monitor the Monash University accommodation applications page and notify you when changes are detected.

## Features

- Monitors the Monash accommodation applications page using a headless browser
- Sends email notifications when changes are detected
- Web interface to view current status and history
- Archives all changes for reference


## Running Locally

1. Start the monitor:
```bash
python3 monitor.py --interval 100
```

2. Start the web interface:
```bash
python3 web_interface.py
```

The web interface will be available at `http://localhost:5001`

## Running on a Server

1. Install required system packages:
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv chromium-browser
```

2. Set up Python environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install flask requests beautifulsoup4 playwright
playwright install chromium
```

3. Copy the service files to systemd:
```bash
sudo cp monitor.service web-interface.service /etc/systemd/system/
```

4. Enable and start the services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable monitor.service
sudo systemctl enable web-interface.service
sudo systemctl start monitor.service
sudo systemctl start web-interface.service
```

5. Check the status:
```bash
sudo systemctl status monitor.service
sudo systemctl status web-interface.service
```

## Files

- `monitor.py` - Main monitoring script
- `web_interface.py` - Web interface
- `templates/` - Web interface templates
- `webpage_archives/` - Archived webpage content
- `monitor.service` - Systemd service for monitor
- `web-interface.service` - Systemd service for web interface

## Notes

- The monitor checks the page every 100 seconds by default
- Uses a headless browser to properly load the page
- All changes are archived in the `webpage_archives` directory
- The web interface shows the current status and allows viewing history
- Email notifications are sent when changes are detected 