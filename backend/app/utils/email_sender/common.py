import requests
from typing import Optional

from ...core.config import settings


def send_html_email(recipient_email: str, subject: str, html_body: str) -> bool:
    """
    Отправка HTML-писем через Mailgun API.
    Если Mailgun не настроен или не работает — fallback на SMTP.
    """
    # Проверяем наличие Mailgun настроек
    if settings.MAILGUN_API_KEY and settings.MAILGUN_DOMAIN:
        result = _send_via_mailgun(recipient_email, subject, html_body)
        if result:
            return True
        # Fallback на SMTP если Mailgun не сработал
        print("Mailgun failed, falling back to SMTP...")
        return _send_via_smtp(recipient_email, subject, html_body)
    else:
        # SMTP если Mailgun не настроен
        return _send_via_smtp(recipient_email, subject, html_body)


def _send_via_mailgun(recipient_email: str, subject: str, html_body: str) -> bool:
    """
    Отправка через Mailgun HTTP API.
    """
    # Выбираем API endpoint в зависимости от региона
    if settings.MAILGUN_REGION.upper() == "EU":
        api_base = "https://api.eu.mailgun.net/v3"
    else:
        api_base = "https://api.mailgun.net/v3"

    url = f"{api_base}/{settings.MAILGUN_DOMAIN}/messages"

    text_body = "If you see this text, your email client does not support HTML."

    data = {
        "from": settings.EMAIL_SENDER,
        "to": recipient_email,
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }

    try:
        response = requests.post(
            url,
            auth=("api", settings.MAILGUN_API_KEY),
            data=data,
            timeout=30
        )

        if response.status_code == 200:
            return True
        else:
            print(f"Mailgun error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"Mailgun request error: {repr(e)}")
        return False


def _send_via_smtp(recipient_email: str, subject: str, html_body: str) -> bool:
    """
    Fallback: SMTP-отправка HTML-писем.
    Работает с портами 25 (без TLS), 465 (SMTPS), 587 (STARTTLS).
    """
    import smtplib
    import ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.header import Header

    smtp_server = settings.EMAIL_HOST
    smtp_port = int(settings.EMAIL_PORT or 0)
    smtp_username = (getattr(settings, "EMAIL_USERNAME", "") or "").strip()
    smtp_password = (getattr(settings, "EMAIL_PASSWORD", "") or "").strip()
    sender_email = settings.EMAIL_SENDER

    if not smtp_server:
        print("SMTP error: EMAIL_HOST not configured")
        return False

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
