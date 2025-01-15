from flask import Flask, request, jsonify
import pyotp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])

# Secret key for OTP
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set.")

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL = "garpiyan@gmail.com"
PASSWORD = "Live&4507&86"

# Generate OTP using pyotp
def generate_otp(counter):
    hotp = pyotp.HOTP(SECRET_KEY)
    return hotp.at(counter)

# Send OTP to email
def send_email(recipient_email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Your OTP for Pump Activation"

        body = f"Your OTP is: {otp}. It is valid for 5 minutes."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/')
def home():
    return "Backend is running."

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received webhook data:", data)  # Log incoming data for debugging
    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']
        transaction_id = data['data']['id']  # Get the transaction ID

        # Generate a numeric counter from the transaction ID
        counter = sum(ord(char) for char in transaction_id)  # Convert to an integer

        otp = generate_otp(counter)

        # Send OTP to email
        send_email(email, otp)

        return jsonify({"status": "success", "message": "OTP sent to email"}), 200
    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
