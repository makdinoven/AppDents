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

def send_successful_purchase_email(
    recipient_email: str,
    course_names: list[str],
    new_account: bool = False,
    password: str = None,
    region: str = "EN"
):
    """
    Отправляет письмо с подтверждением успешной покупки курса(ов).
    Если new_account=True, письмо содержит данные о новом аккаунте и временный пароль.
    Параметр `region` указывает язык ("RU", "EN", "ES").
    course_names: список названий курсов.
    """

    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email = settings.EMAIL_SENDER

    # Контактный email и URL для кнопки
    contact_email = "info.dis.org@gmail.com"
    login_url = "https://dent-s.com/login"

    # Преобразуем список названий курсов в одну строку
    courses_str = ", ".join(course_names) if course_names else "No course name"

    # Выбираем язык письма
    if region == "RU":
        subject = "Подтверждение покупки — ваш курс добавлен"
        if new_account:
            body_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <title>Подтверждение покупки</title>
              <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{
                  background-color: #fff; padding: 20px; border-radius: 8px; 
                  box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
                }}
                h2 {{ color: #333; }}
                p {{ font-size: 16px; line-height: 1.5; color: #555; }}
                .password {{ font-size: 18px; font-weight: bold; color: #d9534f; }}
                .btn {{
                  display: inline-block; padding: 10px 20px; margin-top: 20px;
                  background-color: #28a745; color: #fff; text-decoration: none; border-radius: 5px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <h2>Добро пожаловать и поздравляем!</h2>
                <p>Вы успешно приобрели курс(ы): <strong>{courses_str}</strong>.</p>
                <p>Для вас создан новый аккаунт.</p>
                <p><strong>Email:</strong> {recipient_email}</p>
                <p><strong>Пароль:</strong> <span class="password">{password}</span></p>
                <p>Пожалуйста, перейдите по кнопке ниже, чтобы войти:</p>
                <a href="{login_url}" class="btn">Войти</a>
<a href="https://dent-s.com/" class="btn" style="background-color: #007bff; margin-left: 10px;">Больше курсов здесь</a>
                <p>Спасибо за покупку!</p>
                
                <p>Если у вас возникнут вопросы, напишите на <strong>{contact_email}</strong>.</p>
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
              <title>Подтверждение покупки</title>
              <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{
                  background-color: #fff; padding: 20px; border-radius: 8px;
                  box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
                }}
                h2 {{ color: #333; }}
                p {{ font-size: 16px; line-height: 1.5; color: #555; }}
                .btn {{
                  display: inline-block; padding: 10px 20px; margin-top: 20px;
                  background-color: #28a745; color: #fff; text-decoration: none; border-radius: 5px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <h2>Подтверждение покупки</h2>
                <p>Вы успешно приобрели курс(ы): <strong>{courses_str}</strong>.</p>
                <p>Они добавлены в ваш аккаунт.</p>
                <p>Пожалуйста, перейдите по кнопке ниже, чтобы войти:</p>
                <a href="{login_url}" class="btn">Войти</a>
                <a href="https://dent-s.com/" class="btn" style="background-color: #007bff; margin-left: 10px;">Больше курсов здесь</a>
                <p>Спасибо за покупку!</p>
                <p>Если у вас возникнут вопросы, напишите на <strong>{contact_email}</strong>.</p>
              </div>
            </body>
            </html>
            """

    elif region == "ES":
        subject = "Confirmación de compra — su curso ha sido agregado"
        if new_account:
            body_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <title>Confirmación de compra</title>
              <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{
                  background-color: #fff; padding: 20px; border-radius: 8px;
                  box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
                }}
                h2 {{ color: #333; }}
                p {{ font-size: 16px; line-height: 1.5; color: #555; }}
                .password {{ font-size: 18px; font-weight: bold; color: #d9534f; }}
                .btn {{
                  display: inline-block; padding: 10px 20px; margin-top: 20px;
                  background-color: #28a745; color: #fff; text-decoration: none; border-radius: 5px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <h2>¡Bienvenido y felicitaciones!</h2>
                <p>Ha comprado con éxito el/los curso(s): <strong>{courses_str}</strong>.</p>
                <p>Se ha creado una nueva cuenta para usted.</p>
                <p><strong>Email:</strong> {recipient_email}</p>
                <p><strong>Contraseña temporal:</strong> <span class="password">{password}</span></p>
                <p>Use el botón a continuación para iniciar sesión:</p>
                <a href="{login_url}" class="btn">Iniciar sesión</a>
                <a href="https://dent-s.com/" class="btn" style="background-color: #007bff; margin-left: 10px;">Más cursos aquí</a>
                <p>¡Gracias por su compra!</p>
                <p>Si tiene alguna pregunta, escriba a <strong>{contact_email}</strong>.</p>
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
              <title>Confirmación de compra</title>
              <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{
                  background-color: #fff; padding: 20px; border-radius: 8px;
                  box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
                }}
                h2 {{ color: #333; }}
                p {{ font-size: 16px; line-height: 1.5; color: #555; }}
                .btn {{
                  display: inline-block; padding: 10px 20px; margin-top: 20px;
                  background-color: #28a745; color: #fff; text-decoration: none; border-radius: 5px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <h2>Confirmación de compra</h2>
                <p>Ha comprado con éxito el/los curso(s): <strong>{courses_str}</strong>.</p>
                <p>Se han agregado a su cuenta.</p>
                <p>Use el botón a continuación para iniciar sesión:</p>
                <a href="{login_url}" class="btn">Iniciar sesión</a>
                <a href="https://dent-s.com/" class="btn" style="background-color: #007bff; margin-left: 10px;">Más cursos aquí</a>
                <p>¡Gracias por su compra!</p>
                <p>Si tiene alguna pregunta, escriba a <strong>{contact_email}</strong>.</p>
              </div>
            </body>
            </html>
            """

    else:
        # По умолчанию - английский
        subject = "Purchase Confirmation - Your Course(s) Has Been Added"
        if new_account:
            body_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <title>Purchase Confirmation</title>
              <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{
                  background-color: #fff; padding: 20px; border-radius: 8px;
                  box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
                }}
                h2 {{ color: #333; }}
                p {{ font-size: 16px; line-height: 1.5; color: #555; }}
                .password {{ font-size: 18px; font-weight: bold; color: #d9534f; }}
                .btn {{
                  display: inline-block; padding: 10px 20px; margin-top: 20px;
                  background-color: #28a745; color: #fff; text-decoration: none; border-radius: 5px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <h2>Welcome and Congratulations!</h2>
                <p>You have successfully purchased the following course(s): <strong>{courses_str}</strong>.</p>
                <p>We have created a new account for you.</p>
                <p><strong>Email:</strong> {recipient_email}</p>
                <p><strong>Temporary Password:</strong> <span class="password">{password}</span></p>
                <p>Please use the button below to log in:</p>
                <a href="{login_url}" class="btn">Log In</a>
                <a href="https://dent-s.com/" class="btn" style="background-color: #007bff; margin-left: 10px;">More courses here</a>
                <p>Thank you for your purchase!</p>
                <p>If you have any questions, contact us at <strong>{contact_email}</strong>.</p>
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
                .container {{
                  background-color: #fff; padding: 20px; border-radius: 8px;
                  box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
                }}
                h2 {{ color: #333; }}
                p {{ font-size: 16px; line-height: 1.5; color: #555; }}
                .btn {{
                  display: inline-block; padding: 10px 20px; margin-top: 20px;
                  background-color: #28a745; color: #fff; text-decoration: none; border-radius: 5px;
                }}
              </style>
            </head>
            <body>
              <div class="container">
                <h2>Purchase Confirmation</h2>
                <p>You have successfully purchased the following course(s): <strong>{courses_str}</strong>.</p>
                <p>They have been added to your account.</p>
                <p>Please use the button below to log in:</p>
                <a href="{login_url}" class="btn">Log In</a>
                <a href="https://dent-s.com/" class="btn" style="background-color: #007bff; margin-left: 10px;">More courses here</a>
                <p>Thank you for your purchase!</p>
                <p>If you have any questions, contact us at <strong>{contact_email}</strong>.</p>
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

def send_failed_purchase_email(
    recipient_email: str,
    course_names: list[str],
    region: str = "EN"
):
    """
    Отправляет письмо об ошибке при оплате, с учётом локализации.
    course_names: список названий курсов, которые пытались купить.
    """

    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email = settings.EMAIL_SENDER

    contact_email = "info.dis.org@gmail.com"
    # Можно добавить ссылку на повторную оплату или просто на сайт

    courses_str = ", ".join(course_names) if course_names else "No course name"

    if region == "RU":
        subject = "Ошибка оплаты"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Ошибка оплаты</title>
          <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{
              background-color: #fff; padding: 20px; border-radius: 8px;
              box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
            }}
            h2 {{ color: #333; }}
            p {{ font-size: 16px; line-height: 1.5; color: #555; }}
            .btn {{
              display: inline-block; padding: 10px 20px; margin-top: 20px;
              background-color: #dc3545; color: #fff; text-decoration: none; border-radius: 5px;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Ошибка оплаты</h2>
            <p>К сожалению, ваша оплата за курс(ы): <strong>{courses_str}</strong> не прошла.</p>
            <p>Пожалуйста, попробуйте ещё раз или свяжитесь со службой поддержки.</p>
            <p>Если у вас возникнут вопросы, напишите на <strong>{contact_email}</strong>.</p>
          </div>
        </body>
        </html>
        """
    elif region == "ES":
        subject = "Error de pago"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Error de pago</title>
          <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{
              background-color: #fff; padding: 20px; border-radius: 8px;
              box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
            }}
            h2 {{ color: #333; }}
            p {{ font-size: 16px; line-height: 1.5; color: #555; }}
            .btn {{
              display: inline-block; padding: 10px 20px; margin-top: 20px;
              background-color: #dc3545; color: #fff; text-decoration: none; border-radius: 5px;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Error de pago</h2>
            <p>Lamentablemente, su pago por el/los curso(s): <strong>{courses_str}</strong> no se realizó correctamente.</p>
            <p>Por favor, inténtelo de nuevo o póngase en contacto con el soporte.</p>
            <p>Si tiene alguna pregunta, escriba a <strong>{contact_email}</strong>.</p>
          </div>
        </body>
        </html>
        """
    else:
        subject = "Payment Failed"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Payment Failed</title>
          <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{
              background-color: #fff; padding: 20px; border-radius: 8px;
              box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
            }}
            h2 {{ color: #333; }}
            p {{ font-size: 16px; line-height: 1.5; color: #555; }}
            .btn {{
              display: inline-block; padding: 10px 20px; margin-top: 20px;
              background-color: #dc3545; color: #fff; text-decoration: none; border-radius: 5px;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Payment Failed</h2>
            <p>Unfortunately, your payment for the following course(s): <strong>{courses_str}</strong> could not be processed.</p>
            <p>Please try again or contact support for assistance.</p>
            <p>If you have any questions, contact us at <strong>{contact_email}</strong>.</p>
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

def send_already_owned_course_email(
    recipient_email: str,
    course_names: list[str],
    region: str = "EN"
):
    """
    Отправляет письмо, уведомляющее, что пользователь оплатил курсы, которые у него уже есть.
    Предлагаем выбрать другой курс такой же стоимости, связавшись с поддержкой.
    """
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email = settings.EMAIL_SENDER

    contact_email = "info.dis.org@gmail.com"
    courses_str = ", ".join(course_names) if course_names else "No course name"

    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    if region == "RU":
        subject = "Оплаченные курсы уже есть в вашем аккаунте"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Курсы уже есть</title>
          <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{
              background-color: #fff; padding: 20px; border-radius: 8px; 
              box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
            }}
            h2 {{ color: #333; }}
            p {{ font-size: 16px; line-height: 1.5; color: #555; }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Вы уже владеете этими курсами</h2>
            <p>Вы оплатили курсы, которые у вас уже есть: <strong>{courses_str}</strong>.</p>
            <p>Если хотите заменить их на другие курсы той же стоимости, свяжитесь с нами по адресу <strong>{contact_email}</strong>.</p>
            <p>Спасибо!</p>
          </div>
        </body>
        </html>
        """
    elif region == "ES":
        subject = "Cursos ya adquiridos"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Cursos ya adquiridos</title>
          <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{
              background-color: #fff; padding: 20px; border-radius: 8px;
              box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
            }}
            h2 {{ color: #333; }}
            p {{ font-size: 16px; line-height: 1.5; color: #555; }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Usted ya posee estos cursos</h2>
            <p>Ha pagado por los cursos que ya tenía: <strong>{courses_str}</strong>.</p>
            <p>Si desea reemplazarlos por otros cursos del mismo valor, por favor contáctenos en <strong>{contact_email}</strong>.</p>
            <p>¡Gracias!</p>
          </div>
        </body>
        </html>
        """
    else:
        subject = "You Already Own These Courses"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Already Owned Courses</title>
          <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{
              background-color: #fff; padding: 20px; border-radius: 8px; 
              box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; margin: auto;
            }}
            h2 {{ color: #333; }}
            p {{ font-size: 16px; line-height: 1.5; color: #555; }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>You Already Own These Courses</h2>
            <p>You have paid for the following course(s), which you already own: <strong>{courses_str}</strong>.</p>
            <p>If you would like to exchange them for another course of the same price, please contact us at <strong>{contact_email}</strong>.</p>
            <p>Thank you!</p>
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
        print(f"Error sending already-owned-course email: {e}")