from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from enum import Enum

class LanguageEnum(str, Enum):
    EN = "en"
    ES = "es"
    RU = "ru"
