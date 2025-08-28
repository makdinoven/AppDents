from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Table, Enum, Boolean, DateTime, func, Float, \
    Index, BigInteger, Numeric
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base, relationship, backref
from enum import Enum as PyEnum
import datetime as _dt

Base = declarative_base()

landing_authors = Table(
    'landing_authors',
    Base.metadata,
    Column('landing_id', Integer, ForeignKey('landings.id'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id'), primary_key=True)
)

# Ассоциативная таблица для связи пользователей и курсов (многие ко многим)
users_courses = Table(
    'users_courses',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)


users_books = Table(
    'users_books',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True),
)


# ассоциативная таблица для связи лендингов и курсов (многие ко многим)
landing_course = Table(
    'landing_course',
    Base.metadata,
    Column('landing_id', Integer, ForeignKey('landings.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)

landing_tags = Table(
    'landing_tags',
    Base.metadata,
    Column('landing_id', Integer, ForeignKey('landings.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

# Ассоциация «книга-тег»
book_tags = Table(
    "book_tags",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id"), primary_key=True),
    Column("tag_id",  Integer, ForeignKey("tags.id"),  primary_key=True),
)

# Ассоциация «книжный лендинг — книги (бандл)»
book_landing_books = Table(
    "book_landing_books",
    Base.metadata,
    Column("book_landing_id", Integer, ForeignKey("book_landings.id"), primary_key=True),
    Column("book_id",         Integer, ForeignKey("books.id"),         primary_key=True),
)


class PurchaseSource(str, PyEnum):
    HOMEPAGE                  = "HOMEPAGE"          # 1
    LANDING                   = "LANDING"           # 2
    PROFESSOR_PAGE            = "PROFESSOR_PAGE"   # 3
    CABINET_OFFER             = "CABINET_OFFER"     # 4
    PROFESSOR_OFFER           = "PROFESSOR_OFFER"   # 5
    PROFESSORS_LIST_OFFER     = "PROF_LIST_OFFER"   # 6
    LANDING_OFFER             = "LANDING_OFFER"     # 7
    CART                      = "CART"              # 8
    COURSES_PAGE              = "COURSES_PAGE"      # 9
    COURSES_PAGE_OFFER        = "COURSES_OFFER"     # 10
    CABINET_FREE = "CABINET_FREE"
    SPECIAL_OFFER = "SPECIAL_OFFER"
    VIDEO_LANDING = "VIDEO_LANDING"
    LANDING_WEBINAR = "LANDING_WEBINAR"
    OTHER                     = "OTHER"

class FreeCourseSource(str, PyEnum):
    """Источник, откуда пользователь получил бесплатный доступ."""
    LANDING        = "landing"         # рекламный лендинг
    SPECIAL_OFFER  = "special_offer"   # спец-предложение
    EMAIL = "email"

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    sections = Column(JSON)

    # Связь с пользователями, купившими курс
    users = relationship("User", secondary=users_courses, back_populates="courses")

class Landing(Base):
    __tablename__ = 'landings'
    id = Column(Integer, primary_key=True)
    language = Column(Enum('EN', 'RU', 'ES', 'PT', 'AR', 'IT', name='landing_language'), nullable=False, server_default='EN')
    page_name = Column(String(255))
    landing_name = Column(Text)
    old_price = Column(String(255))
    new_price = Column(String(255))
    course_program = Column(Text)
    lessons_info = Column(JSON)
    preview_photo = Column(String(255), default='')
    sales_count = Column(Integer, default=0)
    duration = Column(String(50), default='')
    lessons_count = Column(String(50), default='')
    is_hidden = Column(Boolean, nullable=False, server_default='0')
    in_advertising = Column(Boolean, default=False)
    ad_flag_expires_at = Column(DateTime, nullable=True)


    # Связь с лекторами через ассоциативную таблицу
    authors = relationship("Author", secondary=landing_authors, back_populates="landings")
    # Связь с курсами через новую ассоциативную таблицу
    courses = relationship("Course", secondary=landing_course)
    tags = relationship("Tag", secondary=landing_tags, back_populates="landings")

    @hybrid_property
    def course_ids(self) -> list[int]:
        """Список ID курсов, связанных с этим лендингом."""
        return [c.id for c in self.courses]

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    landings = relationship("Landing", secondary=landing_tags, back_populates="tags")

class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    photo = Column(String(255))
    language = Column(Enum('EN', 'RU', 'ES', 'PT', 'AR', 'IT', name='author_language'), nullable=False, server_default='EN')

    # Лендинги, к которым привязан автор
    landings = relationship("Landing", secondary=landing_authors, back_populates="authors")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(255))

    balance = Column(Float, default=0.0, nullable=False)
    referral_code = Column(String(20), unique=True, index=True)
    invited_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.utc(), nullable=False)
    free_trial_used = Column(Boolean, default=False, nullable=False)   # <- NEW


    cart = relationship("Cart", uselist=False, back_populates="user")

    courses = relationship("Course", secondary=users_courses, back_populates="users")
    invited_users = relationship(
        "User",
        backref=backref("inviter", remote_side=[id]),
        foreign_keys="[User.invited_by_id]",
    )
    free_courses = relationship(
        "FreeCourseAccess",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    special_offers = relationship(
        "SpecialOffer",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    books = relationship("Book", secondary=users_books, backref="users")


    @hybrid_property
    def active_special_offer_ids(self) -> list[int]:
        """
        ID курсов из действующих спец-предложений.
        Используется в /me/courses и /detail/{id}.
        """
        now = _dt.datetime.utcnow()
        return [so.course_id for so in self.special_offers if so.expires_at > now]

    @property
    def partial_course_ids(self) -> list[int]:
        """
        ID курсов с бесплатным доступом, которые ещё не были куплены.
        """
        return [
            fca.course_id
            for fca in self.free_courses
            if not fca.converted_to_full
        ]


class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    landing_id = Column(Integer, ForeignKey('landings.id'), nullable=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=True)
    created_at = Column(DateTime, server_default=func.utc(), nullable=False)
    book_landing_id = Column(Integer, ForeignKey('book_landings.id'), nullable=True)
    book_id         = Column(Integer, ForeignKey('books.id'),         nullable=True)
    # Если хотите хранить "покупка была из рекламы или нет"
    from_ad = Column(Boolean, default=False)
    amount = Column(Float, nullable=False, default=0.0)

    source = Column(
        Enum(PurchaseSource, name="purchase_source"),
        nullable=False,
        server_default=PurchaseSource.OTHER.value
    )

    user = relationship("User", backref="purchases")
    landing = relationship("Landing", backref="purchases")
    course = relationship("Course", backref="purchases")
    book_landing = relationship("BookLanding")
    book = relationship("Book")

class WalletTxTypes(str, PyEnum):
    REFERRAL_CASHBACK = "REFERRAL_CASHBACK"
    INTERNAL_PURCHASE = "INTERNAL_PURCHASE"
    ADMIN_ADJUST      = "ADMIN_ADJUST"

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount     = Column(Float, nullable=False)           # +/-
    type       = Column(
        Enum(WalletTxTypes, name="wallet_tx_type"),
        nullable=False
    )
    meta       = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.utc(), nullable=False)

    user = relationship("User", backref="wallet_tx")

class ReferralRule(Base):
    """
    min_purchase_no / max_purchase_no задают диапазон порядкового
    номера покупки приглашённого (1-я, 2-я … ∞).
    Сейчас будет одна строка 1-∞ с percent = 50.
    """
    __tablename__ = "referral_rules"
    id              = Column(Integer, primary_key=True)
    min_purchase_no = Column(Integer, nullable=False)
    max_purchase_no = Column(Integer)           # NULL = ∞
    percent         = Column(Float, nullable=False)

class AdVisit(Base):
    __tablename__ = "ad_visits"
    id          = Column(Integer, primary_key=True)
    landing_id  = Column(Integer, ForeignKey("landings.id"), nullable=False)
    visited_at  = Column(DateTime, server_default=func.utc(), nullable=False)
    fbp         = Column(String(255))
    fbc         = Column(String(255))
    ip_address  = Column(String(45))

    landing = relationship("Landing", backref="ad_visits")

class Cart(Base):
    __tablename__ = "carts"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)
    updated_at   = Column(DateTime, server_default=func.utc_timestamp(),
                          onupdate=func.utc_timestamp(), nullable=False)

    user = relationship("User", back_populates="cart")
    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class CartItemType(str, PyEnum):
    LANDING = "LANDING"
    BOOK    = "BOOK"            # резерв под будущее

class CartItem(Base):
    __tablename__ = "cart_items"

    id         = Column(Integer, primary_key=True)
    cart_id    = Column(Integer, ForeignKey("carts.id"), nullable=False)
    item_type  = Column(Enum(CartItemType, name="cart_item_type"), nullable=False)
    landing_id = Column(Integer, ForeignKey("landings.id"))
    book_landing_id = Column(Integer, ForeignKey("book_landings.id"))                      # для книг позже
    price      = Column(Float, nullable=False)
    added_at   = Column(DateTime, server_default=func.utc_timestamp(), nullable=False)

    cart = relationship("Cart", back_populates="items")
    landing = relationship("Landing")
    book_landing = relationship("BookLanding")

class ProcessedStripeEvent(Base):
    __tablename__ = "processed_stripe_events"

    id           = Column(String, primary_key=True)       # event.id от Stripe
    processed_at = Column(DateTime(timezone=True),
                          server_default=func.now())

class FreeCourseAccess(Base):
    """
    Храним факт, что пользователь получил бесплатный
    доступ к первому уроку курса.
    Если позже курс будет куплен полностью – запись удаляем.
    """
    __tablename__ = "free_course_access"
    __table_args__ = {"extend_existing": True}

    user_id   = Column(Integer, ForeignKey("users.id"), primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)
    granted_at = Column(DateTime,
                        server_default=func.utc_timestamp(),
                        nullable=False)
    converted_to_full = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="TRUE – пользователь купил полный доступ к этому курсу"
    )
    converted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC-время оплаты полного курса"
    )
    source = Column(
        Enum(
            FreeCourseSource,
            name="freecoursesource",  # ⟵ то же имя, что у старого типа!
            validate_strings=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=FreeCourseSource.LANDING.value,
        comment="Источник выдачи partial-курса",
    )
    user   = relationship("User", back_populates="free_courses")
    course = relationship("Course")

class AbandonedCheckout(Base):
    """
    E-mails тех, кто открыл Checkout, но не заплатил.
    Запись удаляется, когда по этому session_id приходит completed.
    """
    __tablename__ = "abandoned_checkouts"

    id         = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    email      = Column(String(255), nullable=False, index=True)
    course_ids = Column(String(255))                 # "12,34,56"
    region     = Column(String(10))
    created_at = Column(DateTime, server_default=func.utc(), nullable=False)
    message_sent = Column(
        Boolean,
        nullable=False,
        server_default="0",
        comment="TRUE – e-mail по лидy уже отправлен"
    )

class PreviewStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED  = "failed"

class LessonPreview(Base):
    __tablename__ = "lesson_previews"

    id           = Column(BigInteger, primary_key=True, autoincrement=True)
    video_link   = Column(Text, nullable=False)
    preview_url  = Column(String(700), nullable=False)

    generated_at = Column(DateTime, nullable=False, server_default=func.utc_timestamp())
    checked_at   = Column(DateTime)

    status = Column(
        Enum(
            PreviewStatus,
            name="previewstatus",
            validate_strings=True,
            values_callable=lambda e: [x.value for x in e],  # нижний регистр
        ),
        nullable=False,
        server_default=PreviewStatus.PENDING.value,
    )
    enqueued_at  = Column(DateTime)
    updated_at   = Column(DateTime, nullable=False,
                          server_default=func.utc_timestamp(),
                          onupdate=func.utc_timestamp())
    attempts     = Column(Integer, nullable=False, server_default="0")
    last_error   = Column(Text)


class SpecialOffer(Base):
    """
    Специальное предложение («­кабинетная акция»).
    • один курс в оффере на пользователя;
    • действует 24 ч (expires_at);
    • после покупки или экспирации запись удаляем Celery-таском.
    """
    __tablename__ = "special_offers"

    user_id    = Column(Integer, ForeignKey("users.id"), primary_key=True)
    course_id  = Column(Integer, ForeignKey("courses.id"), primary_key=True)
    landing_id = Column(Integer, ForeignKey("landings.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.utc_timestamp(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="1",
                       comment="True – оффер ещё действует; False – истёк или куплен")

    user    = relationship("User", back_populates="special_offers")
    course  = relationship("Course")
    landing = relationship("Landing")

class SlideType(str, PyEnum):
    """Тип слайда."""
    COURSE = "COURSE"   # карточка курса (лендинг)
    BOOK   = "BOOK"     # резерв под книги
    FREE   = "FREE"     # произвольный promo-слайд

class Slide(Base):
    """
    Один элемент слайдера для конкретного языка (региона).
    Слайды выводятся в порядке `order_index`.
    """
    __tablename__ = "slides"

    id          = Column(Integer, primary_key=True)
    language    = Column(Enum('EN', 'RU', 'ES', 'PT', 'AR', 'IT',
                              name='landing_language'), nullable=False)
    order_index = Column(Integer, nullable=False, comment="Порядок показа")
    type        = Column(Enum(SlideType, name="slide_type"), nullable=False)

    # Привязка к лендингу курса (актуально для type=COURSE)
    landing_id  = Column(Integer, ForeignKey("landings.id"))
    landing     = relationship("Landing")

    # Поля для type=FREE (promo-слайд)
    bg_media_url = Column(String(700))
    title        = Column(String(255))
    description  = Column(Text)
    target_url   = Column(String(700))

    is_active  = Column(Boolean, nullable=False, server_default="1")
    created_at = Column(DateTime, server_default=func.utc_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.utc_timestamp(),
                        onupdate=func.utc_timestamp(), nullable=False)

    __table_args__ = (
        Index("ix_slide_lang_order", "language", "order_index"),
    )
import logging
logger = logging.getLogger(__name__)

book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id",   Integer, ForeignKey("books.id"),   primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)

class BookFileFormat(str, PyEnum):
    PDF  = "PDF"
    EPUB = "EPUB"
    MOBI = "MOBI"
    AZW3 = "AZW3"
    FB2  = "FB2"

class Book(Base):
    """
    Основная сущность «Книга».

    • Файлы разных форматов — в BookFile.
    • Аудиоверсии (целиком либо по главам) — BookAudio.
    • Отдельные лендинги (разные языки/цены/оферы) — BookLanding.
    """
    __tablename__ = "books"

    id          = Column(Integer, primary_key=True)
    title       = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    cover_url   = Column(String(700))
    language    = Column(Enum('EN', 'RU', 'ES', 'PT', 'AR', 'IT',
                              name='book_language'), nullable=False,
                          server_default='EN')
    created_at  = Column(DateTime, server_default=func.utc_timestamp(),
                         nullable=False)
    updated_at  = Column(DateTime, server_default=func.utc_timestamp(),
                         onupdate=func.utc_timestamp(), nullable=False)

    authors      = relationship("Author",
                                secondary=book_authors,
                                back_populates="books")
    files        = relationship("BookFile",
                                back_populates="book",
                                cascade="all, delete-orphan",
                                lazy="selectin")
    audio_files  = relationship("BookAudio",
                                back_populates="book",
                                cascade="all, delete-orphan",
                                lazy="selectin")
    landings     = relationship("BookLanding",
                                back_populates="book",
                                cascade="all, delete-orphan",
                                lazy="selectin")
    tags = relationship(
        "Tag",
        secondary=book_tags,
        back_populates="books",
        lazy="selectin",
    )


class BookFile(Base):
    """
    Один файл книги в конкретном формате (PDF, EPUB, …).

    size_bytes   — для выводов «вес файла» на фронте.
    """
    __tablename__ = "book_files"

    id          = Column(Integer, primary_key=True)
    book_id     = Column(Integer, ForeignKey("books.id"), nullable=False)
    file_format = Column(Enum(BookFileFormat,
                              name="book_file_format"), nullable=False)
    s3_url      = Column(String(700), nullable=False)
    size_bytes  = Column(Integer)

    book = relationship("Book", back_populates="files")

class BookAudio(Base):
    """
    Аудиоверсия книги.

    Если `chapter_index` = NULL → цельный mp3/ogg.
    Иначе — конкретная глава.
    """
    __tablename__ = "book_audios"

    id            = Column(Integer, primary_key=True)
    book_id       = Column(Integer, ForeignKey("books.id"), nullable=False)
    chapter_index = Column(Integer)
    title         = Column(String(255))
    duration_sec  = Column(Integer)
    s3_url        = Column(String(700), nullable=False)
    book = relationship("Book", back_populates="audio_files")

class BookLanding(Base):
    """
    Отдельная посадочная страница книги (как Landing для курса).

    page_name — URL-slug: `/books/<page_name>`.
    """
    __tablename__ = "book_landings"

    id            = Column(Integer, primary_key=True)
    book_id       = Column(Integer, ForeignKey("books.id"), nullable=False)
    language      = Column(Enum('EN', 'RU', 'ES', 'PT', 'AR', 'IT',
                                name='landing_language'), nullable=False,
                            server_default='EN')
    page_name     = Column(String(255), unique=True, nullable=False)
    landing_name  = Column(String(255))
    old_price = Column(Numeric(10, 2))
    new_price = Column(Numeric(10, 2))
    description   = Column(Text)
    preview_photo = Column(String(700))
    preview_pdf   = Column(String(700),
                           comment="S3-URL PDF-файла с первыми 10-15 стр.")
    preview_imgs  = Column(JSON,
                           comment="['https://…/page1.jpg', '…/page2.jpg', …]")
    sales_count   = Column(Integer, default=0)
    is_hidden     = Column(Boolean, nullable=False, server_default='0')
    created_at    = Column(DateTime, server_default=func.utc_timestamp())
    updated_at    = Column(DateTime, server_default=func.utc_timestamp(),
                           onupdate=func.utc_timestamp())

    book = relationship("Book", back_populates="landings")
    books_bundle = relationship(
        "Book",
        secondary=book_landing_books,
        lazy="selectin",
    )

# ── Динамически вешаем обратную связь на Author ─────────────────────────────
try:
    Author  # noqa: F401  — уже объявлен выше
    if not hasattr(Author, "books"):
        Author.books = relationship(
            "Book",
            secondary=book_authors,
            back_populates="authors",
            lazy="selectin",
        )
except NameError as exc:
    logger.error("Author class not found while binding books: %s", exc)

try:
    Tag  # noqa: F401
    if not hasattr(Tag, "books"):
        Tag.books = relationship(
            "Book",
            secondary=book_tags,
            back_populates="tags",
            lazy="selectin",
        )
except NameError:
    pass
