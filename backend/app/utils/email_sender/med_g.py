"""
Med.G шаблоны.

"""

from .common import send_html_email
from .dent_s_courses_html import COURSES_BLOCK as BASE_COURSES_BLOCK

MED_G_DOMAIN = "https://med.g"
MED_G_COLOR = "#006d8d"


def send_password_to_user(recipient_email: str, password: str, region: str):
    """Отправка пароля при регистрации для Med.G."""
    subject = {
        "IT": "La tua password per Med.G",
        "EN": "Your Med.G password",
        "RU": "Ваш пароль Med.G",
        "ES": "Tu contraseña Med.G",
        "PT": "Sua senha Med.G",
        "AR": "كلمة المرور الخاصة بك Med.G",
    }.get(region.upper(), "Your Med.G password")

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
                  <p>Il tuo account è stato creato con successo.</p>
                  <p>La tua password è: <b>{password}</b></p>
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


def send_successful_purchase_email(
    recipient_email: str,
    course_names: list[str] | None = None,
    new_account: bool = False,
    password: str | None = None,
    region: str = "EN",
    book_titles: list[str] | None = None,
):
    """Письмо при успешной покупке: курсы и/или книги для Med.G."""
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
    }.get(region.upper(), {})

    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""

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

    html = f"""
    <html{html_dir}>
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
                  <h2 style="margin:0 0 20px 0;">{loc["heading_new"] if new_account else loc["heading_default"]}</h2>
                  {account_block}
                  {courses_block}
                  {books_block}
                  <p style="text-align:center;margin:30px 0;">
                    <a href="{MED_G_DOMAIN}/login"
                       style="background:{MED_G_COLOR};color:#fff;padding:12px 28px;
                       text-decoration:none;border-radius:25px;">{loc["login"]}</a>
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


def send_already_owned_course_email(
    recipient_email: str,
    course_names: list[str],
    region: str = "EN"
):
    """Уведомление о том, что курсы уже есть у пользователя для Med.G."""
    contact_email = "support@med.g"
    courses_str = ", ".join(course_names) if course_names else ""

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
    }

    loc = translations.get(region.upper(), translations["EN"])
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""

    html = f"""
    <html{html_dir}>
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
                  <h2 style="margin:0 0 20px 0;">{loc["heading"]}</h2>
                  <p>{loc["message"].format(courses=courses_str)}</p>
                  <p>{loc["action"].format(contact=contact_email)}</p>
                  <p style="text-align:center;margin:30px 0;">
                    <a href="{MED_G_DOMAIN}/login"
                       style="background:{MED_G_COLOR};color:#fff;padding:12px 28px;
                       text-decoration:none;border-radius:25px;">{loc["button"]}</a>
                  </p>
                  <p>{loc["thanks"]}</p>
                  <p>Distinti saluti,<br><b>Med.G Team</b></p>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
      </body>
    </html>
    """
    send_html_email(recipient_email, loc["subject"], html_body=html)


def send_invitation_email(
    recipient_email: str,
    sender_email: str,
    referral_code: str,
    region: str = "EN"
) -> None:
    """Письмо-приглашение от пользователя на платформу Med.G."""
    register_url = f"{MED_G_DOMAIN}/?rc={referral_code}"
    
    translations = {
        "EN": {
            "subject": "You've been invited to Med.G platform!",
            "heading": "Join Med.G Platform",
            "greeting": f"{sender_email} invites you to join our medical online learning platform!",
            "intro": "Discover a world of professional medical education at your fingertips.",
            "button": "Explore Platform",
        },
        "IT": {
            "subject": "Sei stato invitato alla piattaforma Med.G!",
            "heading": "Unisciti a Med.G",
            "greeting": f"{sender_email} ti invita a unirti alla nostra piattaforma di formazione medica online!",
            "intro": "Scopri un mondo di educazione medica professionale a portata di mano.",
            "button": "Visualizza piattaforma",
        },
        "RU": {
            "subject": "Вас пригласили на платформу Med.G!",
            "heading": "Присоединяйтесь к Med.G",
            "greeting": f"{sender_email} приглашает вас на нашу платформу медицинского онлайн-обучения!",
            "intro": "Откройте для себя мир профессионального медицинского образования.",
            "button": "Посмотреть платформу",
        },
    }
    
    loc = translations.get(region.upper(), translations["EN"])
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""
    
    html = f"""
    <html{html_dir}>
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
                  <h2 style="margin:0 0 20px 0;">{loc["heading"]}</h2>
                  <p>{loc["greeting"]}</p>
                  <p>{loc["intro"]}</p>
                  <p style="text-align:center;margin:30px 0;">
                    <a href="{register_url}"
                       style="background:{MED_G_COLOR};color:#fff;padding:12px 28px;
                       text-decoration:none;border-radius:25px;">{loc["button"]}</a>
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
    send_html_email(recipient_email, loc["subject"], html_body=html)


def send_invitation_confirmation_email(
    sender_email: str,
    recipient_email: str,
    region: str = "EN"
) -> None:
    """Письмо-подтверждение отправителю о том, что приглашение отправлено для Med.G."""
    referral_url = f"{MED_G_DOMAIN}/referrals"
    
    translations = {
        "EN": {
            "subject": "Invitation sent successfully",
            "heading": "Invitation Sent!",
            "message": f"You have successfully sent an invitation to <strong>{recipient_email}</strong>.",
            "info": "If they register using your referral link, you will receive 50% cashback from all their purchases on the platform.",
            "button": "View My Referrals",
        },
        "IT": {
            "subject": "Invito inviato con successo",
            "heading": "Invito inviato!",
            "message": f"Hai inviato con successo un invito a <strong>{recipient_email}</strong>.",
            "info": "Se si registrano usando il tuo link referral, riceverai il 50% di cashback da tutti i loro acquisti sulla piattaforma.",
            "button": "Visualizza i miei referral",
        },
        "RU": {
            "subject": "Приглашение успешно отправлено",
            "heading": "Приглашение отправлено!",
            "message": f"Вы успешно отправили приглашение для <strong>{recipient_email}</strong>.",
            "info": "Если они зарегистрируются по вашей реферальной ссылке, вы будете получать 50% кэшбэка со всех их покупок на платформе.",
            "button": "Мои рефералы",
        },
    }
    
    loc = translations.get(region.upper(), translations["EN"])
    html_dir = ' dir="rtl"' if region.upper() == "AR" else ""
    
    html = f"""
    <html{html_dir}>
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
                  <h2 style="margin:0 0 20px 0;">{loc["heading"]}</h2>
                  <p>{loc["message"]}</p>
                  <p>{loc["info"]}</p>
                  <p style="text-align:center;margin:30px 0;">
                    <a href="{referral_url}"
                       style="background:{MED_G_COLOR};color:#fff;padding:12px 28px;
                       text-decoration:none;border-radius:25px;">{loc["button"]}</a>
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
    send_html_email(sender_email, loc["subject"], html_body=html)


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
