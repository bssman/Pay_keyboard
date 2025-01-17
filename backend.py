import os
import smtplib
from flask_cors import CORS
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from threading import Thread
import logging

app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Email credentials (Replace with your email provider settings)
EMAIL_HOST = os.getenv("EMAIL_HOST", )
EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_email(to_email, subject, body):
    try:
        # Set up the MIME
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the server and send the email
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()  # Use TLS encryption
        server.login(EMAIL_USER, EMAIL_PASS)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        server.quit()

        logger.info(f"Email sent successfully to {to_email}")

    except Exception as e:
        logger.error(f"Error sending email: {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    logger.info(f"Received webhook data: {data}")

    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']
        amount = data['data']['amount'] // 100  # Convert kobo to Naira

        if amount <= 0:
            return jsonify({"status": "error", "message": "Invalid amount provided"}), 400

        # Send email to the customer with the amount paid
        subject = "Payment Successful"
        body = f"Dear Customer, \n\nYour payment of {amount} NGN was successful. Thank you for using our service!"
        send_email(email, subject, body)

        return jsonify({"status": "success", "message": "Email sent to customer."}), 200

    return jsonify({"status": "error", "message": "Invalid event type"}), 400

if __name__ == "__main__":
    app.run(debug=True)
