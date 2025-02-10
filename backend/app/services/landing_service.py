# services/landings.py
from typing import List

from sqlalchemy.orm import Session
from ..models.models import Landing, Course, Section, Module, Author
from ..schemas.landing import LandingCreate, LandingUpdate, LanguageEnum


def create_landing(db: Session, landing_data: LandingCreate) -> Landing:
    # Получаем курс по course_id
    course = db.query(Course).filter(Course.id == landing_data.course_id).first()
    if not course:
        raise ValueError("Курс не найден")

    # Создаем объект лендинга
    landing = Landing(
        language=landing_data.language,
        course_id=landing_data.course_id,
        title=landing_data.title,
        tag=landing_data.tag,
        main_image=landing_data.main_image,
        old_price=landing_data.old_price,
        price=landing_data.price,
        main_text=landing_data.main_text
    )
    db.add(landing)
    db.flush()  # чтобы получить id лендинга до commit

    # Добавляем лекторов (авторов)
    if landing_data.authors:
        authors = db.query(Author).filter(Author.id.in_(landing_data.authors)).all()
        if not authors:
            raise ValueError("Не найден ни один из указанных лекторов")
        landing.authors.extend(authors)

    # Добавляем модули в курс, если они указаны
    if landing_data.modules:
        # Если у курса уже есть секции, используем первую
        if course.sections:
            section = course.sections[0]
        else:
            # Иначе создаем новую секцию с именем по умолчанию
            section = Section(course_id=course.id, name="Основной раздел")
            db.add(section)
            db.flush()
            course.sections.append(section)
        # Для каждого модуля создаем объект и привязываем к секции
        for module_data in landing_data.modules:
            module = Module(
                section_id=section.id,
                title=module_data.title,
                short_video_link=module_data.short_video_link,
                full_video_link=module_data.full_video_link,
                program_text=module_data.program_text,
                duration=module_data.duration
            )
            db.add(module)
        # Если передана программа курса, обновляем описание курса
        if landing_data.main_text:
            course.description = landing_data.main_text

    db.commit()
    db.refresh(landing)
    # Для формирования ответа с модулями получаем список модулей курса
    if landing.course:
        landing.modules = landing.course.modules
    return landing

def update_landing(db: Session, landing_id: int, landing_data: LandingUpdate) -> Landing:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise ValueError("Лендинг не найден")
    # Обновляем поля лендинга, если они указаны
    if landing_data.title is not None:
        landing.title = landing_data.title
    if landing_data.tag is not None:
        landing.tag = landing_data.tag
    if landing_data.main_image is not None:
        landing.main_image = landing_data.main_image
    if landing_data.old_price is not None:
        landing.old_price = landing_data.old_price
    if landing_data.price is not None:
        landing.price = landing_data.price
    if landing_data.main_text is not None:
        landing.main_text = landing_data.main_text
        if landing.course:
            landing.course.description = landing_data.main_text
    if landing_data.language is not None:
        landing.language = landing_data.language
    if landing_data.course_id is not None:
        course = db.query(Course).filter(Course.id == landing_data.course_id).first()
        if not course:
            raise ValueError("Новый курс не найден")
        landing.course_id = landing_data.course_id
        landing.course = course
    if landing_data.authors is not None:
        authors = db.query(Author).filter(Author.id.in_(landing_data.authors)).all()
        landing.authors = authors
    if landing_data.modules is not None:
        # Обновляем модули: удаляем все модули в первой секции и добавляем новые
        if landing.course:
            if landing.course.sections:
                section = landing.course.sections[0]
            else:
                section = Section(course_id=landing.course.id, name="Основной раздел")
                db.add(section)
                db.flush()
                landing.course.sections.append(section)
            # Удаляем старые модули из секции
            for module in list(section.modules):
                db.delete(module)
            # Добавляем новые модули
            for mod_data in landing_data.modules:
                module = Module(
                    section_id=section.id,
                    title=mod_data.title,
                    short_video_link=mod_data.short_video_link,
                    full_video_link=mod_data.full_video_link,
                    program_text=mod_data.program_text,
                    duration=mod_data.duration
                )
                db.add(module)
        else:
            raise ValueError("Лендинг не привязан к курсу, невозможно обновить модули")
    db.commit()
    db.refresh(landing)
    if landing.course:
        landing.modules = landing.course.modules
    return landing

def delete_landing(db: Session, landing_id: int) -> Landing:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise ValueError("Лендинг не найден")
    db.delete(landing)
    db.commit()
    return landing

def get_landing_cards(db: Session):
    # Возвращаем все лендинги – для карточек достаточно основных полей и списка авторов
    landings = db.query(Landing).all()
    return landings

def get_landing_by_id(db: Session, landing_id: int):
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise ValueError("Лендинг не найден")
    if landing.course:
        landing.modules = landing.course.modules
    return landing

def get_landings_by_language(db: Session, language: LanguageEnum):
    """
    Возвращает список лендингов, отфильтрованных по языку.
    """
    landings = db.query(Landing).filter(Landing.language == language).all()
    return landings

def search_landings(db: Session, query: str) -> List[Landing]:
    """
    Ищет лендинги по части названия (регистронезависимый поиск).
    """
    landings = db.query(Landing).filter(Landing.title.ilike(f"%{query}%")).all()
    return landings