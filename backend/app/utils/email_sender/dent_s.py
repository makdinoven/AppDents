"""
Шаблоны Dent-S
"""
from .common import send_html_email
from .dent_s_courses_html import COURSES_BLOCK
from ...core.config import settings


def send_password_to_user(recipient_email: str, password: str, region: str):
    """Письмо с новым паролем при регистрации."""
    subject = {
        "EN": "Your New Account Password",
        "RU": "Ваш новый пароль для аккаунта",
        "IT": "La tua nuova password per l'account",
        "ES": "Tu nueva contraseña de cuenta",
    }.get(region.upper(), "Your New Account Password")

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#edf8ff;">
      <div style="max-width:600px;margin:auto;background:white;padding:20px;border-radius:12px;">
        <img src="https://dent-s.com/assets/img/logo.png" alt="Dent-S" width="150" />
        <h2>{subject}</h2>
        <p>Your new password: <b>{password}</b></p>
        <p><a href="https://dent-s.com/login"
               style="background:#01433d;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;">
               Log In</a></p>
        <p>Best regards,<br><b>Dent-S Team</b></p>
      </div>
    </body></html>
    """
    send_html_email(recipient_email, subject, html)


def send_recovery_email(recipient_email: str, new_password: str, region: str):
    """Восстановление пароля."""
    send_password_to_user(recipient_email, new_password, region)


def send_successful_purchase_email(
    recipient_email: str,
    course_names: list[str] | None = None,
    new_account: bool = False,
    password: str | None = None,
    region: str = "EN",
    book_titles: list[str] | None = None,
):
    """Письмо при успешной покупке: курсы и/или книги."""
    subject = {
        "EN": "Purchase Confirmation — Items added to your account",
        "RU": "Подтверждение покупки — элементы добавлены в аккаунт",
        "IT": "Conferma di acquisto — elementi aggiunti all'account",
        "ES": "Confirmación de compra — elementos añadidos a su cuenta",
    }.get(region.upper(), "Purchase Confirmation")

    courses_str = ", ".join(course_names or [])
    books_str = ", ".join(book_titles or [])

    login_url = "https://dent-s.com/login"
    labels = {
        "EN": {"courses": "Courses", "books": "Books", "login": "Log In",
                "purchased_courses": "You have purchased:", "purchased_books": "You have purchased:"},
        "RU": {"courses": "Курсы", "books": "Книги", "login": "Войти",
                "purchased_courses": "Вы приобрели:", "purchased_books": "Вы приобрели:"},
        "IT": {"courses": "Corsi", "books": "Libri", "login": "Accedi",
                "purchased_courses": "Hai acquistato:", "purchased_books": "Hai acquistato:"},
        "ES": {"courses": "Cursos", "books": "Libros", "login": "Iniciar sesión",
                "purchased_courses": "Ha comprado:", "purchased_books": "Ha comprado:"},
    }.get(region.upper(), {"courses": "Courses", "books": "Books", "login": "Log In",
                           "purchased_courses": "You have purchased:", "purchased_books": "You have purchased:"})

    account_block = ""
    if new_account:
        account_block = f"""
        <div style=\"margin-top:12px;\">
          <p><b>Email:</b> {recipient_email}</p>
          <p><b>Password:</b> {password or ''}</p>
        </div>
        """

    sections = []
    if courses_str:
        sections.append(f"<h3 style=\"margin:16px 0 6px;\">{labels['courses']}</h3><p>{labels['purchased_courses']} <b>{courses_str}</b></p>")
    if books_str:
        sections.append(f"<h3 style=\"margin:16px 0 6px;\">{labels['books']}</h3><p>{labels['purchased_books']} <b>{books_str}</b></p>")
    body_sections = "".join(sections)

    html = f"""
    <html><body style=\"font-family:Arial,sans-serif;background:#edf8ff;\">\n
      <div style=\"max-width:600px;margin:auto;background:white;padding:20px;border-radius:12px;\">\n
        <img src=\"https://dent-s.com/assets/img/logo.png\" alt=\"Dent-S\" width=\"150\" />
        <h2>{subject}</h2>
        {account_block}
        {body_sections}
        <p><a href=\"{login_url}\" style=\"background:#01433d;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;\">{labels['login']}</a></p>
        <p>Best regards,<br><b>Dent-S Team</b></p>
      </div>
    </body></html>
    """
    send_html_email(recipient_email, subject, html)


def send_failed_purchase_email(recipient_email: str, course_info: dict, region: str):
    """Письмо при неудачной оплате."""
    subject = {
        "EN": "Payment failed",
        "RU": "Оплата не прошла",
        "IT": "Pagamento fallito",
        "ES": "Pago fallido",
    }.get(region.upper(), "Payment failed")

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#edf8ff;">
      <div style="max-width:600px;margin:auto;background:white;padding:20px;border-radius:12px;">
        <img src="https://dent-s.com/assets/img/logo.png" alt="Dent-S" width="150" />
        <h2>{subject}</h2>
        <p>Unfortunately, your payment could not be completed.</p>
        <p>Please try again or contact support.</p>
        <p><a href="https://dent-s.com/courses"
              style="background:#01433d;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;">Try Again</a></p>
      </div>
    </body></html>
    """
    send_html_email(recipient_email, subject, html)


def send_already_owned_course_email(recipient_email: str, course_info: dict, region: str):
    """Письмо если пользователь уже купил курс."""
    subject = {
        "EN": "You already have this course",
        "RU": "Этот курс уже у вас",
        "IT": "Hai già questo corso",
        "ES": "Ya tienes este curso",
    }.get(region.upper(), "You already have this course")

    title = course_info.get("title", "Course")
    url = course_info.get("url", "https://dent-s.com/login")

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#edf8ff;">
      <div style="max-width:600px;margin:auto;background:white;padding:20px;border-radius:12px;">
        <img src="https://dent-s.com/assets/img/logo.png" alt="Dent-S" width="150" />
        <h2>{subject}</h2>
        <p>You already have access to this course: <b>{title}</b></p>
        <a href="{url}" style="background:#01433d;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;">Go to Course</a>
      </div>
    </body></html>
    """
    send_html_email(recipient_email, subject, html)


def send_abandoned_checkout_email(recipient_email: str, password: str, course_info: dict, region: str):
    """Письмо пользователю, бросившему корзину."""
    subject = {
        "EN": "Your free access to our course",
        "RU": "Ваш бесплатный доступ к курсу",
        "IT": "Il tuo accesso gratuito al corso",
        "ES": "Tu acceso gratuito al curso",
    }.get(region.upper(), "Your free access")

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#edf8ff;">
      <div style="max-width:600px;margin:auto;background:white;padding:20px;border-radius:12px;">
        <img src="https://dent-s.com/assets/img/logo.png" alt="Dent-S" width="150" />
        <h2>{subject}</h2>
        <p>Your password: <b>{password}</b></p>
        <p>Enjoy your free course below:</p>
        {COURSES_BLOCK.get(region.upper(), COURSES_BLOCK["EN"])}
      </div>
    </body></html>
    """
    send_html_email(recipient_email, subject, html)
