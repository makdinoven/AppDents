# backend/app/tasks/ny2026_leads.py
from __future__ import annotations

import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..models.models_v2 import Lead, EmailCampaign, EmailCampaignRecipient, EmailCampaignRecipientStatus
from ..services_v2.lead_campaign_service import skip_send_and_cleanup_if_user_exists, normalize_email
from ..services_v2.email_suppression_service import get_suppression
from ..models.models_v2 import SuppressionType
from ..utils import email_sender
from ..core.config import settings

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.ny2026_leads.send_ny2026_tick")
def send_ny2026_tick(max_per_run: int = 1) -> dict:
    """
    Пачечная рассылка по таблице leads для кампании NY2026.

    Идея "почти без остановок":
    - запускаем часто через celery beat (например каждые 5 секунд)
    - берём небольшой батч, чтобы задача почти всегда выполнялась, не простаивая

    Правила:
    - если email уже есть в users → удаляем из leads и НЕ шлём письмо
    - если пользователя нет → резервируем recipient (для бонуса) и шлём письмо
    - бонус выдаётся позже при регистрации/покупке, но ТОЛЬКО если status=sent
    """
    db: Session = SessionLocal()
    try:
        campaign = db.query(EmailCampaign).filter(EmailCampaign.code == "NY2026").first()
        if not campaign:
            return {"status": "no_campaign"}

        # Берём лидов, которым ещё не слали NY2026 (нет записи recipient).
        # SKIP LOCKED позволяет нескольким воркерам не мешать друг другу.
        leads = (
            db.query(Lead)
            .filter(
                ~db.query(EmailCampaignRecipient.id)
                .filter(
                    EmailCampaignRecipient.campaign_id == campaign.id,
                    EmailCampaignRecipient.email == Lead.email,
                )
                .exists()
            )
            .order_by(Lead.id)
            .limit(max_per_run)
            .with_for_update(skip_locked=True)
            .all()
        )

        if not leads:
            return {"status": "empty"}

        sent = 0
        skipped_user_exists = 0
        failed = 0

        # Собираем кандидатов на отправку (после чисток user_exists/suppression)
        to_send_by_lang: dict[str, list[str]] = {}
        lead_ids_by_email: dict[str, int] = {}

        for lead in leads:
            email = (lead.email or "").strip()
            if not email:
                continue

            if skip_send_and_cleanup_if_user_exists(db, email=email):
                skipped_user_exists += 1
                continue

            # Если email уже в suppression (invalid/hard_bounce/complaint/unsubscribe)
            # — удаляем из leads и больше не пытаемся слать.
            sup = get_suppression(db, email)
            if sup and sup.type in {SuppressionType.INVALID, SuppressionType.HARD_BOUNCE, SuppressionType.COMPLAINT, SuppressionType.UNSUBSCRIBE}:
                db.query(Lead).filter(Lead.id == lead.id).delete(synchronize_session=False)
                db.commit()
                failed += 1
                continue

            lang = (getattr(lead, "language", "EN") or "EN").upper()
            to_send_by_lang.setdefault(lang, []).append(email)
            lead_ids_by_email[email] = lead.id

        if not to_send_by_lang:
            return {"status": "ok", "sent": 0, "skipped_user_exists": skipped_user_exists, "failed": failed}

        # 1) Reserve recipients для всех выбранных email (одним коммитом, поштучно с дедупом)
        reserved: list[str] = []
        for lang, emails in to_send_by_lang.items():
            for email in emails:
                rec = EmailCampaignRecipient(
                    campaign_id=campaign.id,
                    email=email,
                    language=lang,
                    status=EmailCampaignRecipientStatus.UNKNOWN,
                    sent_at=None,
                )
                db.add(rec)
                try:
                    db.flush()
                    reserved.append(email)
                except IntegrityError:
                    db.rollback()
                    # duplicate reserve → пропускаем
                    continue
        db.commit()

        # 2) Bulk-send по языкам (валидация каждого email внутри send_html_email_bulk)
        now = datetime.utcnow()
        for lang, emails in to_send_by_lang.items():
            if not emails:
                continue

            # ── Provider-aware throttling ───────────────────────────────────────
            # Yahoo режет сильнее всего, Gmail тоже чувствительный к всплескам.
            # Поэтому дробим отправку по провайдерам с разными chunk_size.
            yahoo_domains = {
                "yahoo.com", "yahoo.co.uk", "yahoo.fr", "yahoo.de", "yahoo.es", "yahoo.it",
                "ymail.com", "rocketmail.com",
                "yahooinc.com",
            }
            gmail_domains = {"gmail.com", "googlemail.com"}

            def _domain(email: str) -> str:
                em = (email or "").strip().lower()
                return em.split("@", 1)[1] if "@" in em else ""

            yahoo_emails: list[str] = []
            gmail_emails: list[str] = []
            other_emails: list[str] = []

            for e in emails:
                d = _domain(e)
                if d in yahoo_domains:
                    yahoo_emails.append(e)
                elif d in gmail_domains:
                    gmail_emails.append(e)
                else:
                    other_emails.append(e)

            chunk_default = int(getattr(settings, "NY2026_BULK_CHUNK_DEFAULT", 400) or 400)
            chunk_gmail = int(getattr(settings, "NY2026_BULK_CHUNK_GMAIL", 150) or 150)
            chunk_yahoo = int(getattr(settings, "NY2026_BULK_CHUNK_YAHOO", 80) or 80)
            pause_s = float(getattr(settings, "NY2026_BULK_PAUSE_SECONDS", 1.0) or 0.0)

            def _send_and_mark(batch: list[str], *, chunk_size: int) -> tuple[int, int]:
                """Returns (sent_count_increment, not_sent_count_increment)."""
                if not batch:
                    return 0, 0
                try:
                    res = email_sender.send_new_year_campaign_email_bulk(
                        batch,
                        region=lang,
                        chunk_size=max(1, min(1000, int(chunk_size))),
                        pause_seconds_between_chunks=max(0.0, float(pause_s)),
                    )
                except Exception as e:
                    logger.warning("NY2026 bulk send failed (lang=%s): %s", lang, e)
                    res = {"ok": False, "sent": 0, "accepted_emails": []}

                accepted_emails = [x.strip().lower() for x in (res.get("accepted_emails") or [])]
                all_emails = [x.strip().lower() for x in batch]

                if res.get("ok") and accepted_emails:
                    db.query(EmailCampaignRecipient).filter(
                        EmailCampaignRecipient.campaign_id == campaign.id,
                        EmailCampaignRecipient.language == lang,
                        EmailCampaignRecipient.email.in_(accepted_emails),
                    ).update(
                        {"status": EmailCampaignRecipientStatus.SENT, "sent_at": now},
                        synchronize_session=False,
                    )

                    not_sent = [e for e in all_emails if e not in set(accepted_emails)]
                    if not_sent:
                        db.query(EmailCampaignRecipient).filter(
                            EmailCampaignRecipient.campaign_id == campaign.id,
                            EmailCampaignRecipient.language == lang,
                            EmailCampaignRecipient.status == EmailCampaignRecipientStatus.UNKNOWN,
                            EmailCampaignRecipient.email.in_(not_sent),
                        ).delete(synchronize_session=False)
                    db.commit()
                    return int(res.get("sent", 0)), max(0, len(all_emails) - len(accepted_emails))

                # Вообще не отправилось — удаляем UNKNOWN recipients, чтобы был повтор позже
                db.query(EmailCampaignRecipient).filter(
                    EmailCampaignRecipient.campaign_id == campaign.id,
                    EmailCampaignRecipient.language == lang,
                    EmailCampaignRecipient.status == EmailCampaignRecipientStatus.UNKNOWN,
                    EmailCampaignRecipient.email.in_(all_emails),
                ).delete(synchronize_session=False)
                db.commit()
                return 0, len(all_emails)

            # Отправляем сначала Yahoo (самый строгий), потом Gmail, потом остальных
            s1, f1 = _send_and_mark(yahoo_emails, chunk_size=chunk_yahoo)
            s2, f2 = _send_and_mark(gmail_emails, chunk_size=chunk_gmail)
            s3, f3 = _send_and_mark(other_emails, chunk_size=chunk_default)
            sent += (s1 + s2 + s3)
            failed += (f1 + f2 + f3)

        return {"status": "ok", "sent": sent, "skipped_user_exists": skipped_user_exists, "failed": failed}
    finally:
        db.close()


@shared_task(name="app.tasks.ny2026_leads.send_ny2026_to_email")
def send_ny2026_to_email(target_email: str, region: str = "EN") -> dict:
    """
    Ручной e2e-тест/ручной прогон: отправить NY2026 на КОНКРЕТНЫЙ email.

    Делает:
    - проверка users.email → если есть пользователь: удаляет lead (если есть) и пропускает отправку
    - иначе: гарантирует, что lead существует (для теста удаления из leads при регистрации/покупке)
    - создаёт EmailCampaignRecipient (reserve)
    - шлёт письмо и ставит status=sent/sent_at
    """
    db: Session = SessionLocal()
    try:
        email = normalize_email(target_email)
        if not email:
            return {"status": "bad_email"}

        campaign = db.query(EmailCampaign).filter(EmailCampaign.code == "NY2026").first()
        if not campaign:
            return {"status": "no_campaign"}

        # если пользователь уже зарегистрирован — чистим lead и выходим
        if skip_send_and_cleanup_if_user_exists(db, email=email):
            return {"status": "skipped_user_exists"}

        # гарантируем наличие lead (чтобы потом проверить удаление leads при регистрации/покупке)
        lead = db.query(Lead).filter(Lead.email == email).first()
        if not lead:
            lead = Lead(email=email, language=region.upper(), tags=["manual_test"], source="manual_test")
            db.add(lead)
            db.commit()
            db.refresh(lead)

        # reserve recipient (уникальность по (campaign_id, email))
        rec = EmailCampaignRecipient(
            campaign_id=campaign.id,
            email=email,
            language=(region or getattr(lead, "language", "EN") or "EN").upper(),
            status=EmailCampaignRecipientStatus.UNKNOWN,
            sent_at=None,
        )
        db.add(rec)
        try:
            db.commit()
            db.refresh(rec)
        except IntegrityError:
            db.rollback()
            # если запись уже есть — отправку не повторяем автоматически
            existing = (
                db.query(EmailCampaignRecipient)
                .filter(EmailCampaignRecipient.campaign_id == campaign.id, EmailCampaignRecipient.email == email)
                .first()
            )
            return {"status": "already_exists", "recipient_status": getattr(existing, "status", None)}

        ok = False
        try:
            ok = bool(email_sender.send_new_year_campaign_email(recipient_email=email, region=rec.language))
        except Exception as e:
            logger.warning("NY2026 manual send failed for %s: %s", email, e)
            ok = False

        now = datetime.utcnow()
        if ok:
            db.query(EmailCampaignRecipient).filter(EmailCampaignRecipient.id == rec.id).update(
                {"status": EmailCampaignRecipientStatus.SENT, "sent_at": now},
                synchronize_session=False,
            )
            db.commit()
            return {"status": "sent", "email": email, "recipient_id": rec.id}

        # не оставляем запись, чтобы не было ложного бонуса/счётчика
        db.query(EmailCampaignRecipient).filter(EmailCampaignRecipient.id == rec.id).delete(synchronize_session=False)
        db.commit()
        return {"status": "send_failed"}
    finally:
        db.close()


