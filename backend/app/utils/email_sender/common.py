import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ...core.config import settings
from email.header import Header

# Универсальная функция SMTP-отправки
def send_html_email(recipient_email: str, subject: str, html_body: str) -> bool:
    smtp_server   = settings.EMAIL_HOST               # 172.18.0.1
    smtp_port     = int(settings.EMAIL_PORT or 0)     # может быть строкой
    smtp_username = (settings.EMAIL_USERNAME or "").strip()
    smtp_password = (settings.EMAIL_PASSWORD or "").strip()
    sender_email  = settings.EMAIL_SENDER

    # plain-text альтернатива для лучшей доставляемости
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
            # SMTPS (implicit TLS) — НИКАКОГО starttls()
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15, context=ctx) as s:
                if smtp_username and smtp_password:
                    s.login(smtp_username, smtp_password)
                s.sendmail(sender_email, [recipient_email], msg.as_string())

        elif smtp_port == 587:
            # Submission — STARTTLS обязателен
            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as s:
                s.ehlo()
                s.starttls(context=ctx)
                s.ehlo()
                if smtp_username and smtp_password:
                    s.login(smtp_username, smtp_password)
                s.sendmail(sender_email, [recipient_email], msg.as_string())

        else:
            # 25 — обычно без TLS/логина (локальный relay)
            with smtplib.SMTP(smtp_server, smtp_port or 25, timeout=15) as s:
                if smtp_username and smtp_password:
                    s.login(smtp_username, smtp_password)
                s.sendmail(sender_email, [recipient_email], msg.as_string())

        return True

    except Exception as e:
        # замените на logger.exception(...) при наличии логгера
        print("SMTP error:", repr(e))
        return False


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


def send_successful_purchase_email(
    recipient_email: str,
    course_names: list[str] | None = None,
    new_account: bool = False,
    password: str | None = None,
    region: str = "EN",
    book_titles: list[str] | None = None,
):
    subject_map = {
        "EN": "Purchase Confirmation — Items added to your account",
        "RU": "Подтверждение покупки — элементы добавлены в аккаунт",
        "IT": "Conferma di acquisto — elementi aggiunti all'account",
        "ES": "Confirmación de compra — elementos añadidos a su cuenta",
    }
    subject = subject_map.get(region.upper(), subject_map["EN"])

    courses_str = ", ".join(course_names or [])
    books_str = ", ".join(book_titles or [])

    loc = {
        "EN": {
            "heading_new": "Welcome and congratulations!",
            "heading_default": "Purchase confirmation",
            "courses": "Courses",
            "books": "Books",
            "purchased_courses": "You have purchased the following course(s):",
            "purchased_books": "You have purchased the following book(s):",
            "account_created": "We have created a new account for you:",
            "email": "Email",
            "password": "Temporary password",
            "login": "Log In",
        },
        "RU": {
            "heading_new": "Добро пожаловать и поздравляем!",
            "heading_default": "Подтверждение покупки",
            "courses": "Курсы",
            "books": "Книги",
            "purchased_courses": "Вы приобрели следующие курс(ы):",
            "purchased_books": "Вы приобрели следующие книгу(и):",
            "account_created": "Мы создали для вас новый аккаунт:",
            "email": "Email",
            "password": "Временный пароль",
            "login": "Войти",
        },
        "IT": {
            "heading_new": "Benvenuto e congratulazioni!",
            "heading_default": "Conferma di acquisto",
            "courses": "Corsi",
            "books": "Libri",
            "purchased_courses": "Hai acquistato i seguenti corsi:",
            "purchased_books": "Hai acquistato i seguenti libri:",
            "account_created": "Abbiamo creato per te un nuovo account:",
            "email": "Email",
            "password": "Password temporanea",
            "login": "Accedi",
        },
        "ES": {
            "heading_new": "¡Bienvenido y felicitaciones!",
            "heading_default": "Confirmación de compra",
            "courses": "Cursos",
            "books": "Libros",
            "purchased_courses": "Ha comprado los siguientes cursos:",
            "purchased_books": "Ha comprado los siguientes libros:",
            "account_created": "Hemos creado una nueva cuenta para usted:",
            "email": "Email",
            "password": "Contraseña temporal",
            "login": "Iniciar sesión",
        },
    }.get(region.upper(), {
        "heading_new": "Welcome and congratulations!",
        "heading_default": "Purchase confirmation",
        "courses": "Courses",
        "books": "Books",
        "purchased_courses": "You have purchased the following course(s):",
        "purchased_books": "You have purchased the following book(s):",
        "account_created": "We have created a new account for you:",
        "email": "Email",
        "password": "Temporary password",
        "login": "Log In",
    })

    account_block = ""
    if new_account:
        account_block = f"""
        <div style=\"margin-top:12px;\">\n
          <p>{loc["account_created"]}</p>
          <p><b>{loc["email"]}:</b> {recipient_email}</p>
          <p><b>{loc["password"]}:</b> {password or ""}</p>
        </div>
        """

    courses_block = ""
    if courses_str:
        courses_block = f"""
        <div style=\"margin-top:12px;\">\n
          <h3 style=\"margin:0 0 6px;\">{loc["courses"]}</h3>
          <p style=\"margin:0;\">{loc["purchased_courses"]} <b>{courses_str}</b></p>
        </div>
        """

    books_block = ""
    if books_str:
        books_block = f"""
        <div style=\"margin-top:12px;\">\n
          <h3 style=\"margin:0 0 6px;\">{loc["books"]}</h3>
          <p style=\"margin:0;\">{loc["purchased_books"]} <b>{books_str}</b></p>
        </div>
        """

    html = f"""
    <html><body style=\"font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;\">\n
      <div style=\"max-width:600px;margin:auto;background:#fff;padding:20px;border-radius:10px;\">\n
        <h2>{loc["heading_new"] if new_account else loc["heading_default"]}</h2>
        {account_block}
        {courses_block}
        {books_block}
        <p style=\"margin-top:16px;\"><a href=\"{settings.APP_URL}/login\"
              style=\"background:#01433d;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;\">{loc["login"]}</a></p>
        <p style=\"margin-top:20px;\">Best regards,<br>Dent-S Team</p>
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
