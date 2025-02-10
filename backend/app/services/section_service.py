# services/sections.py
from sqlalchemy.orm import Session
from ..models.models import Course, Section
from ..schemas.course import SectionCreate, SectionUpdate

def create_section(db: Session, course_id: int, section_data: SectionCreate) -> Section:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError("Курс не найден")
    section = Section(name=section_data.name, course_id=course_id)
    db.add(section)
    db.commit()
    db.refresh(section)
    return section

def update_section(db: Session, section_id: int, section_data: SectionUpdate) -> Section:
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise ValueError("Секция не найдена")
    if section_data.name is not None:
        section.name = section_data.name
    db.commit()
    db.refresh(section)
    return section

def delete_section(db: Session, section_id: int) -> Section:
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise ValueError("Секция не найдена")
    db.delete(section)
    db.commit()
    return section

def get_section(db: Session, section_id: int) -> Section:
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise ValueError("Секция не найдена")
    return section
