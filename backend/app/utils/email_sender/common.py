import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from ...core.config import settings


def send_html_email(recipient_email: str, subject: str, html_body: str) -> bool:
    """
    Универсальная SMTP-отправка HTML-писем.
    Работает с портами 25 (без TLS), 465 (SMTPS), 587 (STARTTLS).
    """
    smtp_server   = settings.EMAIL_HOST
    smtp_port     = int(settings.EMAIL_PORT or 0)
    smtp_username = (getattr(settings, "EMAIL_USERNAME", "") or "").strip()
    smtp_password = (getattr(settings, "EMAIL_PASSWORD", "") or "").strip()
    sender_email  = settings.EMAIL_SENDER

    text_body = "If you see this text, your email client does not support HTML."

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = Header(subject, "utf-8")
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    ctx = ssl.create_default_context()

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15, context=ctx) as s:
                if smtp_username and smtp_password:
                    s.login(smtp_username, smtp_password)
                s.sendmail(sender_email, [recipient_email], msg.as_string())

        elif smtp_port == 587:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as s:
                s.ehlo()
                s.starttls(context=ctx)
                s.ehlo()
                if smtp_username and smtp_password:
                    s.login(smtp_username, smtp_password)
                s.sendmail(sender_email, [recipient_email], msg.as_string())

        else:
            with smtplib.SMTP(smtp_server, smtp_port or 25, timeout=15) as s:
                if smtp_username and smtp_password:
                    s.login(smtp_username, smtp_password)
                s.sendmail(sender_email, [recipient_email], msg.as_string())

        return True

    except Exception as e:
        print("SMTP error:", repr(e))
        return False
