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


def send_successful_purchase_email(recipient_email: str, course_info: dict, region: str):
    """Письмо при успешной покупке курса."""
    title = course_info.get("title", "Your course")
    url = course_info.get("url", "https://dent-s.com/login")
    subject = {
        "EN": "Your course is available!",
        "RU": "Ваш курс теперь доступен!",
        "IT": "Il tuo corso è disponibile!",
        "ES": "¡Tu curso ya está disponible!",
    }.get(region.upper(), "Your course is available!")

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#edf8ff;">
      <div style="max-width:600px;margin:auto;background:white;padding:20px;border-radius:12px;">
        <img src="https://dent-s.com/assets/img/logo.png" alt="Dent-S" width="150" />
        <h2>{subject}</h2>
        <p>Thank you for your purchase! You can access your course:</p>
        <a href="{url}" style="background:#01433d;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;">Open Course</a>
        <p style="margin-top:20px;">Course: <b>{title}</b></p>
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
