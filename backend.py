from flask import Flask, request, jsonify
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])

# Secret key for hash-based token generation
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set.")

# Email Configuration
SMTP_SERVER = "mail.codenrobots.com.ng"
SMTP_PORT = 465
EMAIL = "info@codenrobots.com.ng"
PASSWORD = "Live&4507"

# Function to generate hash-based tokens
def generate_token(payment_amount, transaction_id):
    data = f"{payment_amount}{transaction_id}{SECRET_KEY}"
    return hashlib.sha256(data.encode()).hexdigest()[:8]

# Send tokens to email
def send_email(recipient_email, tokens):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Your Pump Activation Tokens"

        body = "Here are your tokens for pump activation:\n\n" + "\n".join(tokens) + "\n\nEach token can be used once."
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
        payment_amount = data['data']['amount']  # Amount paid (e.g., 1000, 5000)

        try:
            payment_amount = int(payment_amount) // 100  # Convert kobo to Naira if necessary
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid payment amount"}), 400

        # Generate tokens based on payment amount
        num_tokens = payment_amount // 200  # Example: 1 token per 200 units paid
        tokens = [
            generate_token(payment_amount, f"{transaction_id}-{i}")
            for i in range(num_tokens)
        ]

        # Send tokens to email
        send_email(email, tokens)

        return jsonify({"status": "success", "message": "Tokens sent to email", "tokens": tokens}), 200

    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(host = '0.0.0.0',port=5000, debug=True)
