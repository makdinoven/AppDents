
from .common import send_html_email
from .dent_s_courses_html import COURSES_BLOCK
from ...core.config import settings


# --------------------------------------------------------------------------
#  HTML-карточка конкретного курса, который уже добавлен пользователю
# --------------------------------------------------------------------------
def render_course_card(course: dict[str, str] | None) -> str:
    if not course:
        return ""
    price       = course.get("price", "")
    old_price   = course.get("old_price", "")
    lessons     = course.get("lessons", "")
    title       = course.get("title", "")
    img         = course.get("img", "https://dent-s.com/assets/img/placeholder.png")
    url         = course.get("url", "#")

    badge_old = (
        f'<span style="text-decoration:line-through;color:#006d8d;">{old_price}</span>'
        if old_price else ""
    )

    return f"""
<tr>
  <td style="font-size:12px;line-height:16px;font-weight:500;border-radius:20px;padding:5px;border:1px solid rgba(100,116,139,0.2);">
    <table style="width:100%;color:#01433d;" cellpadding="0" cellspacing="5px">
      <tr>
        <td valign="top">
          <a href="{url}" style="text-decoration:none;color:#01433d;display:block;">
            <div style="border-radius:20px;background-color:#7fdfd5;padding:10px;">
              <p style="margin:0 0 5px;" align="left">
                <strong>{price}</strong>
                {badge_old}
                <span style="background-color:transparent;color:#017f74;padding:4px 4px;border-radius:20px;border:1px solid #017f74;">{lessons}</span>
              </p>
              <h4 style="margin:0 0 5px;" align="left">{title}</h4>
              <img src="{img}" alt="Course cover" style="max-width:100%;width:100%; object-fit:cover; max-height:300px;border-radius:15px;">
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


# --------------------------------------------------------------------------
#  ПАРОЛЬ ПРИ РЕГИСТРАЦИИ
# --------------------------------------------------------------------------
def send_password_to_user(recipient_email: str, password: str, region: str):
    login_url     = "https://dent-s.com/login"

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

    loc = translations.get(region.upper(), translations["EN"])

    body_html = f"""
    <!DOCTYPE html>
    <html{" dir=\"rtl\"" if region.upper()=="AR" else ""}>
    <head>
      <meta charset="utf-8">
      <title>{loc["subject"]}</title>
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
        <h2>{loc["heading"]}</h2>
        <p>{loc["greeting"]}</p>
        <p>{loc["line1"]}</p>
        <p>{loc["line2"].format(password=password)}</p>
        <p>{loc["line3"]}</p>
        <a href="{login_url}" class="btn">{loc["button"]}</a>
        <p>{loc["closing"]}</p>
      </div>
    </body>
    </html>
    """

    send_html_email(recipient_email, loc["subject"], body_html)


# --------------------------------------------------------------------------
#  ВОССТАНОВЛЕНИЕ ПАРОЛЯ (с блоком курсов)
# --------------------------------------------------------------------------
def send_recovery_email(recipient_email: str, new_password: str, region: str = "EN"):
    login_url     = "https://dent-s.com/login"
    support_email = "info.dis.org@gmail.com"

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
            "footer": "Mensagem automática – не responda."
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
    loc = translations.get(region.upper(), translations["EN"])
    region_courses_html = COURSES_BLOCK.get(region.upper()) or COURSES_BLOCK["EN"]

    body_html = f"""\
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en"{" dir=\"rtl\"" if region.upper()=="AR" else ""}>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{loc["subject"]}</title>
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
                  {loc["heading"]}
                </h2>
              </td>
            </tr>

            <tr>
              <td style="font-size:18px;line-height:26px;font-weight:500;border-radius:20px;padding:20px 10px;border:1px solid rgba(100,116,139,0.2);">
                <p style="margin:0 0 12px 0;">{loc["greeting"]}</p>
                <p style="margin:0 0 12px 0;">{loc["intro"]}</p>
                <p style="margin:0 0 12px 0;">
                  {loc["new_pass_label"]}<br>
                  <span style="color:#7fdfd5;"><strong>{new_password}</strong></span>
                </p>
                <p style="margin:0 0 18px 0;">
                  {loc["caution"]} <strong style="color:#7fdfd5;">{support_email}</strong>
                </p>
                <p style="margin:0 0 18px 0;">{loc["click"]}</p>
                <p style="margin:0 0 18px 0;">
                  <a href="{login_url}"
                     style="display:inline-block;padding:12px 24px;background-color:#01433d;color:#edf8ff;text-decoration:none;border-radius:40px;font-weight:500;">
                    {loc["button"]}
                  </a>
                </p>
                <p style="margin:0;line-height:24px;">{loc["footer"]}</p>
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
    send_html_email(recipient_email, loc["subject"], body_html)


# --------------------------------------------------------------------------
#  ПОДТВЕРЖДЕНИЕ ПОКУПКИ
# --------------------------------------------------------------------------
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
        "PT": "Confirmação de compra — itens adicionados à sua conta",
        "AR": "تأكيد الشراء — تمت إضافة العناصر إلى حسابك",
    }.get(region.upper(), "Purchase Confirmation")

    courses_str = ", ".join(course_names or [])
    books_str = ", ".join(book_titles or [])

    # локализации
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
            "access_info": "You can log in anytime, from any device or browser, using your email and password to access your purchased content:",
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
            "access_info": "Вы можете войти в любое время, с любого устройства и браузера, используя вашу почту и пароль для доступа к приобретённому контенту:",
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
            "access_info": "Puoi accedere in qualsiasi momento, da qualsiasi dispositivo o browser, utilizzando la tua email e password per accedere ai contenuti acquistati:",
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
            "access_info": "Puede iniciar sesión en cualquier momento, desde cualquier dispositivo o navegador, utilizando su correo electrónico y contraseña para acceder al contenido adquirido:",
        },
        "PT": {
            "heading_new": "Bem-vindo e parabéns!",
            "heading_default": "Confirmação de compra",
            "courses": "Cursos",
            "books": "Livros",
            "purchased_courses": "Você comprou os seguintes cursos:",
            "purchased_books": "Você comprou os seguintes livros:",
            "account_created": "Criamos uma nova conta para você:",
            "email": "Email",
            "password": "Senha temporária",
            "login": "Entrar",
            "access_info": "Você pode fazer login a qualquer momento, de qualquer dispositivo ou navegador, usando seu e-mail e senha para acessar o conteúdo adquirido:",
        },
        "AR": {
            "heading_new": "مرحبًا وتهانينا!",
            "heading_default": "تأكيد الشراء",
            "courses": "الدورات",
            "books": "الكتب",
            "purchased_courses": "لقد اشتريت الدورات التالية:",
            "purchased_books": "لقد اشتريت الكتب التالية:",
            "account_created": "لقد أنشأنا لك حسابًا جديدًا:",
            "email": "البريد الإلكتروني",
            "password": "كلمة المرور المؤقتة",
            "login": "تسجيل الدخول",
            "access_info": "يمكنك تسجيل الدخول في أي وقت، من أي جهاز أو متصفح، باستخدام بريدك الإلكتروني وكلمة المرور للوصول إلى المحتوى الذي اشتريته:",
        },
    }.get(region.upper(), {})

    login_url = "https://dent-s.com/login"

    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""

    # --- формируем блоки ---
    account_block = ""
    if new_account:
        account_block = f"""
        <div style="margin-top:12px;">
          <p>{loc["account_created"]}</p>
          <p><b>{loc["email"]}:</b> {recipient_email}</p>
          <p><b>{loc["password"]}:</b> {password or ""}</p>
        </div>
        """

    courses_block = ""
    if courses_str:
        courses_block = f"""
        <div style="margin-top:12px;">
          <h3 style="margin:0 0 6px;">{loc["courses"]}</h3>
          <p style="margin:0;">{loc["purchased_courses"]} <b>{courses_str}</b></p>
        </div>
        """

    books_block = ""
    if books_str:
        books_block = f"""
        <div style="margin-top:12px;">
          <h3 style="margin:0 0 6px;">{loc["books"]}</h3>
          <p style="margin:0;">{loc["purchased_books"]} <b>{books_str}</b></p>
        </div>
        """

    access_block = f"""
        <div style="margin-top:16px;padding:12px;background-color:#e8f5e9;border-radius:8px;border-left:4px solid #28a745;">
          <p style="margin:0;font-size:14px;color:#2e7d32;">
            {loc.get("access_info", "You can log in anytime, from any device or browser, using your email and password to access your purchased content:")}
            <a href="https://dent-s.com" style="color:#01433d;font-weight:600;">dent-s.com</a>
          </p>
        </div>
        """

    body_html = f"""
    <html{html_dir}>
    <head>
      <meta charset="utf-8">
      <title>{subject}</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          background-color: #edf8ff;
          padding: 20px;
        }}
        .container {{
          background-color: #fff;
          padding: 20px;
          border-radius: 12px;
          box-shadow: 0 0 10px rgba(0,0,0,0.1);
          max-width: 600px;
          margin: auto;
        }}
        h2 {{
          color: #01433d;
        }}
        p {{
          font-size: 16px;
          line-height: 1.5;
          color: #333;
        }}
        .btn {{
          display: inline-block;
          padding: 10px 20px;
          margin-top: 20px;
          background-color: #01433d;
          color: #fff;
          text-decoration: none;
          border-radius: 6px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <img src="https://cdn.dent-s.com/logo-dents.png" alt="Dent-S" width="150" />
        <h2>{loc["heading_new"] if new_account else loc["heading_default"]}</h2>
        {account_block}
        {courses_block}
        {books_block}
        {access_block}
        <p style="text-align:center;">
          <a href="{login_url}" class="btn">{loc["login"]}</a>
        </p>
        <p style="margin-top:20px;text-align:center;">Best regards,<br><b>Dent-S Team</b></p>
      </div>
    </body>
    </html>
    """

    send_html_email(recipient_email, subject, body_html)



# --------------------------------------------------------------------------
#  ОШИБКА ОПЛАТЫ
# --------------------------------------------------------------------------
def send_failed_purchase_email(
    recipient_email: str,
    course_names: list[str],
    region: str = "EN"
):
    contact_email = "info.dis.org@gmail.com"
    courses_str = ", ".join(course_names) if course_names else "No course name"

    if region.upper() == "RU":
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
    elif region.upper() == "ES":
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

    send_html_email(recipient_email, subject, body_html)


# --------------------------------------------------------------------------
#  УЖЕ ЕСТЬ КУРС
# --------------------------------------------------------------------------
def send_already_owned_course_email(
    recipient_email: str,
    course_names: list[str],
    region: str = "EN"
):
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
            "action": "Se quiser trocá-los por outro curso do mesmo valor, "
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

    loc = translations.get(region.upper(), translations["EN"])
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""

    body_html = f"""\
    <!DOCTYPE html>
    <html{html_dir}>
    <head>
      <meta charset="utf-8">
      <title>{loc["subject"]}</title>
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
        <h2>{loc["heading"]}</h2>
        <p>{loc["message"].format(courses=courses_str)}</p>
        <p>{loc["action"].format(contact=contact_email)}</p>
        <p>Please click the button below to log in:</p>
        <a href="{login_url}" class="btn">{loc["button"]}</a>
        <p>{loc["thanks"]}</p>
      </div>
    </body>
    </html>
    """
    send_html_email(recipient_email, loc["subject"], body_html)


# --------------------------------------------------------------------------
#  БРОШЕННАЯ КОРЗИНА (аккаунт + $5 бонус + бесплатный урок)
# --------------------------------------------------------------------------
def send_abandoned_checkout_email(
    recipient_email: str,
    password: str,
    course_info: dict[str, str | int | float],
    region: str = "EN"
) -> None:
    login_url     = "https://dent-s.com/login"
    more_url      = "https://dent-s.com/"
    support_email = "info.dis.org@gmail.com"

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
            "footer":     "Mensagem automática — не responda."
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
    region_courses_html = COURSES_BLOCK.get(region.upper()) or COURSES_BLOCK["EN"]
    chosen_course_html  = render_course_card(course_info)

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
        <img src="https://cdn.dent-s.com/logo-dents.png" width="150" style="max-width:150px;width:100%;">
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

        <tr><td style="font-size:14px;line-height:20px;text-align:center;color:#475569;padding-top:20px">
          {loc["footer"]}<br><br><span style="text-decoration:none;color:#79cee7;">{support_email}</span>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    send_html_email(recipient_email, loc["subject"], body_html)


# --------------------------------------------------------------------------
#  ПРИГЛАШЕНИЕ НА ПЛАТФОРМУ (от пользователя)
# --------------------------------------------------------------------------
def send_invitation_email(
    recipient_email: str,
    sender_email: str,
    referral_code: str,
    region: str = "EN"
) -> None:
    """Письмо-приглашение от пользователя на платформу Dent-S."""
    register_url = f"https://dent-s.com/?rc={referral_code}"
    
    translations = {
        "EN": {
            "subject": "You've been invited to Dent-S platform!",
            "heading": "Join Dent-S Platform",
            "greeting": f"{sender_email} invites you to join our dental online learning platform!",
            "intro": "Discover a world of professional dental education at your fingertips.",
            "benefits_title": "What awaits you:",
            "benefits": [
                "Hundreds of online courses from leading experts",
                "Extensive library of dental books and materials",
                "Affordable prices and special offers",
                "Learn at your own pace, anytime, anywhere"
            ],
            "cta": "Join Dent-S today and start your learning journey!",
            "button": "Explore Platform",
            "footer": "This invitation was sent by {sender}. If you received this email by mistake, please ignore it."
        },
        "RU": {
            "subject": "Вас пригласили на платформу Dent-S!",
            "heading": "Присоединяйтесь к Dent-S",
            "greeting": f"{sender_email} приглашает вас на нашу платформу стоматологического онлайн-обучения!",
            "intro": "Откройте для себя мир профессионального стоматологического образования.",
            "benefits_title": "Что вас ждёт:",
            "benefits": [
                "Сотни онлайн-курсов от ведущих экспертов",
                "Обширная библиотека стоматологических книг и материалов",
                "Доступные цены и специальные предложения",
                "Обучайтесь в своём темпе, в любое время и в любом месте"
            ],
            "cta": "Присоединяйтесь к Dent-S сегодня и начните своё обучение!",
            "button": "Посмотреть платформу",
            "footer": "Это приглашение отправлено пользователем {sender}. Если вы получили это письмо по ошибке, просто проигнорируйте его."
        },
        "ES": {
            "subject": "¡Te han invitado a la plataforma Dent-S!",
            "heading": "Únete a Dent-S",
            "greeting": f"¡{sender_email} te invita a unirte a nuestra plataforma de formación dental online!",
            "intro": "Descubre un mundo de educación dental profesional al alcance de tu mano.",
            "benefits_title": "Lo que te espera:",
            "benefits": [
                "Cientos de cursos online de expertos líderes",
                "Amplia biblioteca de libros y materiales dentales",
                "Precios asequibles y ofertas especiales",
                "Aprende a tu propio ritmo, en cualquier momento y lugar"
            ],
            "cta": "¡Únete a Dent-S hoy y comienza tu viaje de aprendizaje!",
            "button": "Ver plataforma",
            "footer": "Esta invitación fue enviada por {sender}. Si recibiste este correo por error, ignóralo."
        },
        "IT": {
            "subject": "Sei stato invitato alla piattaforma Dent-S!",
            "heading": "Unisciti a Dent-S",
            "greeting": f"{sender_email} ti invita a unirti alla nostra piattaforma di formazione odontoiatrica online!",
            "intro": "Scopri un mondo di educazione dentale professionale a portata di mano.",
            "benefits_title": "Cosa ti aspetta:",
            "benefits": [
                "Centinaia di corsi online da esperti di primo piano",
                "Vasta biblioteca di libri e materiali dentali",
                "Prezzi accessibili e offerte speciali",
                "Impara al tuo ritmo, sempre e ovunque"
            ],
            "cta": "Unisciti a Dent-S oggi e inizia il tuo percorso di apprendimento!",
            "button": "Visualizza piattaforma",
            "footer": "Questo invito è stato inviato da {sender}. Se hai ricevuto questa email per errore, ignorala."
        },
        "PT": {
            "subject": "Você foi convidado para a plataforma Dent-S!",
            "heading": "Junte-se ao Dent-S",
            "greeting": f"{sender_email} convida você para nossa plataforma de ensino odontológico online!",
            "intro": "Descubra um mundo de educação odontológica profissional ao seu alcance.",
            "benefits_title": "O que te espera:",
            "benefits": [
                "Centenas de cursos online de especialistas líderes",
                "Ampla biblioteca de livros e materiais odontológicos",
                "Preços acessíveis e ofertas especiais",
                "Aprenda no seu ritmo, a qualquer hora e em qualquer lugar"
            ],
            "cta": "Junte-se ao Dent-S hoje e comece sua jornada de aprendizado!",
            "button": "Ver plataforma",
            "footer": "Este convite foi enviado por {sender}. Se você recebeu este email por engano, ignore-o."
        },
        "AR": {
            "subject": "تمت دعوتك إلى منصة Dent-S!",
            "heading": "انضم إلى Dent-S",
            "greeting": f"{sender_email} يدعوك للانضمام إلى منصتنا للتعليم الإلكتروني في طب الأسنان!",
            "intro": "اكتشف عالم التعليم المهني في طب الأسنان في متناول يدك.",
            "benefits_title": "ما ينتظرك:",
            "benefits": [
                "المئات من الدورات عبر الإنترنت من الخبراء الرائدين",
                "مكتبة واسعة من كتب ومواد طب الأسنان",
                "أسعار معقولة وعروض خاصة",
                "تعلم بالسرعة التي تناسبك، في أي وقت وفي أي مكان"
            ],
            "cta": "انضم إلى Dent-S اليوم وابدأ رحلتك التعليمية!",
            "button": "عرض المنصة",
            "footer": "تم إرسال هذه الدعوة من قبل {sender}. إذا تلقيت هذا البريد الإلكتروني بالخطأ، يرجى تجاهله."
        },
    }
    
    loc = translations.get(region.upper(), translations["EN"])
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""
    
    benefits_html = "".join([f"<li style='margin:8px 0;'>{b}</li>" for b in loc["benefits"]])
    
    body_html = f"""\
<!DOCTYPE html>
<html lang="{region.lower()}"{html_dir}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{loc["subject"]}</title>
</head>
<body style="margin:0;padding:20px;background:#7fdfd5;font-family:Arial,sans-serif;color:#01433d;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
      <a href="https://dent-s.com/">
        <img src="https://cdn.dent-s.com/logo-dents.png" width="150" style="max-width:150px;width:100%;">
      </a>
    </td></tr>
    <tr><td align="center">
      <table cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#edf8ff;border-radius:20px;padding:20px;box-shadow:0 0 10px rgba(0,0,0,0.08);text-align:center;">
        <tr><td>
          <h2 style="margin:0 0 16px;font-size:32px;color:#7fdfd5;font-weight:600;">{loc["heading"]}</h2>
        </td></tr>
        <tr><td style="font-size:18px;line-height:28px;font-weight:500;padding:10px;text-align:left;">
          <p style="margin:0 0 16px;font-size:20px;font-weight:600;text-align:center;">{loc["greeting"]}</p>
          <p style="margin:0 0 16px;">{loc["intro"]}</p>
          <p style="margin:16px 0 8px;font-size:20px;font-weight:600;color:#01433d;">{loc["benefits_title"]}</p>
          <ul style="margin:0 0 16px;padding-left:20px;text-align:left;">
            {benefits_html}
          </ul>
          <p style="margin:16px 0 24px;font-weight:600;text-align:center;">{loc["cta"]}</p>
          <p style="margin:24px 0;text-align:center;">
            <a href="{register_url}" style="display:inline-block;padding:14px 40px;background:#01433d;color:#edf8ff;text-decoration:none;border-radius:40px;font-weight:600;font-size:18px;">{loc["button"]}</a>
          </p>
          <p style="margin:20px 0 0;font-size:14px;color:#64748b;text-align:center;">{loc["footer"].format(sender=sender_email)}</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    send_html_email(recipient_email, loc["subject"], body_html)


# --------------------------------------------------------------------------
#  ПОДТВЕРЖДЕНИЕ ОТПРАВКИ ПРИГЛАШЕНИЯ
# --------------------------------------------------------------------------
def send_invitation_confirmation_email(
    sender_email: str,
    recipient_email: str,
    region: str = "EN"
) -> None:
    """Письмо-подтверждение отправителю о том, что приглашение отправлено."""
    referral_url = "https://dent-s.com/referrals"
    
    translations = {
        "EN": {
            "subject": "Invitation sent successfully",
            "heading": "Invitation Sent!",
            "message": f"You have successfully sent an invitation to <strong>{recipient_email}</strong>.",
            "info": "If they register using your referral link, you will receive 50% cashback from all their purchases on the platform.",
            "tip_title": "How it works:",
            "tips": [
                "Your colleague registers using your unique link",
                "They make purchases on the platform",
                "You automatically receive 50% of the purchase amount to your balance",
                "You can use the balance to purchase any courses or books"
            ],
            "cta": "Track your referrals and earnings in your personal account.",
            "button": "View My Referrals",
            "footer": "Thank you for helping Dent-S grow!"
        },
        "RU": {
            "subject": "Приглашение успешно отправлено",
            "heading": "Приглашение отправлено!",
            "message": f"Вы успешно отправили приглашение для <strong>{recipient_email}</strong>.",
            "info": "Если они зарегистрируются по вашей реферальной ссылке, вы будете получать 50% кэшбэка со всех их покупок на платформе.",
            "tip_title": "Как это работает:",
            "tips": [
                "Ваш коллега регистрируется по вашей уникальной ссылке",
                "Он совершает покупки на платформе",
                "Вы автоматически получаете 50% от суммы покупки на свой баланс",
                "Вы можете использовать баланс для покупки любых курсов или книг"
            ],
            "cta": "Отслеживайте своих рефералов и заработок в личном кабинете.",
            "button": "Мои рефералы",
            "footer": "Спасибо, что помогаете Dent-S расти!"
        },
        "ES": {
            "subject": "Invitación enviada con éxito",
            "heading": "¡Invitación enviada!",
            "message": f"Has enviado con éxito una invitación a <strong>{recipient_email}</strong>.",
            "info": "Si se registran usando tu enlace de referido, recibirás 50% de cashback de todas sus compras en la plataforma.",
            "tip_title": "Cómo funciona:",
            "tips": [
                "Tu colega se registra usando tu enlace único",
                "Realizan compras en la plataforma",
                "Recibes automáticamente el 50% del monto de la compra en tu saldo",
                "Puedes usar el saldo para comprar cualquier curso o libro"
            ],
            "cta": "Rastrea tus referidos y ganancias en tu cuenta personal.",
            "button": "Ver mis referidos",
            "footer": "¡Gracias por ayudar a crecer a Dent-S!"
        },
        "IT": {
            "subject": "Invito inviato con successo",
            "heading": "Invito inviato!",
            "message": f"Hai inviato con successo un invito a <strong>{recipient_email}</strong>.",
            "info": "Se si registrano usando il tuo link referral, riceverai il 50% di cashback da tutti i loro acquisti sulla piattaforma.",
            "tip_title": "Come funziona:",
            "tips": [
                "Il tuo collega si registra usando il tuo link unico",
                "Effettuano acquisti sulla piattaforma",
                "Ricevi automaticamente il 50% dell'importo dell'acquisto sul tuo saldo",
                "Puoi usare il saldo per acquistare qualsiasi corso o libro"
            ],
            "cta": "Traccia i tuoi referral e guadagni nel tuo account personale.",
            "button": "Visualizza i miei referral",
            "footer": "Grazie per aiutare Dent-S a crescere!"
        },
        "PT": {
            "subject": "Convite enviado com sucesso",
            "heading": "Convite enviado!",
            "message": f"Você enviou com sucesso um convite para <strong>{recipient_email}</strong>.",
            "info": "Se eles se registrarem usando seu link de indicação, você receberá 50% de cashback de todas as compras deles na plataforma.",
            "tip_title": "Como funciona:",
            "tips": [
                "Seu colega se registra usando seu link único",
                "Eles fazem compras na plataforma",
                "Você recebe automaticamente 50% do valor da compra em seu saldo",
                "Você pode usar o saldo para comprar qualquer curso ou livro"
            ],
            "cta": "Acompanhe suas indicações e ganhos em sua conta pessoal.",
            "button": "Ver minhas indicações",
            "footer": "Obrigado por ajudar o Dent-S a crescer!"
        },
        "AR": {
            "subject": "تم إرسال الدعوة بنجاح",
            "heading": "تم إرسال الدعوة!",
            "message": f"لقد أرسلت بنجاح دعوة إلى <strong>{recipient_email}</strong>.",
            "info": "إذا قاموا بالتسجيل باستخدام رابط الإحالة الخاص بك، ستحصل على 50% استرداد نقدي من جميع مشترياتهم على المنصة.",
            "tip_title": "كيف يعمل:",
            "tips": [
                "يسجل زميلك باستخدام رابطك الفريد",
                "يقومون بإجراء مشتريات على المنصة",
                "تحصل تلقائيًا على 50% من قيمة الشراء في رصيدك",
                "يمكنك استخدام الرصيد لشراء أي دورات أو كتب"
            ],
            "cta": "تتبع إحالاتك وأرباحك في حسابك الشخصي.",
            "button": "عرض إحالاتي",
            "footer": "شكرًا لمساعدتك Dent-S على النمو!"
        },
    }
    
    loc = translations.get(region.upper(), translations["EN"])
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""
    
    tips_html = "".join([f"<li style='margin:8px 0;'>{t}</li>" for t in loc["tips"]])
    
    body_html = f"""\
<!DOCTYPE html>
<html lang="{region.lower()}"{html_dir}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{loc["subject"]}</title>
</head>
<body style="margin:0;padding:20px;background:#7fdfd5;font-family:Arial,sans-serif;color:#01433d;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
      <a href="https://dent-s.com/">
        <img src="https://cdn.dent-s.com/logo-dents.png" width="150" style="max-width:150px;width:100%;">
      </a>
    </td></tr>
    <tr><td align="center">
      <table cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#edf8ff;border-radius:20px;padding:20px;box-shadow:0 0 10px rgba(0,0,0,0.08);">
        <tr><td>
          <h2 style="margin:0 0 16px;font-size:32px;color:#7fdfd5;font-weight:600;text-align:center;">{loc["heading"]}</h2>
        </td></tr>
        <tr><td style="font-size:18px;line-height:28px;font-weight:500;padding:10px;">
          <p style="margin:0 0 16px;text-align:center;">{loc["message"]}</p>
          <p style="margin:0 0 16px;">{loc["info"]}</p>
          <p style="margin:16px 0 8px;font-size:20px;font-weight:600;color:#01433d;">{loc["tip_title"]}</p>
          <ul style="margin:0 0 16px;padding-left:20px;">
            {tips_html}
          </ul>
          <p style="margin:16px 0 24px;font-weight:500;text-align:center;">{loc["cta"]}</p>
          <p style="margin:24px 0;text-align:center;">
            <a href="{referral_url}" style="display:inline-block;padding:14px 40px;background:#01433d;color:#edf8ff;text-decoration:none;border-radius:40px;font-weight:600;font-size:18px;">{loc["button"]}</a>
          </p>
          <p style="margin:20px 0 0;font-size:14px;color:#64748b;text-align:center;">{loc["footer"]}</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    send_html_email(sender_email, loc["subject"], body_html)


# --------------------------------------------------------------------------
#  НАПОМИНАНИЕ О КОРЗИНЕ (большая корзина)
# --------------------------------------------------------------------------
def send_big_cart_reminder_email(
    recipient_email: str,
    region: str = "EN"
) -> bool:
    """
    Напоминание о незавершённой корзине со скидкой.
    Возвращает True при успешной отправке, False при ошибке.
    """
    site_url = "https://dent-s.com/"

    translations = {
        "EN": {
            "subject": "Your cart is waiting for you!",
            "heading": "Your Cart is Waiting!",
            "greeting": "Hello!",
            "line1": "You've selected some great courses but haven't completed your purchase yet.",
            "line2": "Right now we have special discounts that won't last long.",
            "line3": "Don't miss your chance to get these courses at the best price!",
            "urgency": "Hurry — the offer expires soon!",
            "button": "Complete Purchase",
            "footer": "This is an automated message. Please do not reply."
        },
        "RU": {
            "subject": "Ваша корзина ждёт вас!",
            "heading": "Ваша корзина ждёт!",
            "greeting": "Здравствуйте!",
            "line1": "Вы выбрали отличные курсы, но ещё не завершили покупку.",
            "line2": "Прямо сейчас у нас действуют специальные скидки, которые скоро закончатся.",
            "line3": "Не упустите возможность приобрести эти курсы по лучшей цене!",
            "urgency": "Поторопитесь — предложение скоро истекает!",
            "button": "Завершить покупку",
            "footer": "Это автоматическое сообщение. Пожалуйста, не отвечайте."
        },
        "ES": {
            "subject": "¡Tu carrito te está esperando!",
            "heading": "¡Tu Carrito te Espera!",
            "greeting": "¡Hola!",
            "line1": "Has seleccionado excelentes cursos pero aún no has completado tu compra.",
            "line2": "Ahora mismo tenemos descuentos especiales que no durarán mucho.",
            "line3": "¡No pierdas la oportunidad de obtener estos cursos al mejor precio!",
            "urgency": "¡Date prisa — la oferta expira pronto!",
            "button": "Completar compra",
            "footer": "Este es un mensaje automático. Por favor, no responda."
        },
        "IT": {
            "subject": "Il tuo carrello ti aspetta!",
            "heading": "Il Tuo Carrello ti Aspetta!",
            "greeting": "Ciao!",
            "line1": "Hai selezionato ottimi corsi ma non hai ancora completato l'acquisto.",
            "line2": "In questo momento abbiamo sconti speciali che non dureranno a lungo.",
            "line3": "Non perdere l'occasione di acquistare questi corsi al miglior prezzo!",
            "urgency": "Affrettati — l'offerta scade presto!",
            "button": "Completa l'acquisto",
            "footer": "Questo è un messaggio automatico. Si prega di non rispondere."
        },
        "PT": {
            "subject": "Seu carrinho está esperando por você!",
            "heading": "Seu Carrinho Está Esperando!",
            "greeting": "Olá!",
            "line1": "Você selecionou ótimos cursos, mas ainda não finalizou a compra.",
            "line2": "Neste momento temos descontos especiais que não vão durar muito.",
            "line3": "Não perca a chance de adquirir esses cursos pelo melhor preço!",
            "urgency": "Corra — a oferta expira em breve!",
            "button": "Finalizar compra",
            "footer": "Esta é uma mensagem automática. Por favor, não responda."
        },
        "AR": {
            "subject": "سلة التسوق الخاصة بك في انتظارك!",
            "heading": "سلتك في انتظارك!",
            "greeting": "مرحبًا!",
            "line1": "لقد اخترت دورات رائعة لكنك لم تكمل عملية الشراء بعد.",
            "line2": "لدينا الآن خصومات خاصة لن تستمر طويلاً.",
            "line3": "لا تفوّت فرصة الحصول على هذه الدورات بأفضل سعر!",
            "urgency": "أسرع — العرض ينتهي قريبًا!",
            "button": "إتمام الشراء",
            "footer": "هذه رسالة آلية. يرجى عدم الرد."
        },
    }

    loc = translations.get(region.upper(), translations["EN"])
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""

    body_html = f"""\
<!DOCTYPE html>
<html lang="{region.lower()}"{html_dir}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{loc["subject"]}</title>
</head>
<body style="margin:0;padding:20px;background:#7fdfd5;font-family:Arial,sans-serif;color:#01433d;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
      <a href="{site_url}">
        <img src="https://cdn.dent-s.com/logo-dents.png" width="150" style="max-width:150px;width:100%;">
      </a>
    </td></tr>
    <tr><td align="center">
      <table cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#edf8ff;border-radius:20px;padding:20px;box-shadow:0 0 10px rgba(0,0,0,0.08);text-align:center;">
        <tr><td>
          <h2 style="margin:0 0 16px;font-size:32px;color:#7fdfd5;font-weight:600;">{loc["heading"]}</h2>
        </td></tr>
        <tr><td style="font-size:18px;line-height:28px;font-weight:500;padding:10px;text-align:left;">
          <p style="margin:0 0 16px;font-size:20px;font-weight:600;text-align:center;">{loc["greeting"]}</p>
          <p style="margin:0 0 16px;">{loc["line1"]}</p>
          <p style="margin:0 0 16px;">{loc["line2"]}</p>
          <p style="margin:0 0 16px;font-weight:600;">{loc["line3"]}</p>
          <p style="margin:24px 0;font-size:22px;font-weight:700;color:#01433d;text-align:center;background:#7fdfd5;padding:16px;border-radius:12px;">{loc["urgency"]}</p>
          <p style="margin:24px 0;text-align:center;">
            <a href="{site_url}" style="display:inline-block;padding:14px 40px;background:#01433d;color:#edf8ff;text-decoration:none;border-radius:40px;font-weight:600;font-size:18px;">{loc["button"]}</a>
          </p>
          <p style="margin:20px 0 0;font-size:14px;color:#64748b;text-align:center;">{loc["footer"]}</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    return send_html_email(recipient_email, loc["subject"], body_html)

def send_referral_program_email(
    recipient_email: str,
    referral_link: str,
    region: str = "EN",
    bonus_percent: int = 50,
) -> bool:
    """
    Письмо про реферальную программу Dent-S.
    Информирует пользователя о возможности приглашать друзей и получать 50% кешбэк.
    """
    site_url = "https://dent-s.com"
    profile_url = "https://dent-s.com/profile"

    translations = {
        "RU": {
            "subject": "Реферальная программа Dent-S — зарабатывайте с каждой покупки друзей!",
            "heading": "Реферальная программа",
            "greeting": "Здравствуйте!",
            "intro": f"У нас отличные новости! Теперь вы можете получать <strong>{bonus_percent}% кешбэка</strong> с каждой покупки ваших приглашённых друзей и коллег.",
            "spend_info": "Накопленный кешбэк можно потратить на любые <strong>курсы и книги</strong> на нашем сайте.",
            "how_title": "Как это работает:",
            "steps": [
                "Поделитесь своей реферальной ссылкой с коллегами",
                "Они регистрируются и совершают покупки на платформе",
                f"Вы автоматически получаете {bonus_percent}% от суммы их покупок на свой баланс",
                "Используйте баланс для оплаты курсов и книг"
            ],
            "simple_title": "Всё очень просто!",
            "simple_info": "Подробное руководство по реферальной программе доступно в вашем <strong>личном кабинете</strong>.",
            "privacy_title": "Полная конфиденциальность",
            "privacy_info": "Приглашённый пользователь <strong>не узнает</strong>, что вам возвращаются деньги с его покупок. Это остаётся между вами и нами.",
            "your_link": "Ваша персональная ссылка:",
            "btn_site": "Перейти на сайт",
            "btn_profile": "Личный кабинет",
            "footer": "Это автоматическое сообщение. Пожалуйста, не отвечайте на него."
        },
        "EN": {
            "subject": "Dent-S Referral Program — Earn from every friend's purchase!",
            "heading": "Referral Program",
            "greeting": "Hello!",
            "intro": f"Great news! You can now earn <strong>{bonus_percent}% cashback</strong> from every purchase made by your invited friends and colleagues.",
            "spend_info": "You can spend your accumulated cashback on any <strong>courses and books</strong> on our website.",
            "how_title": "How it works:",
            "steps": [
                "Share your referral link with colleagues",
                "They register and make purchases on the platform",
                f"You automatically receive {bonus_percent}% of their purchase amount to your balance",
                "Use your balance to pay for courses and books"
            ],
            "simple_title": "It's that simple!",
            "simple_info": "A detailed guide to the referral program is available in your <strong>personal account</strong>.",
            "privacy_title": "Complete Privacy",
            "privacy_info": "The invited user <strong>will not know</strong> that you receive money back from their purchases. It stays between you and us.",
            "your_link": "Your personal link:",
            "btn_site": "Visit Website",
            "btn_profile": "My Account",
            "footer": "This is an automated message. Please do not reply."
        },
        "ES": {
            "subject": "Programa de referidos Dent-S — ¡Gana con cada compra de tus amigos!",
            "heading": "Programa de Referidos",
            "greeting": "¡Hola!",
            "intro": f"¡Grandes noticias! Ahora puedes ganar <strong>{bonus_percent}% de cashback</strong> de cada compra realizada por tus amigos y colegas invitados.",
            "spend_info": "Puedes gastar tu cashback acumulado en cualquier <strong>curso y libro</strong> de nuestro sitio web.",
            "how_title": "Cómo funciona:",
            "steps": [
                "Comparte tu enlace de referido con colegas",
                "Ellos se registran y hacen compras en la plataforma",
                f"Recibes automáticamente el {bonus_percent}% del monto de sus compras en tu saldo",
                "Usa tu saldo para pagar cursos y libros"
            ],
            "simple_title": "¡Así de simple!",
            "simple_info": "Una guía detallada del programa de referidos está disponible en tu <strong>cuenta personal</strong>.",
            "privacy_title": "Privacidad Total",
            "privacy_info": "El usuario invitado <strong>no sabrá</strong> que recibes dinero de sus compras. Queda entre tú y nosotros.",
            "your_link": "Tu enlace personal:",
            "btn_site": "Visitar Sitio",
            "btn_profile": "Mi Cuenta",
            "footer": "Este es un mensaje automático. Por favor, no responda."
        },
        "IT": {
            "subject": "Programma Referral Dent-S — Guadagna da ogni acquisto dei tuoi amici!",
            "heading": "Programma Referral",
            "greeting": "Ciao!",
            "intro": f"Ottime notizie! Ora puoi guadagnare <strong>{bonus_percent}% di cashback</strong> da ogni acquisto effettuato dai tuoi amici e colleghi invitati.",
            "spend_info": "Puoi spendere il cashback accumulato su qualsiasi <strong>corso e libro</strong> sul nostro sito.",
            "how_title": "Come funziona:",
            "steps": [
                "Condividi il tuo link referral con i colleghi",
                "Si registrano e fanno acquisti sulla piattaforma",
                f"Ricevi automaticamente il {bonus_percent}% dell'importo dei loro acquisti sul tuo saldo",
                "Usa il saldo per pagare corsi e libri"
            ],
            "simple_title": "È così semplice!",
            "simple_info": "Una guida dettagliata al programma referral è disponibile nel tuo <strong>account personale</strong>.",
            "privacy_title": "Privacy Totale",
            "privacy_info": "L'utente invitato <strong>non saprà</strong> che ricevi denaro dai suoi acquisti. Resta tra te e noi.",
            "your_link": "Il tuo link personale:",
            "btn_site": "Visita il Sito",
            "btn_profile": "Il Mio Account",
            "footer": "Questo è un messaggio automatico. Si prega di non rispondere."
        },
        "PT": {
            "subject": "Programa de Indicação Dent-S — Ganhe com cada compra dos seus amigos!",
            "heading": "Programa de Indicação",
            "greeting": "Olá!",
            "intro": f"Ótimas notícias! Agora você pode ganhar <strong>{bonus_percent}% de cashback</strong> de cada compra feita pelos seus amigos e colegas convidados.",
            "spend_info": "Você pode gastar seu cashback acumulado em qualquer <strong>curso e livro</strong> em nosso site.",
            "how_title": "Como funciona:",
            "steps": [
                "Compartilhe seu link de indicação com colegas",
                "Eles se cadastram e fazem compras na plataforma",
                f"Você recebe automaticamente {bonus_percent}% do valor das compras deles em seu saldo",
                "Use seu saldo para pagar cursos e livros"
            ],
            "simple_title": "É simples assim!",
            "simple_info": "Um guia detalhado do programa de indicação está disponível em sua <strong>conta pessoal</strong>.",
            "privacy_title": "Privacidade Total",
            "privacy_info": "O usuário convidado <strong>não saberá</strong> que você recebe dinheiro das compras dele. Fica entre você e nós.",
            "your_link": "Seu link pessoal:",
            "btn_site": "Visitar Site",
            "btn_profile": "Minha Conta",
            "footer": "Esta é uma mensagem automática. Por favor, não responda."
        },
        "AR": {
            "subject": "برنامج الإحالة Dent-S — اربح من كل عملية شراء لأصدقائك!",
            "heading": "برنامج الإحالة",
            "greeting": "مرحبًا!",
            "intro": f"أخبار رائعة! يمكنك الآن كسب <strong>{bonus_percent}% استرداد نقدي</strong> من كل عملية شراء يقوم بها أصدقاؤك وزملاؤك المدعوون.",
            "spend_info": "يمكنك إنفاق رصيدك المتراكم على أي <strong>دورات وكتب</strong> على موقعنا.",
            "how_title": "كيف يعمل:",
            "steps": [
                "شارك رابط الإحالة الخاص بك مع الزملاء",
                "يسجلون ويقومون بعمليات شراء على المنصة",
                f"تحصل تلقائيًا على {bonus_percent}% من قيمة مشترياتهم في رصيدك",
                "استخدم رصيدك لدفع ثمن الدورات والكتب"
            ],
            "simple_title": "إنها بهذه البساطة!",
            "simple_info": "دليل مفصل لبرنامج الإحالة متاح في <strong>حسابك الشخصي</strong>.",
            "privacy_title": "خصوصية تامة",
            "privacy_info": "المستخدم المدعو <strong>لن يعرف</strong> أنك تحصل على أموال من مشترياته. يبقى الأمر بينك وبيننا.",
            "your_link": "رابطك الشخصي:",
            "btn_site": "زيارة الموقع",
            "btn_profile": "حسابي",
            "footer": "هذه رسالة آلية. يرجى عدم الرد."
        },
    }

    loc = translations.get(region.upper(), translations["EN"])
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""

    steps_html = "".join([f'<li style="margin:10px 0;padding-left:8px;">{step}</li>' for step in loc["steps"]])

    body_html = f"""\
<!DOCTYPE html>
<html lang="{region.lower()}"{html_dir}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{loc["subject"]}</title>
</head>
<body style="margin:0;padding:20px;background:#7fdfd5;font-family:Arial,sans-serif;color:#01433d;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
      <a href="{site_url}">
        <img src="https://cdn.dent-s.com/logo-dents.png" width="150" style="max-width:150px;width:100%;">
      </a>
    </td></tr>
    <tr><td align="center">
      <table cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#edf8ff;border-radius:20px;padding:20px;box-shadow:0 0 10px rgba(0,0,0,0.08);">
        <tr><td>
          <h2 style="margin:0 0 16px;font-size:32px;color:#7fdfd5;font-weight:600;text-align:center;">{loc["heading"]}</h2>
        </td></tr>
        <tr><td style="font-size:18px;line-height:28px;font-weight:500;padding:10px;">
          <p style="margin:0 0 16px;font-size:20px;font-weight:600;text-align:center;">{loc["greeting"]}</p>
          <p style="margin:0 0 16px;">{loc["intro"]}</p>
          <p style="margin:0 0 20px;">{loc["spend_info"]}</p>

          <p style="margin:20px 0 12px;font-size:20px;font-weight:700;color:#01433d;">{loc["how_title"]}</p>
          <ol style="margin:0 0 20px;padding-left:20px;line-height:26px;">
            {steps_html}
          </ol>

          <div style="background:#7fdfd5;border-radius:16px;padding:20px;margin:20px 0;">
            <p style="margin:0 0 10px;font-size:20px;font-weight:700;color:#01433d;">{loc["simple_title"]}</p>
            <p style="margin:0;color:#01433d;">{loc["simple_info"]}</p>
          </div>

          <div style="background:#fff;border:2px solid #7fdfd5;border-radius:16px;padding:20px;margin:20px 0;">
            <p style="margin:0 0 10px;font-size:20px;font-weight:700;color:#01433d;">{loc["privacy_title"]}</p>
            <p style="margin:0;color:#01433d;">{loc["privacy_info"]}</p>
          </div>

          <p style="margin:24px 0 8px;font-size:16px;font-weight:600;color:#01433d;text-align:center;">{loc["your_link"]}</p>
          <p style="margin:0 0 24px;text-align:center;">
            <a href="{referral_link}" style="word-break:break-all;color:#017f74;font-weight:600;font-size:16px;">{referral_link}</a>
          </p>

          <p style="margin:24px 0;text-align:center;">
            <a href="{site_url}" style="display:inline-block;padding:14px 36px;background:#01433d;color:#edf8ff;text-decoration:none;border-radius:40px;font-weight:600;font-size:16px;margin:6px;">{loc["btn_site"]}</a>
            <a href="{profile_url}" style="display:inline-block;padding:14px 36px;background:#7fdfd5;color:#01433d;text-decoration:none;border-radius:40px;font-weight:600;font-size:16px;margin:6px;border:2px solid #01433d;">{loc["btn_profile"]}</a>
          </p>

          <p style="margin:30px 0 0;font-size:14px;color:#64748b;text-align:center;">{loc["footer"]}</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    return send_html_email(recipient_email, loc["subject"], body_html)
