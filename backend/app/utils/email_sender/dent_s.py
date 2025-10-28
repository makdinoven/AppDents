

from .common import send_html_email
from .dent_s_courses_html import COURSES_BLOCK

# ----------------------------- PASSWORD EMAIL ------------------------------

def send_recovery_email(recipient_email: str, new_password: str, region: str):
    """Оригинальный шаблон Dent-S для восстановления пароля."""
    subject = {
        "EN": "Your New Account Password",
        "RU": "Ваш новый пароль для аккаунта",
        "IT": "La tua nuova password per l'account",
        "ES": "Tu nueva contraseña de cuenta",
        "PT": "Sua nova senha de conta",
        "AR": "كلمة المرور الجديدة لحسابك",
    }.get(region.upper(), "Your New Account Password")

    html = f"""
    <html>
      <body style="margin:0;padding:0;background-color:#edf8ff;font-family:Arial,sans-serif;">
        <table width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#edf8ff">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border-radius:12px;margin:30px 0;">
              <tr>
                <td align="center" style="padding:30px 0 20px 0;">
                  <img src="https://dent-s.com/assets/img/logo.png" alt="Dent-S" width="150" />
                </td>
              </tr>
              <tr>
                <td style="padding:20px 40px;color:#01433d;">
                  <h2 style="margin:0 0 20px 0;font-size:20px;">{subject}</h2>
                  <p style="margin:0 0 10px 0;">Dear user,</p>
                  <p style="margin:0 0 10px 0;">Your account has been successfully created.</p>
                  <p style="margin:0 0 10px 0;">Your new password is:
                    <span style="font-weight:bold;color:#01433d;">{new_password}</span>
                  </p>
                  <p style="margin:0 0 30px 0;">Please click the button below to log in:</p>
                  <p style="text-align:center;">
                    <a href="https://dent-s.com/login"
                       style="background:#01433d;color:#fff;padding:12px 28px;
                       text-decoration:none;border-radius:25px;">Log In</a>
                  </p>
                  <p style="margin:30px 0 0 0;">Best regards,<br><b>Dent-S Team</b></p>
                </td>
              </tr>
              <tr><td height="40"></td></tr>
            </table>
          </td></tr>
        </table>
      </body>
    </html>
    """

    send_html_email(recipient_email, subject, html_body=html)


# ----------------------- ABANDONED CHECKOUT EMAIL --------------------------

def send_abandoned_checkout_email(recipient_email: str, password: str, course_info: dict, region: str):
    """Оригинальный HTML шаблон Dent-S для письма с курсом."""
    subject = {
        "EN": "Your free access to our course",
        "RU": "Ваш бесплатный доступ к курсу",
        "IT": "Il tuo accesso gratuito al corso",
        "ES": "Tu acceso gratuito al curso",
        "PT": "Seu acesso gratuito ao curso",
        "AR": "وصولك المجاني إلى الدورة",
    }.get(region.upper(), "Your free access")


    html = f"""
    <html>
      <body style="margin:0;padding:0;background-color:#edf8ff;font-family:Arial,sans-serif;">
        <table width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#edf8ff">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border-radius:12px;margin:30px 0;">
              <tr><td style="padding:40px;color:#01433d;">
                <h2 style="margin:0 0 20px 0;">{subject}</h2>
                <p style="margin:0 0 10px 0;">Welcome to Dent-S! Your account has been created.</p>
                <p style="margin:0 0 10px 0;">Your password: <b>{password}</b></p>
                <p style="margin:0 0 20px 0;">You can now enjoy your free course below:</p>
                {COURSES_BLOCK.get(region.upper(), COURSES_BLOCK["EN"])}
              </td></tr>
            </table>
          </td></tr>
        </table>
      </body>
    </html>
    """

    send_html_email(recipient_email, subject, html_body=html)
