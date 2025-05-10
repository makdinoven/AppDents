from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Table, Enum, Boolean, DateTime, func, Float
from sqlalchemy.orm import declarative_base, relationship, backref

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

    # balance = Column(Float, default=0.0, nullable=False)
    # referral_code = Column(String(20), unique=True, index=True)
    # invited_by_id = Column(Integer, ForeignKey("users.id"))

    courses = relationship("Course", secondary=users_courses, back_populates="users")
    # invited_users = relationship(
    #     "User",
    #     backref=backref("inviter", remote_side=[id]),
    #     foreign_keys="[User.invited_by_id]",
    # )


class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    landing_id = Column(Integer, ForeignKey('landings.id'), nullable=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=True)
    created_at = Column(DateTime, server_default=func.utc(), nullable=False)
    stripe_event_id = Column(String(255), unique=True, nullable=True)

    # Если хотите хранить "покупка была из рекламы или нет"
    from_ad = Column(Boolean, default=False)
    amount = Column(Float, nullable=False, default=0.0)

    user = relationship("User", backref="purchases")
    landing = relationship("Landing", backref="purchases")
    course = relationship("Course", backref="purchases")

class AdVisit(Base):
    __tablename__ = "ad_visits"
    id          = Column(Integer, primary_key=True)
    landing_id  = Column(Integer, ForeignKey("landings.id"), nullable=False)
    visited_at  = Column(DateTime, server_default=func.utc(), nullable=False)
    fbp         = Column(String(255))
    fbc         = Column(String(255))
    ip_address  = Column(String(45))

    landing = relationship("Landing", backref="ad_visits")
