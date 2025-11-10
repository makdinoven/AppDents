from typing import List, Dict, Any

from sqlalchemy import func, or_, Integer, cast
from sqlalchemy.orm import Session, selectinload

from ..core.config import settings
from ..models import models_v2 as m
from ..models.models_v2 import User, WalletTransaction, WalletTxTypes, Purchase, ReferralRule
from ..schemas_v2.wallet import ReferralReportItem
from ..services_v2.user_service import generate_unique_referral_code


# -------------------- helpers --------------------

def get_referral_link(db: Session, user: m.User) -> str:
    """Генерирует ссылку https://<APP_URL>/register?ref=<code>."""

    if not user.referral_code:
        user.referral_code = generate_unique_referral_code(db)
        db.commit()
        db.refresh(user)

    return f"{user.referral_code}"


def get_wallet_balance(user: m.User) -> float:
    return user.balance


def get_wallet_transactions(db: Session, user_id: int) -> List[m.WalletTransaction]:
    return (
        db.query(m.WalletTransaction)
        .filter(m.WalletTransaction.user_id == user_id)
        .order_by(m.WalletTransaction.created_at.desc())
        .all()
    )

def admin_adjust_balance(
    db: Session,
    user_id: int,
    amount: float,
    meta: dict | None = None
) -> None:
    """
    Админская корректировка баланса:
    положительный amount — зачисление, отрицательный — списание.
    """
    user = db.query(User).get(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")

    # если списываем, проверяем достаточность средств
    if amount < 0 and user.balance < -amount - 1e-6:
        raise ValueError("Not enough balance to deduct")

    user.balance += amount
    tx = WalletTransaction(
        user_id=user_id,
        amount=amount,
        type=WalletTxTypes.ADMIN_ADJUST,
        meta=meta or {}
    )
    db.add(tx)
    db.commit()

def get_referral_report(db, inviter_id: int) -> List[ReferralReportItem]:
    """
    Возвращает список приглашённых + суммы.
    Работает и в MySQL, и в PostgreSQL.
    """
    invited = db.query(m.User).filter(m.User.invited_by_id == inviter_id).all()
    report = []

    for u in invited:
        # 1) сколько потратил приглашённый
        total_paid = (
            db.query(func.coalesce(func.sum(m.Purchase.amount), 0.0))
              .filter(m.Purchase.user_id == u.id)
              .scalar() or 0.0
        )

        # 2) сколько кэшбэка получили с этого приглашённого
        # --- MySQL-совместимый фильтр JSON ---
        from_user_filter = cast(
            func.JSON_UNQUOTE(
                func.JSON_EXTRACT(m.WalletTransaction.meta, '$.from_user')
            ),
            Integer
        ) == u.id

        total_cashback = (
            db.query(func.coalesce(func.sum(m.WalletTransaction.amount), 0.0))
              .filter(
                  m.WalletTransaction.user_id == inviter_id,
                  m.WalletTransaction.type == m.WalletTxTypes.REFERRAL_CASHBACK,
                  from_user_filter
              )
              .scalar() or 0.0
        )

        report.append(
            ReferralReportItem(
                email=u.email,
                total_cashback=total_cashback
            )
        )

    return report

def debit_balance(
    db: Session,
    user_id: int,
    amount: float,
    meta: dict | None = None
) -> None:
    """
    Списывает amount (USD) с баланса – исключение, если денег не хватает.
    """
    user = db.query(User).get(user_id)
    if user.balance < amount - 1e-6:      # небольшой допуск на float
        raise ValueError("Not enough balance")
    user.balance -= amount
    db.add(
        WalletTransaction(
            user_id=user_id,
            amount=-amount,
            type=WalletTxTypes.INTERNAL_PURCHASE,
            meta=meta or {}
        )
    )
    db.commit()

def get_cashback_percent(db: Session, invitee_id: int) -> float:
    """
    Находит порядковый номер покупки invitee_id (1,2,…),
    ищет в referral_rules подходящий диапазон и возвращает percent.
    """
    purchase_count = (
        db.query(func.count(Purchase.id))
          .filter(Purchase.user_id == invitee_id)
          .scalar()
        or 0
    )
    rule = (
        db.query(ReferralRule)
          .filter(
              ReferralRule.min_purchase_no <= purchase_count,
              or_(
                  ReferralRule.max_purchase_no == None,
                  ReferralRule.max_purchase_no >= purchase_count
              )
          )
          .order_by(ReferralRule.min_purchase_no.desc())
          .first()
    )
    return rule.percent if rule else 0.0


def get_wallet_feed(db: Session, user_id: int) -> List[Dict[str, Any]]:
    def _serialize_book(book_obj) -> dict[str, Any] | None:
        if not book_obj:
            return None
        return {
            "id": getattr(book_obj, "id", None),
            "title": getattr(book_obj, "title", None),
            "slug": getattr(book_obj, "slug", None),
            "cover_url": getattr(book_obj, "cover_url", None),
        }

    # --- 1. кошелёк ---
    tx_rows = (
        db.query(m.WalletTransaction)
          .filter(m.WalletTransaction.user_id == user_id)
          .all()
    )
    tx_items = [
        {
            "id": tx.id,
            "amount": tx.amount,
            "type": tx.type.value,
            "meta": tx.meta,
            "created_at": tx.created_at,
            "slug": None,
            "landing_name": None,
            "email": None,
            "book_landing_id": None,
            "book_landing_slug": None,
            "book_landing_name": None,
            "books": [],
        }
        for tx in tx_rows
    ]

    # --- 2. классические покупки ---
    purchase_rows = (
        db.query(m.Purchase)
          .options(
              selectinload(m.Purchase.landing),
              selectinload(m.Purchase.book),
              selectinload(m.Purchase.book_landing).selectinload(m.BookLanding.books),
          )
          .filter(m.Purchase.user_id == user_id)
          .all()
    )
    purchase_items: list[Dict[str, Any]] = []
    for p in purchase_rows:
        book_landing = getattr(p, "book_landing", None)
        book_entries = []
        if getattr(p, "book", None):
            serialized = _serialize_book(p.book)
            if serialized and serialized["id"] is not None:
                book_entries.append(serialized)
        if book_landing and getattr(book_landing, "books", None):
            for book in book_landing.books or []:
                serialized = _serialize_book(book)
                if serialized and serialized["id"] is not None:
                    book_entries.append(serialized)
        # удаляем дубликаты, сохраняя порядок
        dedup_books: dict[int, Dict[str, Any]] = {}
        for entry in book_entries:
            dedup_books[entry["id"]] = entry

        purchase_items.append(
            {
                "id": p.id,
                "amount": -abs(p.amount),
                "type": "PURCHASE",
                "meta": {"source": p.source.value},
                "created_at": p.created_at,
                "slug": p.landing.page_name if p.landing else None,
                "landing_name": p.landing.landing_name if p.landing else None,
                "email": None,
                "book_landing_id": book_landing.id if book_landing else None,
                "book_landing_slug": book_landing.page_name if book_landing else None,
                "book_landing_name": book_landing.landing_name if book_landing else None,
                "books": list(dedup_books.values()),
            }
        )

    # --- 3. склейка ---
    items = tx_items + purchase_items

    # ----------------------------------------------------------------------
    # 4. СБОР ID, которые лежат в meta
    # ----------------------------------------------------------------------
    user_ids   = {i["meta"].get("from_user")    for i in items if isinstance(i["meta"], dict) and i["meta"].get("from_user")}
    purch_ids  = {i["meta"].get("purchase_id")  for i in items if isinstance(i["meta"], dict) and i["meta"].get("purchase_id")}
    course_ids = set()
    book_ids: set[int] = set()
    book_landing_ids: set[int] = set()
    for i in items:
        meta = i["meta"]
        if isinstance(meta, dict) and meta.get("courses"):
            first = meta["courses"][0]
            course_ids.add(first)
        if isinstance(meta, dict):
            meta_books = meta.get("books")
            if isinstance(meta_books, (list, tuple)):
                for bid in meta_books:
                    try:
                        bid_int = int(bid)
                    except (TypeError, ValueError):
                        continue
                    book_ids.add(bid_int)
            blid = meta.get("book_landing_id")
            if blid is not None:
                try:
                    book_landing_ids.add(int(blid))
                except (TypeError, ValueError):
                    pass
        if i.get("book_landing_id"):
            book_landing_ids.add(i["book_landing_id"])
        if i.get("books"):
            for book in i["books"]:
                bid = book.get("id")
                if bid is not None:
                    book_ids.add(bid)

    # ----------------------------------------------------------------------
    # 5. ПОДТЯГИВАЕМ ДАННЫЕ одним запросом на каждый тип
    # ----------------------------------------------------------------------
    email_map = {}
    if user_ids:
        email_map = dict(db.query(m.User.id, m.User.email)
                           .filter(m.User.id.in_(user_ids)))

    purch_land_map = {}
    if purch_ids:
        purch_land_map = dict(
            db.query(m.Purchase.id, m.Landing.landing_name)
              .join(m.Landing, m.Purchase.landing_id == m.Landing.id, isouter=True)
              .filter(m.Purchase.id.in_(purch_ids))
        )

    course_land_map = {}
    if course_ids:
                course_land_map = dict(
                        db.query(m.Landing.id, m.Landing.landing_name)
            .filter(m.Landing.id.in_(course_ids))
                                           )

    book_map: dict[int, Dict[str, Any]] = {}
    if book_ids:
        book_rows = (
            db.query(m.Book.id, m.Book.title, m.Book.slug, m.Book.cover_url)
              .filter(m.Book.id.in_(book_ids))
              .all()
        )
        for bid, title, slug, cover in book_rows:
            book_map[int(bid)] = {
                "id": int(bid),
                "title": title,
                "slug": slug,
                "cover_url": cover,
            }

    book_landing_map: dict[int, Dict[str, Any]] = {}
    if book_landing_ids:
        book_landing_rows = (
            db.query(m.BookLanding)
              .options(selectinload(m.BookLanding.books))
              .filter(m.BookLanding.id.in_(book_landing_ids))
              .all()
        )
        for bl in book_landing_rows:
            serialized_books: dict[int, Dict[str, Any]] = {}
            for bk in getattr(bl, "books", []) or []:
                serialized = _serialize_book(bk)
                if serialized and serialized["id"] is not None:
                    serialized_books[serialized["id"]] = serialized
            book_landing_map[bl.id] = {
                "id": bl.id,
                "slug": bl.page_name,
                "name": bl.landing_name,
                "books": list(serialized_books.values()),
            }

    # ----------------------------------------------------------------------
    # 6. ГИДРАТАЦИЯ элементов
    # ----------------------------------------------------------------------
    for itm in items:
        meta = itm["meta"] if isinstance(itm["meta"], dict) else {}

        # email
        uid = meta.get("from_user")
        if uid and uid in email_map:
            itm["email"] = email_map[uid]

        # landing_name (приоритет: purchase_id → courses[0] → уже заполнено)
        if not itm["landing_name"]:
            pid = meta.get("purchase_id")
            if pid and pid in purch_land_map:
                itm["landing_name"] = purch_land_map[pid]
            elif meta.get("courses"):
                cid = meta["courses"][0]
                itm["landing_name"] = course_land_map.get(cid)

        # book landing details и книги
        existing_books: dict[int, Dict[str, Any]] = {
            b["id"]: b for b in (itm.get("books") or []) if isinstance(b, dict) and b.get("id") is not None
        }

        meta_books = meta.get("books", []) if isinstance(meta, dict) else []
        if isinstance(meta_books, (list, tuple)):
            for bid in meta_books:
                try:
                    bid_int = int(bid)
                except (TypeError, ValueError):
                    continue
                data = book_map.get(bid_int)
                if data:
                    existing_books[bid_int] = data

        book_landing_id = itm.get("book_landing_id") or meta.get("book_landing_id")
        if book_landing_id is not None:
            try:
                book_landing_id = int(book_landing_id)
            except (TypeError, ValueError):
                book_landing_id = None
        if book_landing_id and book_landing_id in book_landing_map:
            bl_info = book_landing_map[book_landing_id]
            itm["book_landing_id"] = book_landing_id
            itm["book_landing_slug"] = bl_info.get("slug")
            if not itm.get("book_landing_name"):
                itm["book_landing_name"] = bl_info.get("name")
            for bk in bl_info.get("books", []):
                if bk and bk.get("id") is not None:
                    existing_books[bk["id"]] = bk

        itm["books"] = list(existing_books.values())

    # итоги, отсортированные по дате ↓
    return sorted(items, key=lambda x: x["created_at"], reverse=True)