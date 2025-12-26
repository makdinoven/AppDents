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
            result = {}
            try:
                result = email_sender.send_new_year_campaign_email_bulk(emails, region=lang)
            except Exception as e:
                logger.warning("NY2026 bulk send failed (lang=%s): %s", lang, e)
                result = {"ok": False, "sent": 0}

            if result.get("ok") and result.get("sent", 0) > 0:
                # отмечаем sent для всех recipients этого языка, которые у нас есть в таблице
                db.query(EmailCampaignRecipient).filter(
                    EmailCampaignRecipient.campaign_id == campaign.id,
                    EmailCampaignRecipient.language == lang,
                    EmailCampaignRecipient.email.in_([e.strip().lower() for e in emails]),
                ).update(
                    {"status": EmailCampaignRecipientStatus.SENT, "sent_at": now},
                    synchronize_session=False,
                )
                db.commit()
                sent += int(result.get("sent", 0))
            else:
                # если не отправилось (или sent=0 из-за валидации/suppression) — удаляем UNKNOWN recipients, чтобы был повтор позже
                db.query(EmailCampaignRecipient).filter(
                    EmailCampaignRecipient.campaign_id == campaign.id,
                    EmailCampaignRecipient.language == lang,
                    EmailCampaignRecipient.status == EmailCampaignRecipientStatus.UNKNOWN,
                    EmailCampaignRecipient.email.in_([e.strip().lower() for e in emails]),
                ).delete(synchronize_session=False)
                db.commit()
                failed += len(emails)

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


