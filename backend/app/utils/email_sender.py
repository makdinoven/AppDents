import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..core.config import settings

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


courses_block: dict[str, str | None] = {
    "EN": """
        <tr>
              <td
                style="
                  font-size: 12px;
                  line-height: 16px;
                  font-weight: 500;
                  border-radius: 20px;
                  padding: 5px;
                  border: 1px solid rgba(100, 116, 139, 0.2);
                "
              >
                <table
                  style="width: 100%; color: #01433d"
                  cellpadding="0"
                  cellspacing="5px"
                >
                  <tr style="width: 100%">
                    <td valign="top">
                      <a
                        href="https://dent-s.com/client/course/occlusiontmj-2"
                        style="
                          text-decoration: none;
                          color: #01433d;
                          display: block;
                          height: 100%;
                        "
                      >
                        <div
                          style="
                            border-radius: 20px;
                            background-color: #7fdfd5;
                            padding: 10px;
                          "
                        >
                          <p
                            style="text-transform: uppercase; margin: 0 0 5px 0"
                            align="left"
                          >
                            gnathology
                          </p>
                          <p style="margin: 0 0 5px 0" align="left">
                            <strong>$19</strong>
                            <span
                              style="
                                text-decoration: line-through;
                                color: #017f74;
                              "
                              >$883</span
                            >
                            <span
                              style="
                                background-color: transparent;
                                color: #017f74;
                                padding: 4px 4px;
                                border-radius: 20px;
                                border: 1px solid #017f74;
                              "
                              >33 lessons</span
                            >
                          </p>
                          <h4 style="margin: 0 0 5px 0" align="left">
                            Occlusion, TMJ Dysfunctions And Orofacial Pain From
                            А To Z. The Most Comprehensive Lecture Course
                          </h4>
                          <img
                            src="https://dent-s.com/assets/img/preview_img/1 (1).png"
                            alt="Course cover"
                            style="max-width: 100%; border-radius: 10px"
                          />
                        </div>
                      </a>
                    </td>
                    <td valign="top">
                      <a
                        href="https://dent-s.com/client/course/zero-bone-loss-concepts---how-to-develop-and-maintain-crestal-bone-stability"
                        style="
                          text-decoration: none;
                          color: #01433d;
                          display: block;
                        "
                      >
                        <div
                          style="
                            border-radius: 20px;
                            background-color: #79cee7;
                            padding: 10px;
                          "
                        >
                          <p
                            style="text-transform: uppercase; margin: 0 0 5px 0"
                            align="left"
                          >
                            surgery
                          </p>
                          <p style="margin: 0 0 5px 0" align="left">
                            <strong>$29</strong>
                            <span style="
                                text-decoration: line-through;
                                color: #006d8d;
                              "
                              >$500</span
                            >
                            <span
                              style="
                                background-color: transparent;
                                color: #017f74;
                                padding: 4px 4px;
                                border-radius: 20px;
                                border: 1px solid #017f74;
                              "
                              >8 lessons</span
                            >
                          </p>
                          <h4 style="margin: 0 0 5px 0" align="left">
                            Zero Bone Loss Concepts - How to develop and
                            maintain crestal bone stability
                          </h4>
                          <img
                            src="https://dent-s.com/assets/img/preview_img/30.png"
                            alt="Course cover"
                            style="max-width: 100%; border-radius: 10px"
                          />
                        </div>
                      </a>
                    </td>
                  </tr>
                  <tr style="width: 100%">
                    <td valign="top">
                      <a
                        href="https://dent-s.com/client/course/zero-bone-loss-concepts-immediate-implants"
                        style="text-decoration: none; color: #01433d"
                      >
                        <div
                          style="
                            border-radius: 20px;
                            background-color: #79cee7;
                            padding: 10px;
                          "
                        >
                          <p
                            style="text-transform: uppercase; margin: 0 0 5px 0"
                            align="left"
                          >
                            surgery
                          </p>
                          <p style="margin: 0 0 5px 0" align="left">
                            <strong>$19</strong>
                            <span
                              style="
                                text-decoration: line-through;
                                color: #006d8d;
                              "
                              >$500</span
                            >
                            <span
                              style="
                                background-color: transparent;
                                color: #017f74;
                                padding: 4px 4px;
                                border-radius: 20px;
                                border: 1px solid #017f74;
                              "
                              >8 lessons</span
                            >
                          </p>
                          <h4 style="margin: 0 0 5px 0" align="left">
                            Zero Bone Loss Concepts, Immediate implants
                          </h4>
                          <img
                            src="https://dent-s.com/assets/img/preview_img/ЗероБон.png"
                            alt="Course cover"
                            style="max-width: 100%; border-radius: 10px"
                          />
                        </div>
                      </a>
                    </td>
                    <td valign="top">
                      <a
                        href="https://dent-s.com/client/course/authors-course-ofarnaldocastellucci"
                        style="text-decoration: none; color: #01433d"
                      >
                        <div
                          style="
                            border-radius: 20px;
                            background-color: #79cee7;
                            padding: 10px;
                          "
                        >
                          <p style="text-transform: uppercase; margin: 0 0 5px 0"
                            align="left"
                          >
                            endodontics
                          </p>
                          <p style="margin: 0 0 5px 0" align="left">
                            <strong>$19</strong>
                            <span
                              style="
                                text-decoration: line-through;
                                color: #006d8d;
                              "
                              >$250</span
                            >
                            <span
                              style="
                                background-color: transparent;
                                color: #017f74;
                                padding: 4px 4px;
                                border-radius: 20px;
                                border: 1px solid #017f74;
                              "
                              >8 lessons</span
                            >
                          </p>
                          <h4 style="margin: 0 0 5px 0" align="left">
                            Author's course of Arnaldo Castellucci
                          </h4>
                          <img
                            src="https://dent-s.com/assets/img/preview_img/castellucci.png"
                            alt="Course cover"
                            style="max-width: 100%; border-radius: 10px"
                          />
                        </div>
                      </a>
                    </td>
                  </tr>
                  <tr style="width: 100%; height: auto">
                    <td valign="top" style="height: auto"></td>
                    <td valign="top" style="height: auto"></td>
                  </tr>
                  <tr>
                    <td colspan="2" align="center" style="padding: 15px 0">
                      <a
                        href="https://dent-s.com/courses"
                        style="
                          display: inline-block;
                          padding: 12px 24px;
                          background-color: #01433d;
                          color: #edf8ff;
                          text-decoration: none;
                          border-radius: 40px;
                          font-weight: 500;
                        "
                      >
                        See all
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
    """,
    # Для остальных локалей можно задать собственный HTML,
    # а пока используем English как запасной вариант
    "RU": None,
    "IT": None,
    "ES": None,
    "PT": None,
    "AR": None,
}

# --------------------------------------------------------------------------
#  HTML-карточка конкретного курса, который уже добавлен пользователю
# --------------------------------------------------------------------------
def render_course_card(course: dict[str, str | int | float]) -> str:
    """
    :param course: {
        "url": str,           # ссылка на страницу курса
        "category": str,      # gnathology / surgery / ...
        "price": str,         # «$19»
        "old_price": str,     # «$883»   (может быть пустой строкой)
        "lessons": int,       # 33
        "title": str,         # длинный заголовок
        "img": str,           # URL обложки
    }
    :return: готовый HTML-фрагмент
    """
    badge_old = (
        f"""<span style="text-decoration:line-through;color:#006d8d;">{course["old_price"]}</span>"""  # noqa: E501
        if course.get("old_price") else ""
    )
    return f"""\
<tr>
  <td style="font-size:12px;line-height:16px;font-weight:500;border-radius:20px;padding:5px;border:1px solid rgba(100,116,139,0.2);">
    <table style="width:100%;color:#01433d;" cellpadding="0" cellspacing="5px">
      <tr>
        <td valign="top">
          <a href="{course["url"]}" style="text-decoration:none;color:#01433d;display:block;">
            <div style="border-radius:20px;background-color:#7fdfd5;padding:10px;">
              <p style="text-transform:uppercase;margin:0 0 5px;" align="left">{course["category"]}</p>
              <p style="margin:0 0 5px;" align="left">
                <strong>{course["price"]}</strong>
                {badge_old}
                <span style="background-color:transparent;color:#017f74;padding:4px 4px;border-radius:20px;border:1px solid #017f74;">{course["lessons"]} lessons</span>
              </p>
              <h4 style="margin:0 0 5px;" align="left">{course["title"]}</h4>
              <img src="{course["img"]}" alt="Course cover" style="max-width:100%;border-radius:10px;">
            </div>
          </a>
          <p style="margin:6px 0 0;font-size:14px;color:#475569;" align="center">
            <em>Этот курс уже доступен в&nbsp;вашем кабинете</em>
          </p>
        </td>
      </tr>
    </table>
  </td>
</tr>
"""


def send_password_to_user(recipient_email: str, password: str, region: str):
    smtp_server   = settings.EMAIL_HOST
    smtp_port     = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email  = settings.EMAIL_SENDER
    login_url     = "https://dent-s.com/login"

    # Словарь переводов
    translations = {
        "EN": {
            "subject": "Your New Account Password",
            "heading": "Your New Account Password",
            "greeting": "Dear User,",
            "line1": "Your account has been successfully created.",
            "line2": "Your new password is: <span class=\"password\">{password}</span>",
            "line3": "Please click the button below to log in:",
            "button": "Log In",
            "closing": "Best regards"
        },
        "RU": {
            "subject": "Ваш новый пароль для аккаунта",
            "heading": "Ваш новый пароль для учётной записи",
            "greeting": "Уважаемый пользователь,",
            "line1": "Ваш аккаунт был успешно создан.",
            "line2": "Ваш новый пароль: <span class=\"password\">{password}</span>",
            "line3": "Пожалуйста, нажмите кнопку ниже, чтобы войти:",
            "button": "Войти",
            "closing": "С наилучшими пожеланиями"
        },
        "IT": {
            "subject": "La tua nuova password",
            "heading": "La tua nuova password",
            "greeting": "Caro utente,",
            "line1": "Il tuo account è stato creato con successo.",
            "line2": "La tua nuova password è: <span class=\"password\">{password}</span>",
            "line3": "Fai clic sul pulsante qui sotto per accedere:",
            "button": "Accedi",
            "closing": "Distinti saluti"
        },
        "ES": {
            "subject": "Tu nueva contraseña",
            "heading": "Tu nueva contraseña",
            "greeting": "Estimado usuario,",
            "line1": "Su cuenta ha sido creada con éxito.",
            "line2": "Su nueva contraseña es: <span class=\"password\">{password}</span>",
            "line3": "Haga clic en el botón a continuación para iniciar sesión:",
            "button": "Iniciar sesión",
            "closing": "Saludos cordiales"
        },
        "PT": {
            "subject": "Sua nova senha",
            "heading": "Sua nova senha",
            "greeting": "Prezado usuário,",
            "line1": "Sua conta foi criada com sucesso.",
            "line2": "Sua nova senha é: <span class=\"password\">{password}</span>",
            "line3": "Por favor, clique no botão abaixo para fazer login:",
            "button": "Entrar",
            "closing": "Atenciosamente"
        },
        "AR": {
            "subject": "كلمة المرور الجديدة لحسابك",
            "heading": "كلمة المرور الجديدة لحسابك",
            "greeting": "عزيزي المستخدم،",
            "line1": "تم إنشاء حسابك بنجاح.",
            "line2": "كلمة المرور الجديدة الخاصة بك هي: <span class=\"password\">{password}</span>",
            "line3": "يرجى النقر على الزر أدناه لتسجيل الدخول:",
            "button": "تسجيل الدخول",
            "closing": "مع أطيب التحيات"
        },
    }

    # Выбираем нужный перевод или дефолт на английский
    locale = translations.get(region.upper(), translations["EN"])

    # Формируем HTML, подставляя пароль и ссылку
    body_html = f"""
    <!DOCTYPE html>
    <html{" dir=\"rtl\"" if region.upper()=="AR" else ""}>
    <head>
      <meta charset="utf-8">
      <title>{locale["subject"]}</title>
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
        .btn {{
          display: inline-block;
          padding: 10px 20px;
          margin-top: 20px;
          background-color: #28a745;
          color: #fff;
          text-decoration: none;
          border-radius: 5px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>{locale["heading"]}</h2>
        <p>{locale["greeting"]}</p>
        <p>{locale["line1"]}</p>
        <p>{locale["line2"].format(password=password)}</p>
        <p>{locale["line3"]}</p>
        <a href="{login_url}" class="btn">{locale["button"]}</a>
        <p>{locale["closing"]}</p>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"]    = sender_email
    msg["To"]      = recipient_email
    msg["Subject"] = locale["subject"]
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_port != 25:
                server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        print("Error sending email:", e)

def send_recovery_email(recipient_email: str, new_password: str, region: str = "EN"):
    """
    Отправляет письмо для восстановления пароля, используя внешний блок
    recommended courses. SMTP‑логика не изменилась.
    """
    # 1. SMTP‑параметры (как было)
    smtp_server   = settings.EMAIL_HOST
    smtp_port     = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email  = settings.EMAIL_SENDER

    # 2. Общие переменные
    login_url     = "https://dent-s.com/login"
    support_email = "info.dis.org@gmail.com"

    # 3. Переводы
    translations = {
        "EN": {
            "subject": "Password Recovery Instructions",
            "heading": "Password Recovery Request",
            "greeting": "Dear User,",
            "intro": "We have received a request to reset your password.",
            "new_pass_label": "Your new password is:",
            "caution": "If you did not request a password reset, please contact our support team immediately.",
            "click": "Please click the button below to log in:",
            "button": "Log in",
            "footer": "This is an automated message. Please do not reply."
        },
        "RU": {
            "subject": "Инструкции по восстановлению пароля",
            "heading": "Запрос на восстановление пароля",
            "greeting": "Уважаемый пользователь,",
            "intro": "Мы получили запрос на сброс вашего пароля.",
            "new_pass_label": "Ваш новый пароль:",
            "caution": "Если вы не запрашивали сброс пароля, немедленно свяжитесь с поддержкой.",
            "click": "Пожалуйста, нажмите кнопку ниже, чтобы войти:",
            "button": "Войти",
            "footer": "Это автоматическое сообщение. Пожалуйста, не отвечайте."
        },
        "IT": {
            "subject": "Istruzioni per il ripristino della password",
            "heading": "Richiesta di ripristino password",
            "greeting": "Caro utente,",
            "intro": "Abbiamo ricevuto una richiesta per reimpostare la tua password.",
            "new_pass_label": "La tua nuova password è:",
            "caution": "Se non hai richiesto il reset, contatta subito il supporto.",
            "click": "Clicca sul pulsante qui sotto per accedere:",
            "button": "Accedi",
            "footer": "Messaggio automatico – non rispondere."
        },
        "ES": {
            "subject": "Instrucciones para la recuperación de contraseña",
            "heading": "Solicitud de recuperación de contraseña",
            "greeting": "Estimado usuario,",
            "intro": "Hemos recibido una solicitud para restablecer tu contraseña.",
            "new_pass_label": "Tu nueva contraseña es:",
            "caution": "Si no solicitaste esto, contacta de inmediato a soporte.",
            "click": "Haz clic en el botón de abajo para iniciar sesión:",
            "button": "Iniciar sesión",
            "footer": "Mensaje automático – no responder."
        },
        "PT": {
            "subject": "Instruções para recuperação de senha",
            "heading": "Solicitação de recuperação de senha",
            "greeting": "Prezado usuário,",
            "intro": "Recebemos um pedido para redefinir sua senha.",
            "new_pass_label": "Sua nova senha é:",
            "caution": "Se não foi você quem solicitou isto, fale com o suporte imediatamente.",
            "click": "Clique no botão abaixo para entrar:",
            "button": "Entrar",
            "footer": "Mensagem automática – não responda."
        },
        "AR": {
            "subject": "تعليمات استعادة كلمة المرور",
            "heading": "طلب استعادة كلمة المرور",
            "greeting": "عزيزي المستخدم،",
            "intro": "لقد استلمنا طلبًا لإعادة تعيين كلمة المرور الخاصة بك.",
            "new_pass_label": "كلمة المرور الجديدة الخاصة بك:",
            "caution": "إذا لم تطلب استعادة كلمة المرور، يرجى التواصل مع الدعم فورًا.",
            "click": "يرجى النقر على الزر أدناه لتسجيل الدخول:",
            "button": "تسجيل الدخول",
            "footer": "هذه رسالة آلية، يرجى عدم الرد."
        },
    }
    locale = translations.get(region.upper(), translations["EN"])

    # 4. HTML‑фрагмент с курсами
    region_courses_html = courses_block.get(region.upper()) or courses_block["EN"]

    # 5. Полный HTML шаблон
    body_html = f"""\
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en"{" dir=\"rtl\"" if region.upper()=="AR" else ""}>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{locale["subject"]}</title>
  </head>
  <body style="margin:0;padding:20px;background-color:#7fdfd5;font-family:Arial,sans-serif;color:#01433d;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="transparent">
      <tr align="center">
        <td>
          <a href="https://dent-s.com/">
            <img src="https://cdn.dent-s.com/logo-dents.png"
                 alt="Logo" width="150"
                 style="width:100%;max-width:150px;">
          </a>
        </td>
      </tr>

      <tr>
        <td align="center">
          <!--[if (gte mso 9)|(IE)]>
          <table width="600" align="center" cellpadding="0" cellspacing="0" border="0"><tr><td>
          <![endif]-->

          <table align="center" border="0" cellpadding="0" cellspacing="0"
                 style="max-width:600px;width:100%;background-color:#edf8ff;
                        padding:20px 10px 10px;border-radius:20px;
                        box-shadow:0 0 10px rgba(0,0,0,0.1);text-align:center;">

            <tr>
              <td>
                <h2 style="margin:0;color:#7fdfd5;font-size:32px;padding:0 10px 20px;font-weight:600;">
                  {locale["heading"]}
                </h2>
              </td>
            </tr>

            <tr>
              <td style="font-size:18px;line-height:26px;font-weight:500;border-radius:20px;padding:20px 10px;border:1px solid rgba(100,116,139,0.2);">
                <p style="margin:0 0 12px 0;">{locale["greeting"]}</p>
                <p style="margin:0 0 12px 0;">{locale["intro"]}</p>
                <p style="margin:0 0 12px 0;">
                  {locale["new_pass_label"]}<br>
                  <span style="color:#7fdfd5;"><strong>{new_password}</strong></span>
                </p>
                <p style="margin:0 0 18px 0;">
                  {locale["caution"]} <strong style="color:#7fdfd5;">{support_email}</strong>
                </p>
                <p style="margin:0 0 18px 0;">{locale["click"]}</p>
                <p style="margin:0 0 18px 0;">
                  <a href="{login_url}"
                     style="display:inline-block;padding:12px 24px;background-color:#01433d;color:#edf8ff;text-decoration:none;border-radius:40px;font-weight:500;">
                    {locale["button"]}
                  </a>
                </p>
                <p style="margin:0;line-height:24px;">{locale["footer"]}</p>
              </td>
            </tr>
            
            {region_courses_html}
            
          </table>

          <!--[if (gte mso 9)|(IE)]></td></tr></table><![endif]-->
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    # 6. Отправка (как было)
    msg = MIMEMultipart()
    msg["From"]    = sender_email
    msg["To"]      = recipient_email
    msg["Subject"] = locale["subject"]
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_port != 25:
                server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
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
    Параметр `region` указывает язык ("RU", "EN", "ES", "IT", "PT", "AR").
    """
    smtp_server   = settings.EMAIL_HOST
    smtp_port     = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email  = settings.EMAIL_SENDER

    contact_email = "info.dis.org@gmail.com"
    login_url     = "https://dent-s.com/login"
    more_url      = "https://dent-s.com/"

    courses_str = ", ".join(course_names) if course_names else ""

    # Словарь переводов
    translations = {
        "EN": {
            "subject":        "Purchase Confirmation — Your Course(s) Has Been Added",
            "heading_default":"Purchase Confirmation",
            "heading_new":    "Welcome and Congratulations!",
            "purchased":      "You have successfully purchased the following course(s): <strong>{courses_str}</strong>.",
            "account_info":   "We have created a new account for you.",
            "label_email":    "<strong>Email:</strong> {recipient_email}",
            "label_password": "<strong>Temporary Password:</strong> <span class=\"password\">{password}</span>",
            "added":          "They have been added to your account.",
            "prompt":         "Please use the button below to log in:",
            "btn_login":      "Log In",
            "btn_more":       "More courses here",
            "thanks":         "Thank you for your purchase!",
            "support":        "If you have any questions, contact us at <strong>{contact_email}</strong>."
        },
        "RU": {
            "subject":        "Подтверждение покупки — ваш курс добавлен",
            "heading_default":"Подтверждение покупки",
            "heading_new":    "Добро пожаловать и поздравляем!",
            "purchased":      "Вы успешно приобрели курс(ы): <strong>{courses_str}</strong>.",
            "account_info":   "Для вас создан новый аккаунт.",
            "label_email":    "<strong>Email:</strong> {recipient_email}",
            "label_password": "<strong>Пароль:</strong> <span class=\"password\">{password}</span>",
            "added":          "Они добавлены в ваш аккаунт.",
            "prompt":         "Пожалуйста, перейдите по кнопке ниже, чтобы войти:",
            "btn_login":      "Войти",
            "btn_more":       "Больше курсов здесь",
            "thanks":         "Спасибо за покупку!",
            "support":        "Если у вас возникнут вопросы, напишите на <strong>{contact_email}</strong>."
        },
        "ES": {
            "subject":        "Confirmación de compra — su curso ha sido agregado",
            "heading_default":"Confirmación de compra",
            "heading_new":    "¡Bienvenido y felicitaciones!",
            "purchased":      "Ha comprado con éxito el/los curso(s): <strong>{courses_str}</strong>.",
            "account_info":   "Se ha creado una nueva cuenta para usted.",
            "label_email":    "<strong>Email:</strong> {recipient_email}",
            "label_password": "<strong>Contraseña temporal:</strong> <span class=\"password\">{password}</span>",
            "added":          "Se han agregado a su cuenta.",
            "prompt":         "Use el botón a continuación para iniciar sesión:",
            "btn_login":      "Iniciar sesión",
            "btn_more":       "Más cursos aquí",
            "thanks":         "¡Gracias por su compra!",
            "support":        "Si tiene alguna pregunta, escriba a <strong>{contact_email}</strong>."
        },
        "IT": {
            "subject":        "Conferma di acquisto — il tuo corso è stato aggiunto",
            "heading_default":"Conferma di acquisto",
            "heading_new":    "Benvenuto e congratulazioni!",
            "purchased":      "Hai acquistato con successo il/los corso(i): <strong>{courses_str}</strong>.",
            "account_info":   "Abbiamo creato un nuovo account per te.",
            "label_email":    "<strong>Email:</strong> {recipient_email}",
            "label_password": "<strong>Password temporanea:</strong> <span class=\"password\">{password}</span>",
            "added":          "Sono stati aggiunti al tuo account.",
            "prompt":         "Per favore, usa il pulsante qui sotto per accedere:",
            "btn_login":      "Accedi",
            "btn_more":       "Altri corsi qui",
            "thanks":         "Grazie per il tuo acquisto!",
            "support":        "Se hai domande, contatta <strong>{contact_email}</strong>."
        },
        "PT": {
            "subject":        "Confirmação de compra — seu curso foi adicionado",
            "heading_default":"Confirmação de compra",
            "heading_new":    "Bem‑vindo e parabéns!",
            "purchased":      "Você comprou com sucesso o(s) curso(s): <strong>{courses_str}</strong>.",
            "account_info":   "Criamos uma nova conta para você.",
            "label_email":    "<strong>Email:</strong> {recipient_email}",
            "label_password": "<strong>Senha temporária:</strong> <span class=\"password\">{password}</span>",
            "added":          "Eles foram adicionados à sua conta.",
            "prompt":         "Por favor, use o botão abaixo para fazer login:",
            "btn_login":      "Entrar",
            "btn_more":       "Mais cursos aqui",
            "thanks":         "Obrigado pela sua compra!",
            "support":        "Se tiver dúvidas, entre em contato em <strong>{contact_email}</strong>."
        },
        "AR": {
            "subject":        "تأكيد الشراء — تم إضافة دورتك",
            "heading_default":"تأكيد الشراء",
            "heading_new":    "مرحبًا وتهانينا!",
            "purchased":      "لقد اشتريت بنجاح الدورة(الدورات): <strong>{courses_str}</strong>.",
            "account_info":   "تم إنشاء حساب جديد لك.",
            "label_email":    "<strong>البريد الإلكتروني:</strong> {recipient_email}",
            "label_password": "<strong>كلمة المرور المؤقتة:</strong> <span class=\"password\">{password}</span>",
            "added":          "تمت إضافتها إلى حسابك.",
            "prompt":         "يرجى استخدام الزر أدناه لتسجيل الدخول:",
            "btn_login":      "تسجيل الدخول",
            "btn_more":       "المزيد من الدورات هنا",
            "thanks":         "شكرًا لشرائك!",
            "support":        "إذا كانت لديك أي أسئلة، تواصل معنا على <strong>{contact_email}</strong>."
        },
    }

    # Выбираем нужный язык или падаем на английский
    locale = translations.get(region.upper(), translations["EN"])

    # Общие стили и обёртка
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""
    body_html = f"""\
    <!DOCTYPE html>
    <html{html_dir}>
    <head>
      <meta charset="utf-8">
      <title>{locale["subject"]}</title>
      <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{
          background-color: #fff;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 0 10px rgba(0,0,0,0.1);
          max-width: 600px;
          margin: auto;
        }}
        h2 {{ color: #333; }}
        p {{ font-size: 16px; line-height: 1.5; color: #555; }}
        .password {{ font-size: 18px; font-weight: bold; color: #d9534f; }}
        .btn {{
          display: inline-block;
          padding: 10px 20px;
          margin-top: 20px;
          background-color: #28a745;
          color: #fff;
          text-decoration: none;
          border-radius: 5px;
        }}
        .btn-more {{ background-color: #007bff; margin-left: 10px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h2>{locale["heading_new"] if new_account else locale["heading_default"]}</h2>
        <p>{locale["purchased"].format(courses_str=courses_str)}</p>"""

    if new_account:
        body_html += f"""
        <p>{locale["account_info"]}</p>
        <p>{locale["label_email"].format(recipient_email=recipient_email)}</p>
        <p class="password">{locale["label_password"].format(password=password)}</p>"""
    else:
        body_html += f"""
        <p>{locale["added"]}</p>"""

    body_html += f"""
        <p>{locale["prompt"]}</p>
        <a href="{login_url}" class="btn">{locale["btn_login"]}</a>
        <a href="{more_url}" class="btn btn-more">{locale["btn_more"]}</a>
        <p>{locale["thanks"]}</p>
        <p>{locale["support"].format(contact_email=contact_email)}</p>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"]    = sender_email
    msg["To"]      = recipient_email
    msg["Subject"] = locale["subject"]
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_port != 25:
                server.starttls()
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
    """
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email = settings.EMAIL_SENDER

    contact_email = "info.dis.org@gmail.com"
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
              display: inline-block;
              padding: 10px 20px;
              margin-top: 20px;
              background-color: #28a745;
              color: #fff;
              text-decoration: none;
              border-radius: 5px;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Ошибка оплаты</h2>
            <p>К сожалению, ваша оплата за курс(ы): <strong>{courses_str}</strong> не прошла.</p>
            <p>Пожалуйста, попробуйте ещё раз или свяжитесь со службой поддержки.</p>
            <p>Для входа в систему используйте кнопку ниже:</p>
            <a href="https://dent-s.com/login" class="btn">Войти</a>
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
              display: inline-block;
              padding: 10px 20px;
              margin-top: 20px;
              background-color: #28a745;
              color: #fff;
              text-decoration: none;
              border-radius: 5px;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Error de pago</h2>
            <p>Lamentablemente, su pago por el/los curso(s): <strong>{courses_str}</strong> no se realizó correctamente.</p>
            <p>Por favor, inténtelo de nuevo o póngase en contacto con el soporte.</p>
            <p>Utilice el botón a continuación para iniciar sesión:</p>
            <a href="https://dent-s.com/login" class="btn">Iniciar sesión</a>
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
              display: inline-block;
              padding: 10px 20px;
              margin-top: 20px;
              background-color: #28a745;
              color: #fff;
              text-decoration: none;
              border-radius: 5px;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <h2>Payment Failed</h2>
            <p>Unfortunately, your payment for the following course(s): <strong>{courses_str}</strong> could not be processed.</p>
            <p>Please try again or contact support for assistance.</p>
            <p>Please click the button below to log in:</p>
            <a href="https://dent-s.com/login" class="btn">Log In</a>
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
            if smtp_port != 25:
                server.starttls()
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
    Предлагаем выбрать другой курс той же стоимости, связавшись с поддержкой.
    Поддерживаем языки: EN, RU, ES, IT, PT, AR (fallback — EN).
    """
    smtp_server   = settings.EMAIL_HOST
    smtp_port     = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email  = settings.EMAIL_SENDER

    contact_email = "info.dis.org@gmail.com"
    login_url     = "https://dent-s.com/login"
    courses_str   = ", ".join(course_names) if course_names else ""

    translations = {
        "EN": {
            "subject": "You Already Own These Courses",
            "heading": "You Already Own These Courses",
            "message": ("You have paid for the following course(s), which you already own: "
                        "<strong>{courses}</strong>."),
            "action": "If you would like to exchange them for another course of the same price, "
                      "please contact us at <strong>{contact}</strong>.",
            "button": "Log In",
            "thanks": "Thank you!"
        },
        "RU": {
            "subject": "Оплаченные курсы уже есть в вашем аккаунте",
            "heading": "Вы уже владеете этими курсами",
            "message": ("Вы оплатили курсы, которые у вас уже есть: "
                        "<strong>{courses}</strong>."),
            "action": "Если хотите заменить их на другие курсы той же стоимости, "
                      "свяжитесь с нами по адресу <strong>{contact}</strong>.",
            "button": "Войти",
            "thanks": "Спасибо!"
        },
        "ES": {
            "subject": "Cursos ya adquiridos",
            "heading": "Usted ya posee estos cursos",
            "message": ("Ha pagado por los cursos que ya tenía: "
                        "<strong>{courses}</strong>."),
            "action": "Si desea reemplazarlos por otros cursos del mismo valor, "
                      "por favor contáctenos en <strong>{contact}</strong>.",
            "button": "Iniciar sesión",
            "thanks": "¡Gracias!"
        },
        "IT": {
            "subject": "Hai già questi corsi",
            "heading": "Hai già questi corsi",
            "message": ("Hai già acquistato i seguenti corso(i): "
                        "<strong>{courses}</strong>."),
            "action": "Se desideri sostituirli con altri corsi dello stesso prezzo, "
                      "contattaci a <strong>{contact}</strong>.",
            "button": "Accedi",
            "thanks": "Grazie!"
        },
        "PT": {
            "subject": "Você já possui estes cursos",
            "heading": "Você já possui estes cursos",
            "message": ("Você pagou pelos seguintes curso(s), "
                        "que você já possui: <strong>{courses}</strong>."),
            "action": "Se quiser trocá‑los por outro curso do mesmo valor, "
                      "entre em contato conosco em <strong>{contact}</strong>.",
            "button": "Entrar",
            "thanks": "Obrigado!"
        },
        "AR": {
            "subject": "لقد امتلكت هذه الدورات بالفعل",
            "heading": "لقد امتلكت هذه الدورات بالفعل",
            "message": ("لقد دفعت مقابل الدورة(الدورات) التالية، والتي تمتلكها بالفعل: "
                        "<strong>{courses}</strong>."),
            "action": "إذا كنت ترغب في استبدالها بدورات أخرى بنفس السعر، "
                      "يرجى التواصل معنا على <strong>{contact}</strong>.",
            "button": "تسجيل الدخول",
            "thanks": "شكرًا لك!"
        },
    }

    locale = translations.get(region.upper(), translations["EN"])
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""

    body_html = f"""\
    <!DOCTYPE html>
    <html{html_dir}>
    <head>
      <meta charset="utf-8">
      <title>{locale["subject"]}</title>
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
        <h2>{locale["heading"]}</h2>
        <p>{locale["message"].format(courses=courses_str)}</p>
        <p>{locale["action"].format(contact=contact_email)}</p>
        <p>Please click the button below to log in:</p>
        <a href="{login_url}" class="btn">{locale["button"]}</a>
        <p>{locale["thanks"]}</p>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"]    = sender_email
    msg["To"]      = recipient_email
    msg["Subject"] = locale["subject"]
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_port != 25:
                server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
    except Exception as e:
        print(f"Error sending already-owned-course email: {e}")

# --------------------------------------------------------------------------
#  MARKETING LETTER FOR ABANDONED CHECKOUT
# --------------------------------------------------------------------------
def send_abandoned_checkout_email(
    recipient_email: str,
    password: str,
    course_info: dict[str, str | int | float],
    region: str = "EN"
) -> None:
    """
    Письмо для лида из abandoned_checkouts.

    • включает акцентированный пароль, бонус 5 $;
    • отображает конкретный курс, который уже добавлен пользователю
      (карточка генерируется через render_course_card);
    • подставляет локализованный текст и блок курсов courses_block.
    """
    import smtplib
    import logging
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # SMTP-конфигурация
    smtp_server   = settings.EMAIL_HOST
    smtp_port     = settings.EMAIL_PORT
    smtp_username = settings.EMAIL_USERNAME
    smtp_password = settings.EMAIL_PASSWORD
    sender_email  = settings.EMAIL_SENDER

    # Постоянные ссылки
    login_url     = "https://dent-s.com/login"
    more_url      = "https://dent-s.com/"
    support_email = "info.dis.org@gmail.com"

    # ------------------------------------------------------------------
    #  Локализованные строки (обновлены и «оживлены»)
    # ------------------------------------------------------------------
    translations = {
        "RU": {
            "subject":   "Ваш бонус 5 $ и бесплатный урок уже ждут вас!",
            "heading":   "Мы ценим ваш интерес!",
            "greeting":  "Здравствуйте!",
            "l1":        "Мы заметили, что у вас возникли проблемы с оплатой, и хотим вам помочь.",
            "l2":        "Мы создали для вас аккаунт — пароль можно изменить в любой момент в личном кабинете.",
            "l3":        "Мы уже начислили 5 $ на ваш баланс — вы можете потратить их на любой курс на нашем сайте.",
            "l4":        "Специально для вас мы добавили в ваш личный кабинет курс, которым вы интересовались, и открыли полный доступ к первому уроку бесплатно.",
            "l5":        "Надеемся, что это улучшит ваше впечатление о нас. Если у вас остались вопросы, пишите на <strong>info.dis.org@gmail.com</strong>.",
            "extras": [
                "Реферальная программа: приглашайте коллег и получайте <strong>50 %</strong> от их покупок.",
                "Сотни курсов в десятках категорий и на разных языках."
            ],
            "login_hint": "Для входа используйте e-mail <strong>{recipient_email}</strong> — это ваш логин.",
            "btn_login":  "Войти",
            "btn_more":   "Выбрать курс",
            "footer":     "Это автоматическое письмо, отвечать на него не нужно."
        },
        "EN": {
            "subject":   "Your $5 bonus and free lesson are waiting!",
            "heading":   "We value your interest!",
            "greeting":  "Hello!",
            "l1":        "We noticed you had trouble completing your payment and we want to help.",
            "l2":        "An account has been created for you — feel free to change the password at any time in your dashboard.",
            "l3":        "We’ve already added $5 to your balance—you can spend it on any course on our site.",
            "l4":        "Just for you, we’ve added the course you were interested in to your dashboard and unlocked full access to the first lesson for free.",
            "l5":        "We hope this gesture improves your experience with us. If you still have questions, write to <strong>info.dis.org@gmail.com</strong>.",
            "extras": [
                "Referral program: invite a colleague and earn <strong>50 %</strong> of their purchases.",
                "Hundreds of courses across dozens of categories and languages."
            ],
            "login_hint": "Sign in with <strong>{recipient_email}</strong> — this is your login.",
            "btn_login":  "Log in",
            "btn_more":   "Browse courses",
            "footer":     "This is an automated message. Please do not reply."
        },
        "ES": {
            "subject":   "¡Tu bono de 5 $ y la lección gratis te esperan!",
            "heading":   "¡Valoramos tu interés!",
            "greeting":  "¡Hola!",
            "l1":        "Detectamos que hubo un problema con el pago y queremos ayudarte.",
            "l2":        "Ya creamos una cuenta para ti — puedes cambiar la contraseña cuando quieras.",
            "l3":        "Hemos añadido 5 $ a tu saldo; puedes gastarlos en cualquier curso.",
            "l4":        "Hemos añadido a tu panel el curso que te interesaba y desbloqueado gratis la primera lección.",
            "l5":        "Esperamos mejorar así tu experiencia con nosotros. Si tienes dudas, escríbenos a <strong>info.dis.org@gmail.com</strong>.",
            "extras": [
                "Programa de referidos: invita a un colega y gana el <strong>50 %</strong> de sus compras.",
                "Cientos de cursos en varias categorías e idiomas."
            ],
            "login_hint": "Para entrar usa el e-mail <strong>{recipient_email}</strong> — es tu usuario.",
            "btn_login":  "Iniciar sesión",
            "btn_more":   "Explorar cursos",
            "footer":     "Mensaje automático — no responder."
        },
        "IT": {
            "subject":   "Il tuo bonus da 5 $ e la lezione gratuita ti aspettano!",
            "heading":   "Apprezziamo il tuo interesse!",
            "greeting":  "Ciao!",
            "l1":        "Abbiamo visto che il pagamento non è andato a buon fine e vogliamo aiutarti.",
            "l2":        "Ti abbiamo creato un account; puoi cambiare la password quando vuoi dal tuo profilo.",
            "l3":        "Abbiamo accreditato 5 $ sul tuo saldo — spendili su qualsiasi corso.",
            "l4":        "Abbiamo aggiunto al tuo profilo il corso che ti interessava e sbloccato gratuitamente la prima lezione.",
            "l5":        "Speriamo che questo migliori la tua esperienza con noi. Per qualunque dubbio scrivici a <strong>info.dis.org@gmail.com</strong>.",
            "extras": [
                "Programma referral: invita un collega e guadagna il <strong>50 %</strong> dei suoi acquisti.",
                "Centinaia di corsi in molte categorie e lingue."
            ],
            "login_hint": "Per accedere usa l’e-mail <strong>{recipient_email}</strong> — è il tuo login.",
            "btn_login":  "Accedi",
            "btn_more":   "Scopri i corsi",
            "footer":     "Messaggio automatico — non rispondere."
        },
        "PT": {
            "subject":   "Seu bônus de 5 $ e aula grátis estão esperando!",
            "heading":   "Valorizamos seu interesse!",
            "greeting":  "Olá!",
            "l1":        "Percebemos um problema no pagamento e queremos ajudar.",
            "l2":        "Criamos uma conta para você — altere a senha quando quiser.",
            "l3":        "Adicionamos 5 $ ao seu saldo — use em qualquer curso.",
            "l4":        "Adicionamos ao seu painel o curso de seu interesse e liberamos a primeira aula gratuitamente.",
            "l5":        "Esperamos melhorar sua experiência. Dúvidas? Escreva para <strong>info.dis.org@gmail.com</strong>.",
            "extras": [
                "Programa de indicação: convide um colega e receba <strong>50 %</strong> das compras dele.",
                "Centenas de cursos em várias categorias e idiomas."
            ],
            "login_hint": "Entre com o e-mail <strong>{recipient_email}</strong> — este é seu login.",
            "btn_login":  "Entrar",
            "btn_more":   "Ver cursos",
            "footer":     "Mensagem automática — não responda."
        },
        "AR": {
            "subject":   "هدية 5 $ والدرس المجاني بانتظارك!",
            "heading":   "نقدّر اهتمامك!",
            "greeting":  "مرحبًا!",
            "l1":        "لاحظنا وجود مشكلة في الدفع ونرغب بمساعدتك.",
            "l2":        "أنشأنا لك حسابًا — يمكنك تغيير كلمة المرور في أي وقت.",
            "l3":        "أضفنا 5 $ إلى رصيدك — استخدمها لشراء أي دورة.",
            "l4":        "أضفنا إلى حسابك الدورة التي كنت مهتمًا بها وفتحنا الدرس الأول مجانًا.",
            "l5":        "نأمل أن يحسّن ذلك تجربتك معنا. لأي استفسار راسلنا على <strong>info.dis.org@gmail.com</strong>.",
            "extras": [
                "نظام الإحالة: ادعُ زميلًا واحصل على <strong>50 %</strong> من مشترياته.",
                "العديد من الدورات في مختلف المجالات واللغات."
            ],
            "login_hint": "استخدم البريد <strong>{recipient_email}</strong> لتسجيل الدخول.",
            "btn_login":  "تسجيل الدخول",
            "btn_more":   "استكشاف الدورات",
            "footer":     "هذه رسالة آلية، يرجى عدم الرد."
        },
    }

    loc = translations.get(region.upper(), translations["EN"])
    region_courses_html = courses_block.get(region.upper()) or courses_block["EN"]
    chosen_course_html  = render_course_card(course_info)

    # ------------------------------------------------------------------
    #  Формируем HTML
    # ------------------------------------------------------------------
    body_html = f"""\
<!DOCTYPE html>
<html lang="{region.lower()}"{" dir=\"rtl\"" if region.upper()=="AR" else ""}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{loc["subject"]}</title>
</head>
<body style="margin:0;padding:20px;background:#7fdfd5;font-family:Arial,sans-serif;color:#01433d;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
      <a href="https://dent-s.com/">
        <img src="https://cdn.dent-s.com/logo-dents.png" alt="Logo" width="150" style="max-width:150px;width:100%;">
      </a>
    </td></tr>
    <tr><td align="center">
      <table cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#edf8ff;border-radius:20px;padding:20px;box-shadow:0 0 10px rgba(0,0,0,0.08);text-align:center;">
        <tr><td>
          <h2 style="margin:0 0 12px;font-size:32px;color:#7fdfd5;">{loc["heading"]}</h2>
          <p style="margin:0 0 20px;font-size:20px;font-weight:600;">{loc["greeting"]}</p>
        </td></tr>
        <tr><td style="font-size:18px;line-height:28px;font-weight:500;padding:0 10px;text-align:left;">
          <p>{loc["l1"]}</p>
          <p>{loc["l2"]}</p>
          <p>{loc["l3"]}</p>
          <p>{loc["l4"]}</p>
        </td></tr>

        {chosen_course_html}

        <tr><td style="font-size:18px;line-height:28px;font-weight:500;padding:10px;text-align:left;">
          <p>{loc["l5"]}</p>
          <p style="margin:24px 0 6px;font-size:20px;font-weight:700;color:#01433d;text-align:center;">{loc["login_hint"].format(recipient_email=recipient_email)}</p>
          <p style="margin:0 0 24px;font-size:38px;font-weight:700;color:#7fdfd5;text-align:center;">{password}</p>
          <p>{'</p><p>'.join(loc['extras'])}</p>
          <p style="margin:30px 0 24px;text-align:center;">
            <a href="{login_url}" style="display:inline-block;padding:12px 36px;background:#01433d;color:#edf8ff;text-decoration:none;border-radius:40px;font-weight:600;">{loc["btn_login"]}</a>
            &nbsp;&nbsp;
            <a href="{more_url}" style="display:inline-block;padding:12px 36px;background:#2d8eff;color:#edf8ff;text-decoration:none;border-radius:40px;font-weight:600;">{loc["btn_more"]}</a>
          </p>
        </td></tr>

        {region_courses_html}

        <tr><td style="font-size:14px;line-height:20px;text-align:center;color:#475569;padding-top:20px;">
          {loc["footer"]}<br><br>{support_email}
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    # ------------------------------------------------------------------
    #  Отправка
    # ------------------------------------------------------------------
    msg = MIMEMultipart()
    msg["From"]    = sender_email
    msg["To"]      = recipient_email
    msg["Subject"] = loc["subject"]
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_port != 25:
                server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            logging.info("Abandoned-checkout e-mail sent to %s", recipient_email)
    except Exception as exc:
        logging.error("SMTP error while sending to %s: %s", recipient_email, exc)



