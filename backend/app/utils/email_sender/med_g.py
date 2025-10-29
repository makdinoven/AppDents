"""
Med.G шаблоны.

"""

from .common import send_html_email
from .dent_s_courses_html import COURSES_BLOCK as BASE_COURSES_BLOCK

MED_G_DOMAIN = "https://med.g"
MED_G_COLOR = "#006d8d"


def send_recovery_email(recipient_email: str, new_password: str, region: str):
    subject = {
        "IT": "La tua nuova password per Med.G",
        "EN": "Your new Med.G password",
        "RU": "Ваш новый пароль Med.G",
        "ES": "Tu nueva contraseña Med.G",
    }.get(region.upper(), "Your new Med.G password")

    html = f"""
    <html>
      <body style="margin:0;padding:0;background-color:#f3f7f8;font-family:'Segoe UI',sans-serif;">
        <table width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#f3f7f8">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border-radius:12px;margin:30px 0;">
              <tr>
                <td align="center" style="padding:30px 0 20px 0;">
                  <img src="{MED_G_DOMAIN}/static/logo-medg.png" alt="Med.G" width="150" />
                </td>
              </tr>
              <tr>
                <td style="padding:20px 40px;color:{MED_G_COLOR};">
                  <h2 style="margin:0 0 20px 0;">{subject}</h2>
                  <p>La tua nuova password è: <b>{new_password}</b></p>
                  <p>Accedi cliccando il pulsante qui sotto:</p>
                  <p style="text-align:center;margin:30px 0;">
                    <a href="{MED_G_DOMAIN}/login"
                       style="background:{MED_G_COLOR};color:#fff;padding:12px 28px;
                       text-decoration:none;border-radius:25px;">Accedi</a>
                  </p>
                  <p>Distinti saluti,<br><b>Med.G Team</b></p>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
      </body>
    </html>
    """
    send_html_email(recipient_email, subject, html_body=html)


def send_abandoned_checkout_email(recipient_email: str, password: str, course_info: dict, region: str):
    subject = {
        "IT": "Accesso gratuito al corso Med.G",
        "EN": "Your free Med.G course access",
        "RU": "Бесплатный доступ к курсу Med.G",
        "ES": "Acceso gratuito al curso Med.G",
    }.get(region.upper(), "Accesso gratuito")

    # Используем тот же блок курсов, просто домен заменяем
    block = BASE_COURSES_BLOCK.get(region.upper(), BASE_COURSES_BLOCK["EN"]).replace("https://dent-s.com", MED_G_DOMAIN)

    html = f"""
    <html>
      <body style="margin:0;padding:0;background-color:#f3f7f8;font-family:'Segoe UI',sans-serif;">
        <table width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#f3f7f8">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border-radius:12px;margin:30px 0;">
              <tr><td style="padding:40px;color:{MED_G_COLOR};">
                <h2 style="margin:0 0 20px 0;">{subject}</h2>
                <p>La tua password: <b>{password}</b></p>
                <p>Accedi e inizia il corso gratuito:</p>
                {block}
              </td></tr>
            </table>
          </td></tr>
        </table>
      </body>
    </html>
    """
    send_html_email(recipient_email, subject, html_body=html)
