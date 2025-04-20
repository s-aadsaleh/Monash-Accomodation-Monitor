#!/usr/bin/env python3

import asyncio
from playwright.async_api import async_playwright
import hashlib
import time
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import argparse
from bs4 import BeautifulSoup
import difflib

# URL to monitor
TARGET_URL = "https://www.monash.edu/accommodation/apply/apply-now"

# File to store previous state
HISTORY_FILE = "webpage_state.txt"

# Directory for archives
ARCHIVE_DIR = "webpage_archives"

# Email Configuration - EDIT THESE VALUES
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # e.g., smtp.gmail.com for Gmail
    'smtp_port': 587,                 # typically 587 for TLS
    'use_tls': True,                  # True for most modern email providers
    'username': 'liamishere9@gmail.com',  # your email login
    'password': 'xnqq njjc hhrc zwta',    # your email password or app password
    'sender': 'liamishere9@gmail.com',   # email address to send from
    'recipient': 'netting-locker.8g@icloud.com'  # email address to receive notifications
}

def ensure_archive_dir():
    """Ensure the archive directory exists"""
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)

def archive_content(content):
    """Archive the current content with timestamp"""
    ensure_archive_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(ARCHIVE_DIR, f"fetch_{timestamp}.txt")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Archived content to {filename}")

async def fetch_webpage():
    """Fetch the webpage content using Playwright and extract the applications section"""
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch()
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            # Create a new page
            page = await context.new_page()
            
            # Navigate to the page
            await page.goto(TARGET_URL, wait_until="networkidle")
            
            # Wait for the content to load
            await page.wait_for_selector("body")
            
            # Extract the applications section text
            content = await page.evaluate("""
                () => {
                    // Find the section containing accommodation applications
                    const sections = Array.from(document.querySelectorAll('div, section'));
                    let targetSection = null;
                    
                    for (const section of sections) {
                        const text = section.textContent.toLowerCase();
                        if (text.includes('accommodation applications') && 
                            text.includes('clayton campus') && 
                            text.includes('peninsula campus')) {
                            targetSection = section;
                            break;
                        }
                    }
                    
                    if (targetSection) {
                        return targetSection.textContent.trim();
                    }
                    return null;
                }
            """)
            
            # Close browser
            await browser.close()
            
            if not content:
                print("Could not find the applications section on the page")
                return None
                
            return content
    except Exception as e:
        print(f"Error fetching webpage: {e}")
        return None

def get_webpage_hash(content):
    """Generate a hash of the webpage content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def save_state(content_hash, content):
    """Save the current state to a file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# Last updated: {timestamp}\n")
        f.write(f"{content_hash}\n\n")
        f.write(content)

def load_previous_state():
    """Load the previous state from the file"""
    if not os.path.exists(HISTORY_FILE):
        return None, None
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # Skip the timestamp line and get the hash and content
            parts = content.split('\n\n', 1)
            if len(parts) == 2:
                # Split the first part to get the hash (skip timestamp line)
                hash_line = parts[0].split('\n')[1]  # Get second line (hash)
                return hash_line.strip(), parts[1]
            return None, None
    except Exception as e:
        print(f"Error loading previous state: {e}")
        return None, None

def get_text_differences(old_content, new_content):
    """Get a readable diff between old and new content"""
    if not old_content:
        return "Initial check - no previous content to compare."
    
    # Split content into lines
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    # Generate diff
    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))
    
    # Format changes for email
    changes = []
    for line in diff:
        if line.startswith('+ '):  # Added line
            changes.append(f"ADDED: {line[2:]}")
        elif line.startswith('- '):  # Removed line
            changes.append(f"REMOVED: {line[2:]}")
        elif line.startswith('? '):  # Changed line
            changes.append(f"CHANGED: {line[2:]}")
    
    if not changes:
        return "No text differences detected."
    
    return "\n".join(changes)

def send_email(old_content, new_content):
    """Send email notification about the change"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender']
        msg['To'] = EMAIL_CONFIG['recipient']
        msg['Subject'] = "Change Detected in Monash Accommodation Text"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get the actual differences
        differences = get_text_differences(old_content, new_content)
        
        body = f"""Change detected in Monash Accommodation text at {timestamp}

Changes detected:
----------------
{differences}

Current Text Content:
-------------------
{new_content}

Please visit the page to check: {TARGET_URL}
"""
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        if EMAIL_CONFIG['use_tls']:
            server.starttls()
        
        if EMAIL_CONFIG['username'] and EMAIL_CONFIG['password']:
            server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        
        server.send_message(msg)
        server.quit()
        
        print(f"Email notification sent to {EMAIL_CONFIG['recipient']}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

async def check_for_changes():
    """Check for changes on the webpage"""
    print(f"Checking for changes at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    # Get current content
    current_content = await fetch_webpage()
    if not current_content:
        print("Failed to fetch webpage. Will try again later.")
        return False
    
    # Archive the current content
    archive_content(current_content)
    
    current_hash = get_webpage_hash(current_content)
    
    # Get previous content
    previous_hash, previous_content = load_previous_state()
    
    # First run - always send notification and save state
    if previous_hash is None:
        print("First run of this session. Saving current state and sending notification.")
        save_state(current_hash, current_content)
        return send_email(None, current_content)
    
    # Check for changes
    if current_hash != previous_hash:
        print("Change detected!")
        save_state(current_hash, current_content)
        return send_email(previous_content, current_content)
    
    print("No changes detected.")
    return False

async def main():
    parser = argparse.ArgumentParser(description='Monitor Monash Accommodation webpage for changes')
    parser.add_argument('--interval', type=int, default=3600, 
                        help='Interval between checks in seconds (default: 3600 = 1 hour)')
    parser.add_argument('--run-once', action='store_true', 
                        help='Run once and exit')
    
    args = parser.parse_args()
    
    print(f"Starting monitoring of {TARGET_URL}")
    print(f"Check interval: {args.interval} seconds")
    
    # Save PID and interval for web interface
    with open('monitor.pid', 'w') as f:
        f.write(str(os.getpid()))
    with open('monitor_interval.txt', 'w') as f:
        f.write(str(args.interval))
    
    # Initial check
    await check_for_changes()
    
    if args.run_once:
        print("Run once mode. Exiting.")
        # Clean up PID file
        if os.path.exists('monitor.pid'):
            os.remove('monitor.pid')
        return
    
    # Continuous monitoring
    try:
        while True:
            # Get the start time of this cycle
            cycle_start = time.time()
            
            # Wait for the full interval
            time.sleep(args.interval)
            
            # Get the end time of this cycle
            cycle_end = time.time()
            
            # Calculate actual time slept
            actual_sleep = cycle_end - cycle_start
            
            # If we slept less than the interval (due to system load or other factors),
            # wait for the remaining time
            if actual_sleep < args.interval:
                remaining_time = args.interval - actual_sleep
                time.sleep(remaining_time)
            
            # Perform the check
            await check_for_changes()
            
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
    finally:
        # Clean up PID file
        if os.path.exists('monitor.pid'):
            os.remove('monitor.pid')

if __name__ == "__main__":
    asyncio.run(main()) 