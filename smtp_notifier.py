import streamlit as st
import smtplib
from email.mime.text import MIMEText

def send_email():
    email_sender = st.secrets["email"]
    email_password = st.secrets["password"]
    # temp hardcoded recipient email
    email_receiver = "200551990@student.georgianc.on.ca"
    email_subject = "Badge Issuance Notification"
    email_body = "Congratulations! Your badge has been issued successfully."

    msg = MIMEText(email_body)
    msg['Subject'] = email_subject
    msg['From'] = email_sender
    msg['To'] = email_receiver

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_sender, email_password)
        server.sendmail(email_sender, email_receiver, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")