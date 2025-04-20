# Monash Accommodation Monitor

A simple tool to monitor the Monash University accommodation applications page and notify you when changes are detected.

## Features

- Monitors the Monash accommodation applications page
- Sends email notifications when changes are detected
- Web interface to view current status and history
- Archives all changes for reference

## Setup

1. Install required packages:
```bash
pip3 install flask requests beautifulsoup4
```

2. Edit `monitor.py` and update the email settings:
```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'use_tls': True,
    'username': 'your-email@gmail.com',
    'password': 'your-app-password',
    'sender': 'your-email@gmail.com',
    'recipient': 'recipient@email.com'
}
```

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

1. Copy the service files to systemd:
```bash
sudo cp monitor.service web-interface.service /etc/systemd/system/
```

2. Enable and start the services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable monitor.service
sudo systemctl enable web-interface.service
sudo systemctl start monitor.service
sudo systemctl start web-interface.service
```

3. Check the status:
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
- All changes are archived in the `webpage_archives` directory
- The web interface shows the current status and allows viewing history
- Email notifications are sent when changes are detected 