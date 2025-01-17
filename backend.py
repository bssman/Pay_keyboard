from flask import Flask, request, jsonify
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])

# Secret salt for token hashing
SECRET_SALT = os.getenv("SECRET_SALT", "default_salt")  # Use a secure value

# Email Configuration
SMTP_SERVER = "mail.codenrobots.com.ng"
SMTP_PORT = 465
EMAIL = "info@codenrobots.com.ng"
PASSWORD = "Live&4507"

# Function to generate hashed tokens
def generate_hashed_tokens(amount, transaction_id):
    num_tokens = amount // 200  # Assuming 200 NGN per token
    tokens = []
    for i in range(num_tokens):
        unique_data = f"{transaction_id}-{i}-{SECRET_SALT}"
        token = hashlib.sha256(unique_data.encode()).hexdigest()[:8]  # 8-character token
        tokens.append(token)
    return tokens

# Send tokens via email
def send_email(recipient_email, tokens):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Your OTPs for Pump Activation"

        body = "Your OTPs are:\n\n" + "\n".join(tokens) + "\n\nEach token can be used to activate the pump once."
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
        transaction_id = data['data']['id']  # Unique transaction ID
        payment_amount = data['data'].get('amount')  # Safely access the 'amount' field

        if not payment_amount:
            return jsonify({"status": "error", "message": "Amount not provided in webhook payload"}), 400

        try:
            payment_amount = int(payment_amount) // 100  # Convert kobo to Naira
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid payment amount"}), 400

        if payment_amount <= 0:
            return jsonify({"status": "error", "message": "Payment amount must be greater than zero"}), 400

        # Generate tokens based on payment amount and transaction ID
        tokens = generate_hashed_tokens(payment_amount, transaction_id)

        # Send tokens via email
        send_email(email, tokens)

        return jsonify({"status": "success", "message": "Tokens sent to email"}), 200
    
    return jsonify({"status": "ignored"}), 200


if __name__ == '__main__':
    app.run(port=10000, debug=True)
