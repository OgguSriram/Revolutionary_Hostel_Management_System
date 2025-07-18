# main.py
from flask import Flask
import threading
import logging
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD

from google_sheets import init_google_sheets
from fingerprint import init_fingerprint_sensor
from scheduler import run_scheduler
from attendance import background_attendance
from lcd_display import lcd_display

app = Flask(__name__)
app.secret_key = "hostel_secret_key_2025"

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GPIO and LCD setup
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
Buzzer = 7
GPIO.setup(Buzzer, GPIO.OUT)
lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)
lcd.clear()

# Initialize sheets and sensor
client, enrollment_sheet, attendance_sheet, history_sheet = init_google_sheets()
f = init_fingerprint_sensor()

# Thread events
stop_attendance_thread = threading.Event()
stop_scheduler_thread = threading.Event()

def start_threads():
    attendance_thread = threading.Thread(target=background_attendance, args=(stop_attendance_thread,))
    scheduler_thread = threading.Thread(target=run_scheduler, args=(stop_scheduler_thread,))
    attendance_thread.daemon = True
    scheduler_thread.daemon = True
    attendance_thread.start()
    scheduler_thread.start()

@app.route('/')
def home():
    lcd_display("Dashboard")
    return "HAMS Dashboard Running"

if __name__ == "__main__":
    try:
        print("Hostel Attendance System Started")
        lcd_display("HAMS STARTED")
        start_threads()
        app.run(host='0.0.0.0', port=5002, debug=False)
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        lcd_display("Terminated")
        stop_attendance_thread.set()
        stop_scheduler_thread.set()
    except Exception as e:
        print(f"Unexpected error: {e}")
        lcd_display("System Error")
        stop_attendance_thread.set()
        stop_scheduler_thread.set()
    finally:
        GPIO.cleanup()
        lcd.clear()
        print("GPIO resources cleaned up.")
```

```python
# fingerprint.py
def init_fingerprint_sensor():
    from pyfingerprint.pyfingerprint import PyFingerprint
    import sys
    try:
        f = PyFingerprint('/dev/ttyS0', 57600, 0xFFFFFFFF, 0x00000000)
        if not f.verifyPassword():
            raise ValueError("Incorrect fingerprint sensor password!")
        print("Fingerprint Sensor Initialized")
        return f
    except Exception as e:
        print(f"Fingerprint sensor error: {e}")
        sys.exit(1)
```

```python
# attendance.py
def background_attendance(stop_event):
    from lcd_display import lcd_display
    from datetime import datetime
    import time
    while not stop_event.is_set():
        current_time = datetime.now().strftime("%H:%M")
        if "18:00" <= current_time <= "22:00":
            lcd_display("Mock: Attendance")
            time.sleep(2)
        else:
            lcd_display("HAMS STARTED")
            time.sleep(1)
```

```python
# email_alerts.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, body):
    sender_email = "youremail@example.com"
    password = "your-app-password"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.send_message(msg)
```

```python
# google_sheets.py
def init_google_sheets():
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import sys

    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    CREDS_FILE = "credentials.json"

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        enrollment = client.open("HOSTEL_ENROLL").sheet1
        attendance = client.open("HOSTEL_ATTENDANCE").sheet1
        history = client.open("HOSTEL_ATTENDANCE_HISTORY").sheet1
        return client, enrollment, attendance, history
    except Exception as e:
        print(f"Google Sheets error: {e}")
        sys.exit(1)
```

```python
# scheduler.py
import schedule
import time

def run_scheduler(stop_event):
    schedule.every().day.at("22:00").do(lambda: print("Send absent alerts"))
    schedule.every().day.at("23:30").do(lambda: print("Save history"))
    schedule.every().day.at("23:50").do(lambda: print("Reset attendance"))

    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)
```

```python
# lcd_display.py
from RPLCD.i2c import CharLCD

lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)
lcd.clear()

def lcd_display(message):
    lcd.clear()
    row1 = message[:16].ljust(16)
    lcd.cursor_pos = (0, 0)
    lcd.write_string(row1)
    if len(message) > 16:
        row2 = message[16:32].ljust(16)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(row2)
```

```python
# utils.py
import secrets
import string

def generate_otp(length=6):
    return ''.join(secrets.choice(string.digits) for _ in range(length))
```
