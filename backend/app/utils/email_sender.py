import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..core.config import settings

def send_password_to_user(recipient_email: str, password: str):
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email = settings.EMAIL_SENDER

    subject = "Your New Account Password"


    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Your New Password</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          background-color: #f4f4f4;
          color: #333;
          padding: 20px;
        }}
        .container {{
          background-color: #fff;
          padding: 20px;
          border-radius: 5px;
          box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .password {{
          font-size: 1.5em;
          color: #e74c3c;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Your New Account Password</h2>
        <p>Dear User,</p>
        <p>Your account has been successfully created.</p>
        <p>Your new password is: <span class="password">{password}</span></p>
        
        <p>Best regards</p>
      </div>
    </body>
    </html>
    """

    # Создаем MIME-сообщение
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Если Postfix поддерживает STARTTLS и вы хотите его использовать,
            # можно вызвать server.starttls() после подключения.
            # Если не требуется, оставьте как есть.
            if smtp_port != 25:
                server.starttls()
            # Если аутентификация не требуется, можно пропустить login()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        print("Error sending email:", e)

def send_recovery_email(recipient_email: str, new_password: str):
    """
    Отправляет письмо с инструкциями по восстановлению пароля.

    """
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email = settings.EMAIL_SENDER

    subject = "Password Recovery Instructions"

    # HTML-содержимое письма для восстановления пароля
    body_html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Password Recovery</title>
        <style>
          body {{
            font-family: 'Arial', sans-serif;
            background-color: #f0f0f0;
            padding: 20px;
          }}
          .email-container {{
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            margin: auto;
          }}
          h2 {{
            color: #333;
          }}
          p {{
            font-size: 16px;
            line-height: 1.5;
            color: #555;
          }}
          .password {{
            font-size: 18px;
            font-weight: bold;
            color: #d9534f;
          }}
          .footer {{
            font-size: 12px;
            color: #888;
            text-align: center;
            margin-top: 20px;
          }}
        </style>
      </head>
      <body>
        <div class="email-container">
          <h2>Password Recovery Request</h2>
          <p>Dear User,</p>
          <p>We have received a request to reset your password.</p>
          <p>Your new password is:</p>
          <p class="password">{new_password}</p>
          <p>If you did not request a password reset, please contact our support team immediately.</p>
        </div>
        <div class="footer">
          <p>This is an automated message. Please do not reply to this email.</p>
        </div>
      </body>
    </html>
    """

    # Формирование MIME-сообщения
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Если Postfix поддерживает STARTTLS и вы хотите его использовать,
            # можно вызвать server.starttls() после подключения.
            # Если не требуется, оставьте как есть.
            if smtp_port != 25:
                server.starttls()
            # Если аутентификация не требуется, можно пропустить login()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        # Логирование ошибки или другая обработка
        print("Error sending recovery email:", e)

def send_successful_purchase_email(recipient_email: str, course_id: int, new_account: bool = False, password: str = None):
    """
    Отправляет письмо с подтверждением успешной покупки курса.
    Если new_account=True, письмо содержит данные о новом аккаунте и временный пароль.
    """
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email = settings.EMAIL_SENDER

    subject = "Purchase Confirmation - Your Course Has Been Added"

    if new_account:
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Purchase Confirmation</title>
          <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }}
            h2 {{ color: #333; }}
            p {{ font-size: 16px; line-height: 1.5; color: #555; }}
            .password {{ font-size: 18px; font-weight: bold; color: #d9534f; }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Welcome and Congratulations!</h2>
            <p>Your purchase was successful, and we have created a new account for you.</p>
            <p><strong>Email:</strong> {recipient_email}</p>
            <p><strong>Temporary Password:</strong> <span class="password">{password}</span></p>
            <p>Please log in with these credentials.</p>
            <p>Thank you for your purchase!</p>
          </div>
        </body>
        </html>
        """
    else:
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Purchase Confirmation</title>
          <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }}
            h2 {{ color: #333; }}
            p {{ font-size: 16px; line-height: 1.5; color: #555; }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Purchase Confirmation</h2>
            <p>Your purchase was successful.</p>
            <p>The course (ID: {course_id}) has been added to your account.</p>
            <p>Thank you for your purchase!</p>
          </div>
        </body>
        </html>
        """
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Если Postfix поддерживает STARTTLS и вы хотите его использовать,
            # можно вызвать server.starttls() после подключения.
            # Если не требуется, оставьте как есть.
            if smtp_port != 25:
                server.starttls()
            # Если аутентификация не требуется, можно пропустить login()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        print("Error sending purchase confirmation email:", e)

def send_failed_purchase_email(recipient_email: str, course_id: int = None):
    """
    Отправляет письмо об ошибке при оплате.
    """
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email = settings.EMAIL_SENDER

    subject = "Payment Failed"
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Payment Failed</title>
      <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{ background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }}
        h2 {{ color: #333; }}
        p {{ font-size: 16px; line-height: 1.5; color: #555; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>Payment Failed</h2>
        <p>Unfortunately, your payment could not be processed.</p>
        {"<p>Course ID: " + str(course_id) + "</p>" if course_id else ""}
        <p>Please try again or contact support for assistance.</p>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Если Postfix поддерживает STARTTLS и вы хотите его использовать,
            # можно вызвать server.starttls() после подключения.
            # Если не требуется, оставьте как есть.
            if smtp_port != 25:
                server.starttls()
            # Если аутентификация не требуется, можно пропустить login()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        print("Error sending payment failed email:", e)