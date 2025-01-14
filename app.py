from flask import Flask, request, jsonify
import pyotp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Secret key for OTP
SECRET_KEY = "YOUR_SECRET_KEY"

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

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']
        counter = data['data']['id']  # Use unique transaction ID as counter
        otp = generate_otp(counter)
        
        # Send OTP to email
        send_email(email, otp)

        return jsonify({"status": "success", "message": "OTP sent to email"}), 200
    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
