import logging
from flask import Flask, request, jsonify
import pyotp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])

# Configure logging
logging.basicConfig(level=logging.INFO)  # Log all messages with INFO level or higher
logger = logging.getLogger(__name__)

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

        logger.info(f"Sending OTP to {recipient_email}")
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"OTP sent successfully to {recipient_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")

@app.route('/')
def home():
    return "Backend is running."

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logger.info(f"Received webhook data: {data}")
    
    try:
        if data['event'] == 'charge.success':
            email = data['data']['customer']['email']
            payment_amount = data['data'].get('amount', 0) // 100  # Convert to NGN
            transaction_id = data['data']['id']
            
            if payment_amount <= 0:
                raise ValueError("Invalid payment amount")

            logger.info(f"Processing payment: {payment_amount} NGN for transaction {transaction_id}")
            
            # Generate tokens
            tokens = generate_hashed_tokens(payment_amount, transaction_id)
            logger.info(f"Generated tokens: {tokens}")
            
            # Send email with tokens
            send_email(email, tokens)

            return jsonify({"status": "success", "message": "Tokens sent to email"}), 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def generate_hashed_tokens(payment_amount, transaction_id):
    # Example: Generate a list of tokens based on the payment amount
    num_tokens = payment_amount // 200  # Example: 1 token per 200 units paid
    logger.info(f"Generating {num_tokens} tokens for {transaction_id}")
    
    tokens = [f"token-{transaction_id}-{i}" for i in range(num_tokens)]
    return tokens

if __name__ == '__main__':
    app.run(port=5000, debug=True)
