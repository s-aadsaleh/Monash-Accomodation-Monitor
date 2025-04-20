from flask import Flask, render_template, send_from_directory
import os
import json
import time
from datetime import datetime
import glob
from monitor import HISTORY_FILE, ARCHIVE_DIR, EMAIL_CONFIG
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

def get_script_status():
    """Get the current status of the monitoring script"""
    try:
        # Check if the script is running
        if os.path.exists('monitor.pid'):
            with open('monitor.pid', 'r') as f:
                pid = int(f.read().strip())
                try:
                    # Check if process exists and is running
                    os.kill(pid, 0)
                    # Also check if the process is actually our script
                    try:
                        with open(f'/proc/{pid}/cmdline', 'r') as cmdline:
                            cmd = cmdline.read()
                            if 'monitor.py' in cmd:
                                return "Running"
                    except:
                        # If we can't read cmdline, just trust the pid
                        return "Running"
                except OSError:
                    # Process doesn't exist
                    return "Not Running"
        return "Not Running"
    except Exception as e:
        print(f"Error checking status: {e}")
        return "Unknown"

def get_next_check_time():
    """Calculate time until next check"""
    try:
        if os.path.exists('monitor.pid'):
            with open('monitor.pid', 'r') as f:
                pid = int(f.read().strip())
                try:
                    os.kill(pid, 0)
                    # Get the interval from the running process
                    with open('monitor_interval.txt', 'r') as f:
                        interval = int(f.read().strip())
                    
                    # Get last check time from state file
                    if os.path.exists(HISTORY_FILE):
                        with open(HISTORY_FILE, 'r') as f:
                            first_line = f.readline()
                            if first_line.startswith('# Last updated:'):
                                last_time = datetime.strptime(first_line[15:].strip(), '%Y-%m-%d %H:%M:%S')
                                last_timestamp = last_time.timestamp()
                                current_time = time.time()
                                
                                # Calculate time since last check
                                time_since_last = current_time - last_timestamp
                                
                                # Calculate time until next check
                                time_until_next = interval - (time_since_last % interval)
                                
                                # Only show "Checking now..." if less than 5 seconds
                                if time_until_next < 5:
                                    return "Checking now..."
                                
                                # Format the time string
                                if time_until_next < 60:
                                    return f"{int(time_until_next)} seconds"
                                elif time_until_next < 3600:
                                    minutes = int(time_until_next // 60)
                                    seconds = int(time_until_next % 60)
                                    if seconds == 0:
                                        return f"{minutes} minutes"
                                    return f"{minutes} minutes, {seconds} seconds"
                                else:
                                    hours = int(time_until_next // 3600)
                                    minutes = int((time_until_next % 3600) // 60)
                                    if minutes == 0:
                                        return f"{hours} hours"
                                    return f"{hours} hours, {minutes} minutes"
                    return "Unknown"
                except OSError:
                    return "Not Running"
        return "Not Running"
    except Exception:
        return "Unknown"

def get_latest_content():
    """Get the latest content from the state file"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                # Skip the timestamp and hash lines
                parts = content.split('\n\n', 1)
                if len(parts) == 2:
                    return parts[1]
        return "No content available"
    except Exception:
        return "Error reading content"

def get_latest_filename():
    """Get the filename of the latest fetch"""
    try:
        files = glob.glob(os.path.join(ARCHIVE_DIR, '*.txt'))
        if files:
            # Sort by modification time, newest first
            files.sort(key=os.path.getmtime, reverse=True)
            return os.path.basename(files[0])
        return None
    except Exception:
        return None

def get_last_change_time():
    """Get the timestamp of the last detected change"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if first_line.startswith('# Last updated:'):
                    return first_line[15:].strip()
        return "No changes detected yet"
    except Exception:
        return "Error reading last change time"

def get_archive_files():
    """Get list of archive files"""
    try:
        files = glob.glob(os.path.join(ARCHIVE_DIR, '*.txt'))
        # Sort by modification time, newest first
        files.sort(key=os.path.getmtime, reverse=True)
        return files
    except Exception:
        return []

def get_current_interval():
    """Get the current interval from the monitor_interval.txt file"""
    try:
        if os.path.exists('monitor_interval.txt'):
            with open('monitor_interval.txt', 'r') as f:
                return int(f.read().strip())
        return 0
    except Exception:
        return 0

def format_interval(seconds):
    """Format interval into a human-readable string"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes} minutes"
        return f"{minutes} minutes, {remaining_seconds} seconds"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes == 0:
            return f"{hours} hours"
        return f"{hours} hours, {minutes} minutes"

@app.route('/send_test_email')
def send_test_email():
    """Send a test email with the latest content"""
    try:
        latest_content = get_latest_content()
        latest_filename = get_latest_filename()
        
        if latest_content and latest_filename:
            # Create a test email message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_CONFIG['sender']
            msg['To'] = EMAIL_CONFIG['recipient']
            msg['Subject'] = "TEST EMAIL: Monash Accommodation Monitor Test"
            
            body = f"""This is a TEST email from the Monash Accommodation Monitor.

The email system is working correctly. This is the current content as of {latest_filename}:

{latest_content}

This is NOT a notification of changes - it is only a test to verify the email system is working.
"""
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            if EMAIL_CONFIG['use_tls']:
                server.starttls()
            
            if EMAIL_CONFIG['username'] and EMAIL_CONFIG['password']:
                server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
            
            server.send_message(msg)
            server.quit()
            
            return "Test email sent successfully!"
        else:
            return "No content available to send"
    except Exception as e:
        return f"Error sending test email: {str(e)}"

@app.route('/')
def index():
    status = get_script_status()
    latest_content = get_latest_content()
    latest_filename = get_latest_filename()
    archive_files = get_archive_files()
    interval = get_current_interval()
    interval_display = format_interval(interval)
    last_change_time = get_last_change_time()
    
    return render_template('index.html',
                         status=status,
                         latest_content=latest_content,
                         latest_filename=latest_filename,
                         archive_files=archive_files,
                         interval_display=interval_display,
                         last_change_time=last_change_time,
                         email_recipient=EMAIL_CONFIG['recipient'])

@app.route('/archive/<filename>')
def view_archive(filename):
    try:
        return send_from_directory(ARCHIVE_DIR, filename)
    except Exception:
        return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50000) 