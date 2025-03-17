from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Table, Enum
from sqlalchemy.orm import declarative_base, relationship

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
    language = Column(Enum('EN', 'RU', 'ES', name='landing_language'), nullable=False, server_default='EN')
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
    language = Column(Enum('EN', 'RU', 'ES', name='author_language'), nullable=False, server_default='EN')

    # Лендинги, к которым привязан автор
    landings = relationship("Landing", secondary=landing_authors, back_populates="authors")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(255))

    # Курсы, купленные пользователем, теперь через отдельное отношение
    courses = relationship("Course", secondary=users_courses, back_populates="users")
