import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ...core.config import settings


# Универсальная функция SMTP-отправки
def send_html_email(recipient_email: str, subject: str, html_body: str):
    smtp_server   = settings.EMAIL_HOST
    smtp_port     = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email  = settings.EMAIL_SENDER

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Не включаем TLS, если сервер локальный тестовый (aiosmtpd)
            if smtp_port not in (25, 1025):
                try:
                    server.starttls()
                except smtplib.SMTPNotSupportedError:
                    pass
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            logging.info("📨 Email sent to %s", recipient_email)
    except Exception as e:
        logging.error("SMTP error while sending to %s: %s", recipient_email, e)
        raise


# Универсальное письмо с паролем
def send_password_to_user(recipient_email: str, password: str, region: str):
    subject = {
        "EN": "Your New Account Password",
        "RU": "Ваш новый пароль для аккаунта",
        "IT": "La tua nuova password",
        "ES": "Tu nueva contraseña",
    }.get(region.upper(), "Your New Account Password")

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
      <div style="max-width:600px;margin:auto;background:#fff;padding:20px;border-radius:10px;">
        <h2>{subject}</h2>
        <p>Your new password: <b>{password}</b></p>
        <a href="{settings.APP_URL}/login"
           style="background:#01433d;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;">
           Log In
        </a>
        <p style="margin-top:20px;">Best regards,<br>Dent-S Team</p>
      </div>
    </body></html>
    """
    send_html_email(recipient_email, subject, html)


def send_successful_purchase_email(recipient_email: str, course_info: dict, region: str):
    subject = {
        "EN": "Your course is available!",
        "RU": "Ваш курс доступен!",
        "IT": "Il tuo corso è disponibile!",
        "ES": "¡Tu curso ya está disponible!",
    }.get(region.upper(), "Your course is available!")

    title = course_info.get("title", "Course")
    url = course_info.get("url", settings.APP_URL)

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
      <div style="max-width:600px;margin:auto;background:#fff;padding:20px;border-radius:10px;">
        <h2>{subject}</h2>
        <p>Thank you for your purchase! You can access your course:</p>
        <p><a href="{url}" style="background:#01433d;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;">
          Open Course</a></p>
        <p>Best regards,<br>Dent-S Team</p>
      </div>
    </body></html>
    """
    send_html_email(recipient_email, subject, html)


def send_failed_purchase_email(recipient_email: str, region: str):
    subject = {
        "EN": "Payment failed",
        "RU": "Оплата не прошла",
        "IT": "Pagamento fallito",
        "ES": "Pago fallido",
    }.get(region.upper(), "Payment failed")

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
      <div style="max-width:600px;margin:auto;background:#fff;padding:20px;border-radius:10px;">
        <h2>{subject}</h2>
        <p>Unfortunately, your payment could not be completed.</p>
        <p>Please try again or contact support.</p>
      </div>
    </body></html>
    """
    send_html_email(recipient_email, subject, html)
