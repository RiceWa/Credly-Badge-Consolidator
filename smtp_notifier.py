import streamlit as st
import smtplib
from email.mime.text import MIMEText


def send_email(email_body, recipient_email):
    email_sender = st.secrets["email"]
    email_password = st.secrets["password"]
    email_server = st.secrets["smtp_server"]
    email_port = st.secrets["smtp_port"]

    email_receiver = recipient_email
    email_subject = "Badge Issuance Notification"

    msg = MIMEText(email_body)
    msg['Subject'] = email_subject
    msg['From'] = email_sender
    msg['To'] = email_receiver

    try:
        server = smtplib.SMTP(email_server, email_port)
        server.starttls()
        server.login(email_sender, email_password)
        server.sendmail(email_sender, email_receiver, msg.as_string())
        server.quit()
        print("Email sent successfully!")
        return True, None
    except Exception as e:
        print(f"Error sending email: {e}")
        return False, str(e)
