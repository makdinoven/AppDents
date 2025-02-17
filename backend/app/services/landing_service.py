# services/landings.py
from typing import List, cast

from sqlalchemy.orm import Session
from ..models.models import Landing, Course, Section, Module, Author, Tag
from ..schemas.landing import LandingCreate, LandingUpdate, LanguageEnum


def create_landing(db: Session, landing_data: LandingCreate) -> Landing:
    # Получаем курс по course_id
    course = db.query(Course).filter(Course.id == landing_data.course_id).first()
    if not course:
        raise ValueError("Курс не найден")

    # Проверяем наличие тега
    tag = db.query(Tag).filter(Tag.id == landing_data.tag_id).first()
    if not tag:
        raise ValueError("Тег не найден")

    # Создаем объект лендинга с учетом sales_count
    landing = Landing(
        language=landing_data.language,
        course_id=landing_data.course_id,
        title=landing_data.title,
        tag_id=landing_data.tag_id,
        main_image=landing_data.main_image,
        old_price=landing_data.old_price,
        price=landing_data.price,
        main_text=landing_data.main_text,
        sales_count=landing_data.sales_count or 0  # если значение не передано, по умолчанию 0
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
        if course.sections:
            section = course.sections[0]
        else:
            from ..models.models import Section
            section = Section(course_id=course.id, name="Основной раздел")
            db.add(section)
            db.flush()
            course.sections.append(section)
        for module_data in landing_data.modules:
            from ..models.models import Module
            module = Module(
                section_id=section.id,
                title=module_data.title,
                short_video_link=module_data.short_video_link,
                full_video_link=module_data.full_video_link,
                program_text=module_data.program_text,
                duration=module_data.duration
            )
            db.add(module)
        if landing_data.main_text:
            course.description = landing_data.main_text

    db.commit()
    db.refresh(landing)
    if landing.course:
        landing.modules = landing.course.modules
    return landing


def update_landing(db: Session, landing_id: int, landing_data: LandingUpdate) -> Landing:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise ValueError("Лендинг не найден")

    if landing_data.title is not None:
        landing.title = landing_data.title
    if landing_data.tag_id is not None:
        tag = db.query(Tag).filter(Tag.id == landing_data.tag_id).first()
        if not tag:
            raise ValueError("Тег не найден")
        landing.tag_id = landing_data.tag_id
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
        if landing.course:
            # Если секции уже существуют, используем первую
            if landing.course.sections:
                section = landing.course.sections[0]
            else:
                # Используем cast для явного указания, что course_id – это int
                section = Section(course_id=cast(int, landing.course_id), name="Основной раздел")
                db.add(section)
                db.flush()  # Чтобы получить section.id
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
    # Обработка ручного ввода числа продаж
    if landing_data.sales_count is not None:
        landing.sales_count = landing_data.sales_count

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

def get_landings_by_language(db: Session, language: LanguageEnum, skip: int = 0, limit: int = 30):
    """
    Возвращает список лендингов, отфильтрованных по языку, с поддержкой пагинации.
    :param db: Сессия БД
    :param language: Язык лендинга (en, es, ru)
    :param skip: Количество пропускаемых записей (offset)
    :param limit: Максимальное количество возвращаемых записей
    :return: Список лендингов
    """
    landings = (
        db.query(Landing)
        .filter(Landing.language == language)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return landings


def search_landings(db: Session, query: str) -> List[Landing]:
    """
    Ищет лендинги по части названия (регистронезависимый поиск).
    """
    landings = db.query(Landing).filter(Landing.title.ilike(f"%{query}%")).all()
    return landings