import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.core.config import settings


def send_html_email(recipient_email: str, subject: str, html_body: str):
    """
    Твоя оригинальная функция отправки писем.
    Без изменений — интегрирована в новую структуру.
    """
    smtp_server   = settings.EMAIL_HOST
    smtp_port     = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email  = settings.EMAIL_SENDER

    msg = MIMEMultipart()
    msg["From"]    = sender_email
    msg["To"]      = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_port != 25:
                server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            logging.info("E-mail sent to %s", recipient_email)
    except Exception as exc:
        logging.error("SMTP error while sending to %s: %s", recipient_email, exc)
        raise
