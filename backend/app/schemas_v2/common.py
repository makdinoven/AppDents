from typing import Optional, List, Union, Any, Dict
from enum import Enum

from pydantic import BaseModel, Field


# ═══════════════════ Контексты для фильтров ═══════════════════

class FilterContext(str, Enum):
    """
    Контекст применения фильтра.
    
    Определяет, для какой сущности выполняется поиск/фильтрация.
    """
    BOOKS = "books"           # Каталог книг
    COURSES = "courses"       # Каталог курсов
    AUTHORS_PAGE = "authors"  # Страница авторов


class AuthorCardResponse(BaseModel):
    id: int
    name: str
    photo: Optional[str] = None  # добавили фото

    class Config:
        orm_mode = True

class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


# ═══════════════════ Универсальные схемы фильтров ═══════════════════

class FilterOption(BaseModel):
    """
    Опция для фильтра с множественным выбором.
    
    Используется для publishers, authors, tags, formats и т.д.
    """
    id: Optional[int] = Field(None, description="ID опции (для entities с БД)")
    value: Optional[str] = Field(None, description="Значение опции (для enum-ов типа formats)")
    name: str = Field(..., description="Отображаемое название опции")
    count: int = Field(..., description="Количество элементов с этой опцией после применения текущих фильтров")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Quintessence Publishing",
                "count": 25
            }
        }


class FilterTypeEnum(str, Enum):
    """Типы фильтров для универсальной системы."""
    MULTISELECT = "multiselect"  # Множественный выбор (чекбоксы)
    RANGE = "range"               # Диапазон (слайдер)
    CHECKBOX = "checkbox"         # Одиночный чекбокс


class MultiselectFilter(BaseModel):
    """
    Фильтр с множественным выбором.
    
    Используется для publishers, authors, tags, formats.
    """
    type: FilterTypeEnum = FilterTypeEnum.MULTISELECT
    label: str = Field(..., description="Название фильтра для UI")
    param_name: str = Field(..., description="Имя параметра для query string")
    options: List[FilterOption] = Field(default_factory=list, description="Список доступных опций")
    has_more: bool = Field(default=False, description="Есть ли еще опции сверх лимита")
    total_count: int = Field(default=0, description="Общее количество опций")
    search_endpoint: Optional[str] = Field(None, description="Эндпоинт для поиска по этому фильтру")

    class Config:
        schema_extra = {
            "example": {
                "type": "multiselect",
                "label": "Издатели",
                "param_name": "publisher_ids",
                "options": [
                    {"id": 1, "name": "Quintessence Publishing", "count": 25},
                    {"id": 2, "name": "Wiley", "count": 12}
                ],
                "has_more": True,
                "total_count": 127,
                "search_endpoint": "/api/books/filters/publishers/search"
            }
        }


class RangeFilter(BaseModel):
    """
    Фильтр диапазона (слайдер).
    
    Используется для price, year, pages.
    """
    type: FilterTypeEnum = FilterTypeEnum.RANGE
    label: str = Field(..., description="Название фильтра для UI")
    param_name_from: str = Field(..., description="Имя параметра 'от' для query string")
    param_name_to: str = Field(..., description="Имя параметра 'до' для query string")
    min: Optional[Union[int, float]] = Field(None, description="Минимальное значение")
    max: Optional[Union[int, float]] = Field(None, description="Максимальное значение")
    unit: Optional[str] = Field(None, description="Единица измерения (USD, pages, year)")

    class Config:
        schema_extra = {
            "example": {
                "type": "range",
                "label": "Цена",
                "param_name_from": "price_from",
                "param_name_to": "price_to",
                "min": 9,
                "max": 300,
                "unit": "USD"
            }
        }


class SortOption(BaseModel):
    """Опция сортировки."""
    value: str = Field(..., description="Значение для query string")
    label: str = Field(..., description="Отображаемое название")

    class Config:
        schema_extra = {
            "example": {
                "value": "price_asc",
                "label": "Цена: по возрастанию"
            }
        }


class SelectedMultiselectValues(BaseModel):
    """Выбранные значения для multiselect-фильтра."""
    options: List[FilterOption] = Field(
        default_factory=list,
        description="Полные данные выбранных опций (id, name, count)"
    )


class SelectedRangeValues(BaseModel):
    """Выбранные значения для range-фильтра."""
    value_from: Optional[Union[int, float]] = Field(None, description="Выбранное значение 'от'")
    value_to: Optional[Union[int, float]] = Field(None, description="Выбранное значение 'до'")


class SelectedFilters(BaseModel):
    """
    Все выбранные пользователем фильтры с полными данными.
    
    Позволяет фронтенду отображать выбранные фильтры даже после очистки строки поиска.
    """
    publishers: Optional[SelectedMultiselectValues] = None
    authors: Optional[SelectedMultiselectValues] = None
    tags: Optional[SelectedMultiselectValues] = None
    formats: Optional[SelectedMultiselectValues] = None
    year: Optional[SelectedRangeValues] = None
    price: Optional[SelectedRangeValues] = None
    pages: Optional[SelectedRangeValues] = None


class CatalogFiltersMetadata(BaseModel):
    """
    Метаданные всех доступных фильтров и сортировок для каталога.
    
    Универсальная структура, используемая для книг, курсов, авторов и т.д.
    """
    filters: Dict[str, Union[MultiselectFilter, RangeFilter]] = Field(
        default_factory=dict,
        description="Словарь фильтров по ключам (publishers, authors, tags, formats, price, year, pages)"
    )
    available_sorts: List[SortOption] = Field(
        default_factory=list,
        description="Список доступных опций сортировки"
    )
    selected: Optional[SelectedFilters] = Field(
        None,
        description="Выбранные пользователем фильтры с полными данными"
    )

    class Config:
        schema_extra = {
            "example": {
                "filters": {
                    "publishers": {
                        "type": "multiselect",
                        "label": "Издатели",
                        "param_name": "publisher_ids",
                        "options": [
                            {"id": 1, "name": "Quintessence Publishing", "count": 25}
                        ],
                        "has_more": True,
                        "total_count": 127,
                        "search_endpoint": "/api/books/filters/publishers/search"
                    },
                    "price": {
                        "type": "range",
                        "label": "Цена",
                        "param_name_from": "price_from",
                        "param_name_to": "price_to",
                        "min": 9,
                        "max": 300,
                        "unit": "USD"
                    }
                },
                "available_sorts": [
                    {"value": "price_asc", "label": "Цена: по возрастанию"},
                    {"value": "price_desc", "label": "Цена: по убыванию"}
                ]
            }
        }


# ═══════════════════ Схемы для поиска по фильтрам ═══════════════════

class FilterSearchResponse(BaseModel):
    """
    Ответ при поиске по фильтру (авторы, издатели, теги).
    
    Используется для эндпоинтов поиска с автокомплитом.
    """
    total: int = Field(..., description="Общее количество найденных опций")
    options: List[FilterOption] = Field(default_factory=list, description="Список найденных опций")

    class Config:
        schema_extra = {
            "example": {
                "total": 15,
                "options": [
                    {"id": 42, "name": "John Smith", "count": 5},
                    {"id": 89, "name": "Jane Smith", "count": 3}
                ]
            }
        }