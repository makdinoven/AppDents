from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255))


    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь с таблицей UserCourses (один пользователь -> много записей в UserCourses)
    courses = relationship("UserCourses", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"


class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False, default=0.00)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связь с таблицей UserCourses (один курс -> много записей в UserCourses)
    users = relationship("UserCourses", back_populates="course")

    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}', price={self.price})>"


class UserCourses(Base):
    __tablename__ = 'user_courses'

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)

    purchase_date = Column(DateTime(timezone=True), server_default=func.now())
    price_at_purchase = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Связи (связующая таблица многие-ко-многим через отдельную модель)
    user = relationship("User", back_populates="courses")
    course = relationship("Course", back_populates="users")

    def __repr__(self):
        return f"<UserCourses(id={self.id}, user_id={self.user_id}, course_id={self.course_id})>"
