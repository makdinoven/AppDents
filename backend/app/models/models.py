import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Enum,
    Numeric,
    Table,
    DateTime,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# -------------------------------------------------------------------
# 1. Пользователи и покупки
# -------------------------------------------------------------------
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, server_default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь "User -> UserCourses"
    courses = relationship("UserCourses", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"


class UserCourses(Base):
    """
    Трекинг покупок: какой пользователь купил какой курс.
    """
    __tablename__ = 'user_courses'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    purchase_date = Column(DateTime(timezone=True), server_default=func.now())
    price_at_purchase = Column(Numeric(10, 2), nullable=False, default=0.00)

    user = relationship("User", back_populates="courses")
    course = relationship("Course", back_populates="users")

    def __repr__(self):
        return f"<UserCourses(id={self.id}, user_id={self.user_id}, course_id={self.course_id})>"


# -------------------------------------------------------------------
# 2. Авторы (для лендингов)
# -------------------------------------------------------------------
class LanguageEnum(str, enum.Enum):
    EN = "en"
    ES = "es"
    RU = "ru"


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    photo = Column(String(255), nullable=True)

    # Связь many-to-many с Landing (автор может фигурировать на разных лендингах)
    landings = relationship(
        "Landing",
        secondary="landing_authors",
        back_populates="authors"
    )

    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}')>"


landing_authors = Table(
    "landing_authors",
    Base.metadata,
    Column("landing_id", Integer, ForeignKey("landing.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)


# -------------------------------------------------------------------
# 3. Курс, секции и модули
# -------------------------------------------------------------------
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)     # Название курса
    description = Column(Text, nullable=True)

    # Связь "Course -> Section" (один курс -> много секций)
    sections = relationship(
        "Section",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    # Связь с UserCourses (покупки)
    users = relationship("UserCourses", back_populates="course")

    # Связь "один курс -> один лендинг"
    landing = relationship("Landing", uselist=False, back_populates="course")

    @property
    def modules(self):
        """Возвращает плоский список модулей всех секций курса."""
        modules = []
        for section in self.sections:
            modules.extend(section.modules)
        return modules

    def __repr__(self):
        return f"<Course(id={self.id}, name='{self.name}')>"


class Section(Base):
    """
    Секция внутри курса.
    Каждый курс может содержать несколько секций,
    и каждая секция принадлежит ровно одному курсу.
    """
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String(255), nullable=False)

    course = relationship("Course", back_populates="sections")

    # Связь "Section -> Module" (один секция -> много модулей)
    modules = relationship(
        "Module",
        back_populates="section",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Section(id={self.id}, name='{self.name}', course_id={self.course_id})>"


class Module(Base):
    """
    Модуль (урок) в секции курса.
    Содержит:
      - title: название модуля
      - short_video_link: короткий видеофрагмент (для лендинга)
      - full_video_link: полное видео (доступно после покупки)
      - program_text: программа модуля (текстовое описание/список пунктов)
      - duration: длительность (например, "2h 15m")
    """
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    title = Column(String(255), nullable=False)
    short_video_link = Column(String(255), nullable=True)
    full_video_link = Column(String(255), nullable=True)
    program_text = Column(Text, nullable=True)
    duration = Column(String(50), nullable=True)

    section = relationship("Section", back_populates="modules")

    def __repr__(self):
        return f"<Module(id={self.id}, title='{self.title}', section_id={self.section_id})>"


# -------------------------------------------------------------------
# 4. Лендинг (один курс — один лендинг)
# -------------------------------------------------------------------
class Landing(Base):
    __tablename__ = "landing"

    id = Column(Integer, primary_key=True, index=True)
    language = Column(Enum(LanguageEnum, name="lang_enum"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=True)
    main_image = Column(String(255), nullable=True)
    duration = Column(String(50), nullable=True)
    old_price = Column(Numeric(10, 2), nullable=True)
    price = Column(Numeric(10, 2), nullable=True)
    main_text = Column(Text, nullable=True)
    slug = Column(String(255), nullable=True)
    sales_count = Column(Integer, nullable=False, default=0)

    # Связь с таблицей тегов
    tag = relationship("Tag", back_populates="landings")

    # Связь many-to-many с авторами
    authors = relationship(
        "Author",
        secondary=landing_authors,
        back_populates="landings"
    )
    # Лендинг относится к ровно одному курсу
    course = relationship("Course", back_populates="landing")

    def __repr__(self):
        return f"<Landing(id={self.id}, title='{self.title}', lang={self.language})>"

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)

    # Один тег может быть привязан к нескольким лендингам
    landings = relationship("Landing", back_populates="tag")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"