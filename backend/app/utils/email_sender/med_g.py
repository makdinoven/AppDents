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
            "access_info": "You can log in anytime, from any device or browser, using your email and password to access your purchased content:",
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

    access_block = f"""
        <div style="margin-top:16px;padding:12px;background-color:#e0f4f4;border-radius:8px;border-left:4px solid {MED_G_COLOR};">
          <p style="margin:0;font-size:14px;color:{MED_G_COLOR};">
            {loc.get("access_info", "You can log in anytime, from any device or browser, using your email and password to access your purchased content:")}
            <a href="{MED_G_DOMAIN}" style="color:#004d5c;font-weight:600;">med-g.com</a>
          </p>
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
                  {access_block}
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

    html = f"""\
<!DOCTYPE html>
<html lang="{region.lower()}"{html_dir}>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{loc["subject"]}</title>
</head>
<body style="margin:0;padding:0;background-color:#f3f7f8;font-family:'Segoe UI',sans-serif;">
  <table width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#f3f7f8">
    <tr><td align="center">
      <a href="{MED_G_DOMAIN}/">
        <img src="{MED_G_DOMAIN}/static/logo-medg.png" alt="Med.G" width="150" style="max-width:150px;width:100%;">
      </a>
    </td></tr>
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border-radius:12px;margin:30px 0;">
        <tr>
          <td style="padding:30px 40px;color:{MED_G_COLOR};">
            <h2 style="margin:0 0 20px 0;font-size:28px;text-align:center;">{loc["heading"]}</h2>
            <p style="margin:0 0 16px;font-size:18px;font-weight:600;text-align:center;">{loc["greeting"]}</p>
            <p style="margin:0 0 16px;font-size:16px;line-height:24px;">{loc["line1"]}</p>
            <p style="margin:0 0 16px;font-size:16px;line-height:24px;">{loc["line2"]}</p>
            <p style="margin:0 0 16px;font-size:16px;line-height:24px;font-weight:600;">{loc["line3"]}</p>
            <p style="margin:24px 0;font-size:18px;font-weight:700;text-align:center;background:#e0f4f4;color:{MED_G_COLOR};padding:16px;border-radius:8px;">{loc["urgency"]}</p>
            <p style="text-align:center;margin:30px 0;">
              <a href="{MED_G_DOMAIN}/"
                 style="background:{MED_G_COLOR};color:#fff;padding:14px 40px;
                 text-decoration:none;border-radius:25px;font-weight:600;font-size:16px;display:inline-block;">{loc["button"]}</a>
            </p>
            <p style="margin:20px 0 0;font-size:13px;color:#64748b;text-align:center;">{loc["footer"]}</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    return send_html_email(recipient_email, loc["subject"], html_body=html)


def send_referral_program_email(
    recipient_email: str,
    referral_link: str,
    region: str = "EN",
    bonus_percent: int = 50,
) -> bool:
    """
    Письмо про реферальную программу Med.G.
    Информирует пользователя о возможности приглашать друзей и получать 50% кешбэк.
    """
    profile_url = f"{MED_G_DOMAIN}/profile"

    translations = {
        "EN": {
            "subject": "Your Med.G referral link",
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
        "IT": {
            "subject": "Il tuo link referral Med.G",
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
        "RU": {
            "subject": "Ваша реферальная ссылка Med.G",
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
        "ES": {
            "subject": "Tu enlace de referidos de Med.G",
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
<body style="margin:0;padding:0;background-color:#f3f7f8;font-family:'Segoe UI',sans-serif;">
  <table width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#f3f7f8">
    <tr><td align="center" style="padding:30px 0 20px 0;">
      <a href="{MED_G_DOMAIN}/">
        <img src="{MED_G_DOMAIN}/static/logo-medg.png" alt="Med.G" width="150" />
      </a>
    </td></tr>
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border-radius:12px;margin:0 0 30px 0;">
        <tr>
          <td style="padding:30px 40px;color:{MED_G_COLOR};">
            <h2 style="margin:0 0 20px 0;font-size:28px;text-align:center;">{loc["heading"]}</h2>
            <p style="margin:0 0 16px;font-size:18px;font-weight:600;text-align:center;">{loc["greeting"]}</p>
            <p style="margin:0 0 16px;font-size:16px;line-height:24px;">{loc["intro"]}</p>
            <p style="margin:0 0 20px;font-size:16px;line-height:24px;">{loc["spend_info"]}</p>

            <p style="margin:20px 0 12px;font-size:18px;font-weight:700;color:{MED_G_COLOR};">{loc["how_title"]}</p>
            <ol style="margin:0 0 20px;padding-left:20px;font-size:16px;line-height:24px;">
              {steps_html}
            </ol>

            <div style="background:#e0f4f4;border-radius:12px;padding:20px;margin:20px 0;">
              <p style="margin:0 0 10px;font-size:18px;font-weight:700;color:{MED_G_COLOR};">{loc["simple_title"]}</p>
              <p style="margin:0;font-size:15px;line-height:22px;color:{MED_G_COLOR};">{loc["simple_info"]}</p>
            </div>

            <div style="background:#fff;border:2px solid {MED_G_COLOR};border-radius:12px;padding:20px;margin:20px 0;">
              <p style="margin:0 0 10px;font-size:18px;font-weight:700;color:{MED_G_COLOR};">{loc["privacy_title"]}</p>
              <p style="margin:0;font-size:15px;line-height:22px;color:{MED_G_COLOR};">{loc["privacy_info"]}</p>
            </div>

            <p style="margin:24px 0 8px;font-size:14px;font-weight:600;color:{MED_G_COLOR};text-align:center;">{loc["your_link"]}</p>
            <p style="margin:0 0 24px;text-align:center;">
              <a href="{referral_link}" style="word-break:break-all;color:{MED_G_COLOR};font-weight:600;font-size:14px;">{referral_link}</a>
            </p>

            <p style="text-align:center;margin:30px 0 20px;">
              <a href="{MED_G_DOMAIN}/"
                 style="display:inline-block;background:{MED_G_COLOR};color:#fff;padding:14px 32px;
                 text-decoration:none;border-radius:25px;font-weight:600;font-size:15px;margin:6px;">{loc["btn_site"]}</a>
              <a href="{profile_url}"
                 style="display:inline-block;background:#fff;color:{MED_G_COLOR};padding:12px 30px;
                 text-decoration:none;border-radius:25px;font-weight:600;font-size:15px;margin:6px;border:2px solid {MED_G_COLOR};">{loc["btn_profile"]}</a>
            </p>

            <p style="margin:20px 0 0;font-size:13px;color:#64748b;text-align:center;">{loc["footer"]}</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    text_body = "\n".join(
        [
            f"{loc['heading']}",
            "",
            loc["greeting"],
            "",
            f"You can earn {bonus_percent}% cashback from invited users' purchases."
            if region.upper() != "RU"
            else f"Вы можете получать {bonus_percent}% кешбэка с покупок приглашённых пользователей.",
            "",
            f"{loc['your_link']}",
            referral_link,
            "",
            loc["footer"],
        ]
    )

    mailgun_options = {
        "o:tracking": "no",
        "o:tracking-clicks": "no",
        "o:tracking-opens": "no",
    }

    return send_html_email(
        recipient_email,
        loc["subject"],
        body_html=body_html,
        text_body=text_body,
        mailgun_options=mailgun_options,
    )
