# services/modules.py
from typing import List

from sqlalchemy.orm import Session
from ..models.models import Section, Module
from ..schemas.course import ModuleCreate, ModuleUpdate

def create_module(db: Session, section_id: int, module_data: ModuleCreate) -> Module:
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise ValueError("Секция не найдена")
    module = Module(
        section_id=section_id,
        title=module_data.title,
        short_video_link=module_data.short_video_link,
        full_video_link=module_data.full_video_link,
        program_text=module_data.program_text,
        duration=module_data.duration
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module

def update_module(db: Session, module_id: int, module_data: ModuleUpdate) -> Module:
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise ValueError("Модуль не найден")
    if module_data.title is not None:
        module.title = module_data.title
    if module_data.short_video_link is not None:
        module.short_video_link = module_data.short_video_link
    if module_data.full_video_link is not None:
        module.full_video_link = module_data.full_video_link
    if module_data.program_text is not None:
        module.program_text = module_data.program_text
    if module_data.duration is not None:
        module.duration = module_data.duration
    db.commit()
    db.refresh(module)
    return module

def delete_module(db: Session, module_id: int) -> Module:
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise ValueError("Модуль не найден")
    db.delete(module)
    db.commit()
    return module

def get_module(db: Session, module_id: int) -> Module:
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise ValueError("Модуль не найден")
    return module

def search_modules(db: Session, query: str) -> List[Module]:
    """
    Ищет модули по части названия (регистронезависимый поиск).
    """
    modules = db.query(Module).filter(Module.title.ilike(f"%{query}%")).all()
    return modules