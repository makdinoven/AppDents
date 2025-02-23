import csv
import io
import re
import logging
import asyncio
from rapidfuzz import fuzz
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.models import User, UserCourses, Landing, LanguageEnum
from ..core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Порог совпадения для fuzzy-сравнения
FUZZY_THRESHOLD = 65


def normalize_text(text: str) -> str:
    """
    Приводит строку к нижнему регистру и удаляет все символы, кроме латинских букв и цифр.
    Это позволяет сравнивать "очищённые" строки.
    """
    return re.sub(r'[^a-z0-9]', '', text.lower())


async def process_csv_and_update_users(csv_content: str, db: AsyncSession) -> dict:
    """
    Асинхронно обрабатывает CSV с данными пользователей и их купленными курсами.

    CSV-файл должен содержать следующие колонки (в порядке):
      1. Email
      2. Имя пользователя
      3. Статус (например, Active)
      4. created_at (например, 2024-06-19 14:12:45)
      5. updated_at (например, 2024-08-15 15:45:13)
      6. Купленные курсы – строка с названиями, разделёнными запятыми

    Для каждой строки:
      - Ищется пользователь по email (предполагается, что все пользователи уже существуют).
      - Если пользователь найден, из строки с курсами разбивается список названий.
      - Загружаются все лендинги с языком EN из базы, и для каждого лендинга вычисляется нормализованное значение поля title.
      - Для каждого курса из CSV запускается fuzzy‑matching между нормализованным названием курса и нормализованными заголовками лендингов.
      - Если наилучшее совпадение имеет score не ниже порога, берётся поле course_id из лендинга, и для пользователя создаётся запись в таблице UserCourses (при этом проверяется, чтобы данная покупка ещё не была добавлена).
      - Если совпадение ниже порога, информация сохраняется для отчёта.

    Возвращает статистику:
      - new_user_courses: количество добавленных записей в UserCourses
      - unmatched: отсортированный по убыванию список несопоставленных курсов (с информацией о пользователе, названии из CSV, лучшем совпадении и score)
      - unmatched_count: общее число несопоставленных записей.
    """
    new_user_courses = 0
    unmatched_courses = []

    # Загружаем лендинги с языком EN из базы
    result = await db.execute(
        select(Landing).filter(Landing.language == LanguageEnum.EN)
    )
    landings_db = result.scalars().all()
    logger.debug("Загружено лендингов с языком EN: %d", len(landings_db))
    # Создаем список: (landing, нормализованное значение title)
    landings_normalized = [(landing, normalize_text(landing.title)) for landing in landings_db]

    # Используем io.StringIO для чтения CSV из строки
    csv_file = io.StringIO(csv_content)
    reader = csv.reader(csv_file, delimiter=',')

    for row in reader:
        # Проверяем, что строка содержит как минимум 6 колонок
        if not row or len(row) < 6:
            continue
        email = row[0].strip()
        # Остальные поля читаем, но для логики нам нужен email и поле с курсами
        courses_field = row[5].strip()

        logger.debug("Обработка пользователя: %s, Курсы: %s", email, courses_field)

        # Ищем пользователя по email
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        if not user:
            logger.warning("Пользователь с email %s не найден, пропуск строки.", email)
            continue

        # Разбиваем поле курсов по запятой
        course_names = [c.strip() for c in courses_field.split(',') if c.strip()]
        for course_name_csv in course_names:
            normalized_csv = normalize_text(course_name_csv)
            best_match = None
            best_score = 0

            # Запускаем fuzzy‑matching для каждого лендинга асинхронно
            tasks = [
                asyncio.to_thread(fuzz.ratio, normalized_csv, norm_title)
                for (_, norm_title) in landings_normalized
            ]
            scores = await asyncio.gather(*tasks)
            for i, score in enumerate(scores):
                if score > best_score:
                    best_score = score
                    best_match = landings_normalized[i][0]
            logger.debug("Лучшее совпадение для курса '%s': %s с score %d",
                         course_name_csv, best_match.title if best_match else None, best_score)
            if best_match and best_score >= FUZZY_THRESHOLD:
                # Проверяем, чтобы не было повторного присвоения
                existing_result = await db.execute(
                    select(UserCourses).filter(
                        UserCourses.user_id == user.id,
                        UserCourses.course_id == best_match.course_id
                    )
                )
                if existing_result.scalars().first():
                    logger.info("Курс '%s' (course_id=%s) уже присвоен пользователю %s, пропуск.",
                                best_match.title, best_match.course_id, email)
                    continue
                # Создаем запись в UserCourses, используя course_id из лендинга
                user_course = UserCourses(user_id=user.id, course_id=best_match.course_id, price_at_purchase=0.00)
                db.add(user_course)
                new_user_courses += 1
                logger.info("Добавлен курс '%s' (course_id=%s) пользователю %s", best_match.title, best_match.course_id,
                            email)
            else:
                unmatched_courses.append({
                    "user_email": email,
                    "course_csv": course_name_csv,
                    "best_match": best_match.title if best_match else None,
                    "best_score": best_score
                })
                logger.warning(
                    "Не найдено подходящего совпадения для курса '%s' пользователя %s. Лучшее совпадение: %s с score %d",
                    course_name_csv, email, best_match.title if best_match else "Нет", best_score)

    await db.commit()
    stats = {
        "new_user_courses": new_user_courses,
        "unmatched": sorted(unmatched_courses, key=lambda x: x["best_score"], reverse=True),
        "unmatched_count": len(unmatched_courses)
    }
    logger.debug("Импорт купленных курсов завершён. Статистика: %s", stats)
    return stats
