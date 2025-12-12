from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Table, Enum, Boolean, DateTime, func, Float, \
    Index, BigInteger, Numeric, Date
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

book_landing_tags = Table(
    "book_landing_tags",
    Base.metadata,
    Column("book_landing_id", Integer, ForeignKey("book_landings.id"), primary_key=True),
    Column("tag_id",          Integer, ForeignKey("tags.id"),          primary_key=True),
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
    BOOKS_PAGE = "BOOKS_PAGE"
    BOOKS_OFFER = "BOOKS_OFFER"
    BOOKS_LANDING = "BOOKS_LANDING"
    BOOKS_LANDING_OFFER = "BOOKS_LANDING_OFFER"
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
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),  # MySQL CURRENT_TIMESTAMP
    )

    __table_args__ = (
        # если у тебя уже есть другие индексы — добавь этот в кортеж
        Index("ix_landings_created_at", "created_at"),
        Index("ix_landings_page_name", "page_name"),
    )


    # Связь с лекторами через ассоциативную таблицу
    authors = relationship("Author", secondary=landing_authors, back_populates="landings")
    # Связь с курсами через новую ассоциативную таблицу
    courses = relationship("Course", secondary=landing_course)
    tags = relationship("Tag", secondary=landing_tags, back_populates="landings")

    @hybrid_property
    def course_ids(self) -> list[int]:
        """Список ID курсов, связанных с этим лендингом."""
        return [c.id for c in self.courses]

class LandingAdPeriod(Base):
    __tablename__ = "landing_ad_periods"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    landing_id = Column(Integer, ForeignKey("landings.id"), nullable=False, index=True)

    started_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    ended_at   = Column(DateTime, nullable=True)  # NULL = ещё в рекламе

    # опционально, если хочешь хранить «кто» переключил
    started_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    ended_by   = Column(Integer, ForeignKey("users.id"), nullable=True)

    landing = relationship("Landing", backref="ad_periods")

    __table_args__ = (
        Index("ix_ladp_landing_started", "landing_id", "started_at"),
        Index("ix_ladp_landing_ended",   "landing_id", "ended_at"),
    )

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    landings = relationship("Landing", secondary=landing_tags, back_populates="tags")
    book_landings = relationship("BookLanding", secondary=book_landing_tags, back_populates="tags", lazy="selectin")


class Author(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    photo = Column(String(255))
    language = Column(Enum('EN', 'RU', 'ES', 'PT', 'AR', 'IT', name='author_language'), nullable=False, server_default='EN')

    # Лендинги, к которым привязан автор
    landings = relationship("Landing", secondary=landing_authors, back_populates="authors")
    books = relationship("Book", secondary="book_authors", back_populates="authors")

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


class Invitation(Base):
    __tablename__ = 'invitations'
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    language = Column(String(10), default='EN')
    created_at = Column(DateTime, server_default=func.utc(), nullable=False)
    
    sender = relationship("User", foreign_keys=[sender_id])


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

    # ⬇⬇⬇ новое для напоминаний по большой корзине
    bigcart_send_count = Column(Integer, nullable=False, server_default="0")
    bigcart_last_sent_at = Column(DateTime, nullable=True)

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
    send_count = Column(Integer, nullable=False,server_default="0")
    last_sent_at = Column(DateTime, nullable=True)
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

book_publishers = Table(
    "book_publishers",
    Base.metadata,
    Column("book_id",      Integer, ForeignKey("books.id"),      primary_key=True),
    Column("publisher_id", Integer, ForeignKey("publishers.id"), primary_key=True),
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
    publication_date = Column(String(12), nullable=True, comment="Дата публикации книги")
    page_count = Column(Integer, nullable=True, comment="Количество страниц в книге")
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
    landings = relationship("BookLanding", secondary=book_landing_books, back_populates="books", lazy="selectin")
    tags = relationship(
        "Tag",
        secondary=book_tags,
        back_populates="books",
        lazy="selectin",
    )
    publishers = relationship(
        "Publisher",
        secondary=book_publishers,
        back_populates="books",
        lazy="selectin",
    )


class CreativeStatus(str, PyEnum):
    PENDING    = "pending"
    PROCESSING = "processing"
    READY      = "ready"
    FAILED     = "failed"


class BookCreative(Base):
    __tablename__ = "book_creatives"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    book_id       = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    language      = Column(Enum('EN', 'RU', 'ES', 'PT', 'AR', 'IT', name='book_language'), nullable=False)
    creative_code = Column(String(32), nullable=False, index=True)  # kbhccvksoprg7 | ktawlyumyeaw7 | uoshaoahss0al

    status        = Column(Enum(CreativeStatus, name="creative_status"), nullable=False, server_default=CreativeStatus.PENDING.value)
    placid_job_id = Column(String(128))
    placid_image_url = Column(String(700))
    s3_key        = Column(String(700))
    s3_url        = Column(String(700))
    payload_used  = Column(JSON)
    error_message = Column(Text)

    created_at    = Column(DateTime, server_default=func.utc_timestamp(), nullable=False)
    updated_at    = Column(DateTime, server_default=func.utc_timestamp(), onupdate=func.utc_timestamp(), nullable=False)

    book = relationship("Book")


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

# ───────────────── Publisher ─────────────────
class Publisher(Base):
    """
    Издательство книг.
    Many-to-many с книгами (одна книга может быть от нескольких издательств,
    например, co-publishing или разные издания).
    """
    __tablename__ = "publishers"

    id   = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.utc_timestamp(), nullable=False)

    books = relationship(
        "Book",
        secondary=book_publishers,
        back_populates="publishers",
        lazy="selectin",
    )


# ───────────────── BookLandingImage ─────────────────
class BookLandingImage(Base):
    __tablename__ = "book_landing_images"

    id           = Column(Integer, primary_key=True)
    landing_id   = Column(Integer, ForeignKey("book_landings.id"), nullable=False, index=True)
    s3_url       = Column(String(700), nullable=False)
    alt          = Column(String(255))
    caption      = Column(String(255))
    sort_index   = Column(Integer, nullable=False, server_default="0")
    size_bytes   = Column(BigInteger)
    content_type = Column(String(100))
    created_at   = Column(DateTime, server_default=func.utc_timestamp(), nullable=False)

    # при желании: relationship на BookLanding (не обязательно)
    # landing = relationship("BookLanding", backref="gallery_images")


class BookLanding(Base):
    """
    Отдельная посадочная страница книги (как Landing для курса).

    page_name — URL-slug: `/books/<page_name>`.
    """
    __tablename__ = "book_landings"

    id            = Column(Integer, primary_key=True)
    language      = Column(Enum('EN', 'RU', 'ES', 'PT', 'AR', 'IT',
                                name='landing_language'), nullable=False,
                            server_default='EN')
    page_name     = Column(String(255), unique=True, nullable=False)
    landing_name  = Column(String(255))
    old_price = Column(Numeric(10, 2))
    new_price = Column(Numeric(10, 2))
    description   = Column(Text)
    sales_count   = Column(Integer, default=0)
    is_hidden     = Column(Boolean, nullable=False, server_default='0')
    in_advertising = Column(Boolean, default=False)
    ad_flag_expires_at = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, server_default=func.utc_timestamp())
    updated_at    = Column(DateTime, server_default=func.utc_timestamp(),
                           onupdate=func.utc_timestamp())

    books = relationship("Book", secondary=book_landing_books,
                         back_populates="landings", lazy="selectin")
    tags = relationship("Tag", secondary=book_landing_tags,
                        back_populates="book_landings", lazy="selectin")

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


# ── Модели для аналитики рекламы ─────────────────────────────────────────────

class LandingVisit(Base):
    __tablename__ = "landing_visits"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    landing_id = Column(Integer, ForeignKey("landings.id"), nullable=False, index=True)
    visited_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    from_ad = Column(Boolean, nullable=False, server_default="0")

    landing = relationship("Landing", backref="visits")

    __table_args__ = (
        Index("ix_lvisit_landing_dt", "landing_id", "visited_at"),
    )
class AdStaff(Base):
    __tablename__ = "ad_staff"
    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

class AdAccount(Base):
    __tablename__ = "ad_accounts"
    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

class LandingAdAssignment(Base):
    __tablename__ = "landing_ad_assignments"
    landing_id = Column(Integer, ForeignKey("landings.id"), primary_key=True)
    staff_id   = Column(Integer, ForeignKey("ad_staff.id"), nullable=True)
    account_id = Column(Integer, ForeignKey("ad_accounts.id"), nullable=True)

    landing = relationship("Landing", backref=backref("ad_assignment", uselist=False))
    staff   = relationship("AdStaff")
    account = relationship("AdAccount")

class BookLandingVisit(Base):
    """Все визиты на книжные лендинги."""
    __tablename__ = "book_landing_visits"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    book_landing_id = Column(Integer, ForeignKey("book_landings.id"), nullable=False, index=True)
    visited_at      = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    from_ad         = Column(Boolean, nullable=False, server_default="0")

    book_landing = relationship("BookLanding", backref="visits")

    __table_args__ = (
        Index("ix_book_landing_visits_landing_visited", "book_landing_id", "visited_at"),
    )


class BookLandingAdPeriod(Base):
    """Периоды нахождения книжного лендинга в рекламе."""
    __tablename__ = "book_landing_ad_periods"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    book_landing_id = Column(Integer, ForeignKey("book_landings.id"), nullable=False, index=True)

    started_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    ended_at   = Column(DateTime, nullable=True)  # NULL = ещё в рекламе

    # опционально, если хочешь хранить «кто» переключил
    started_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    ended_by   = Column(Integer, ForeignKey("users.id"), nullable=True)

    book_landing = relationship("BookLanding", backref="ad_periods")

    __table_args__ = (
        Index("ix_bladp_landing_started", "book_landing_id", "started_at"),
        Index("ix_bladp_landing_ended",   "book_landing_id", "ended_at"),
    )

class BookAdVisit(Base):
    """Визиты с рекламы на книжные лендинги с метаданными (fbp, fbc, ip)."""
    __tablename__ = "book_ad_visits"

    id              = Column(Integer, primary_key=True)
    book_landing_id = Column(Integer, ForeignKey("book_landings.id"), nullable=False)
    visited_at      = Column(DateTime, server_default=func.utc(), nullable=False)
    fbp             = Column(String(255))
    fbc             = Column(String(255))
    ip_address      = Column(String(45))

    book_landing = relationship("BookLanding", backref="ad_visits")


class BookLandingAdAssignment(Base):
    """Назначение ответственного и кабинета для книжного лендинга."""
    __tablename__ = "book_landing_ad_assignments"
    book_landing_id = Column(Integer, ForeignKey("book_landings.id"), primary_key=True)
    staff_id        = Column(Integer, ForeignKey("ad_staff.id"), nullable=True)
    account_id      = Column(Integer, ForeignKey("ad_accounts.id"), nullable=True)

    book_landing = relationship("BookLanding", backref=backref("ad_assignment", uselist=False))
    staff        = relationship("AdStaff")
    account      = relationship("AdAccount")


class TermsOfUse(Base):
    """Условия использования."""
    __tablename__ = "terms_of_use"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    language   = Column(String(10), nullable=False, unique=True)
    title      = Column(String(255), nullable=False)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)


class PrivacyPolicy(Base):
    """Политика конфиденциальности."""
    __tablename__ = "privacy_policy"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    language   = Column(String(10), nullable=False, unique=True)
    title      = Column(String(255), nullable=False)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)


class CookiePolicy(Base):
    """Политика использования файлов cookie."""
    __tablename__ = "cookie_policy"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    language   = Column(String(10), nullable=False, unique=True)
    title      = Column(String(255), nullable=False)
    content    = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

class ReferralCampaignEmail(Base):
    """
    Логи рассылки писем по реферальной кампании.
    Одному юзеру шлём максимум одно такое письмо.
    """
    __tablename__ = "referral_campaign_emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",  # pending | sent | error
    )
    error_message = Column(Text)

    sent_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.utc(),  # как у тебя в других моделях
    )

    user = relationship("User", backref="referral_campaign_emails")


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(BigInteger, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    path = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", backref="search_queries")


# ───────────────── Система опросов (Surveys) ─────────────────

class SurveyStatus(str, PyEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class QuestionType(str, PyEnum):
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    FREE_TEXT = "FREE_TEXT"


class Survey(Base):
    """Опрос пользователей."""
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title_key = Column(String(100), nullable=False)       # i18n ключ
    description_key = Column(String(100), nullable=True)  # i18n ключ
    status = Column(
        Enum(SurveyStatus, name="survey_status"),
        nullable=False,
        server_default=SurveyStatus.DRAFT.value
    )
    created_at = Column(DateTime, server_default=func.utc_timestamp(), nullable=False)
    closed_at = Column(DateTime, nullable=True)

    questions = relationship(
        "SurveyQuestion",
        back_populates="survey",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="SurveyQuestion.order_index"
    )


class SurveyQuestion(Base):
    """Вопрос в опросе."""
    __tablename__ = "survey_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    question_type = Column(
        Enum(QuestionType, name="question_type"),
        nullable=False
    )
    text_key = Column(String(100), nullable=False)      # i18n ключ
    options_keys = Column(JSON, nullable=True)          # ["survey.q1.opt1", ...] для choice
    is_required = Column(Boolean, nullable=False, server_default="1")

    survey = relationship("Survey", back_populates="questions")


class SurveyResponse(Base):
    """Ответ пользователя на вопрос опроса."""
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("survey_questions.id"), nullable=False)
    answer_choice = Column(JSON, nullable=True)   # [0, 2] - индексы выбранных вариантов
    answer_text = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.utc_timestamp(), nullable=False)

    __table_args__ = (
        Index("ix_survey_response_user_survey", "user_id", "survey_id"),
    )


class SurveyView(Base):
    """Открытие модалки опроса пользователем (для аналитики конверсии)."""
    __tablename__ = "survey_views"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    viewed_at = Column(DateTime, server_default=func.utc_timestamp(), nullable=False)

    __table_args__ = (
        Index("ix_survey_view_user_survey", "user_id", "survey_id"),
    )
