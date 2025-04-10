import logging
import re

from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from sqlalchemy.orm import Session
import csv
import io


from ..db.database import SessionLocal
from ..models.models_v2 import User, Course


app = FastAPI()

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@router.post("/import-users")
async def import_users(file: UploadFile = File(...)):
    """
    Роут принимает CSV‑файл с данными пользователей.

    Для каждой записи выполняется:
      - Извлечение email из столбца "email". Если email отсутствует, запись пропускается.
      - Проверка наличия пользователя с таким email. Если найден – запись пропускается.
      - Создание нового пользователя без указания id (позволяя СУБД назначить новое значение).
      - Чтение пароля из поля "pass" и установка роли в "user".
      - Обработка поля "course": ожидается строковое представление списка ID курсов (например, "[212, 246, 66]").
        Для каждого ID, если курс найден в БД, выполняется привязка к пользователю через отношение many-to-many.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Допустимы только CSV файлы.")

    session: Session = SessionLocal()
    imported_count = 0

    try:
        content = await file.read()
        decoded = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(decoded))

        for row in csv_reader:
            email = row.get("email")
            if not email:
                continue  # Пропускаем строки без email

            # Если пользователь с таким email уже существует, пропускаем запись
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                continue

            # Создаём нового пользователя:
            # - Используем email из CSV,
            # - Берём пароль из поля "pass",
            # - Устанавливаем role в "user" независимо от данных CSV.
            new_user = User(
                email=email,
                password=row.get("pass"),  # значение из CSV (столбец "pass")
                role="user"
            )

            # Обработка поля "course":
            course_field = row.get("course")
            if course_field:
                # Удаляем пробелы и квадратные скобки, если они есть
                course_field = course_field.strip()
                if course_field.startswith("[") and course_field.endswith("]"):
                    course_field = course_field[1:-1]
                # Разбиваем строку по запятым и оставляем только числовые значения
                course_ids = [token.strip() for token in course_field.split(",") if token.strip().isdigit()]
                for cid in course_ids:
                    course = session.query(Course).filter(Course.id == int(cid)).first()
                    if course:
                        new_user.courses.append(course)

            session.add(new_user)
            imported_count += 1

        session.commit()
        return {"message": f"Импортировано {imported_count} новых пользователей."}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при импорте: {str(e)}")
    finally:
        session.close()


def normalize_course_name(name: str) -> str:
    """
    Нормализует название курса:
      - переводит строку в нижний регистр,
      - удаляет лишние пробелы,
      - заменяет несколько пробелов одним,
      - удаляет всю пунктуацию и спецсимволы,
      - удаляет оставшиеся пробелы.
    """
    normalized = name.lower().strip()  # перевод в нижний регистр и удаление пробелов по краям
    normalized = re.sub(r'\s+', ' ', normalized)  # замена нескольких пробелов одним
    normalized = re.sub(r'[^\w\s]', '', normalized)  # удаление всех символов, кроме букв, цифр и пробелов
    normalized = normalized.replace(" ", "")  # окончательное удаление всех пробелов
    return normalized


@router.post("/import-users-courses")
async def import_users_courses(file: UploadFile = File(...)):
    """
    Импортирует пользователей из CSV‑файла.

    Ожидаемый формат CSV (с заголовком):
        "id","name","email","pass","course","role"

    Особенности:
      - Поле email используется для проверки уникальности (если пользователь с таким email уже есть – строка пропускается).
      - Пароль берется по умолчанию ("default_password").
      - Для каждого импортированного пользователя роль устанавливается в "user" независимо от данных CSV.
      - Поле course содержит названия курсов, разделённые запятой.
        Для сопоставления с курсами в БД применяется нормализация названий (нижний регистр, удаление лишних символов и пробелов).
      - Создаются связи с курсами через ассоциативную таблицу.

    В ответе возвращается подробная статистика импорта.
    """
    # Чтение содержимого файла
    try:
        content = await file.read()
        decoded = content.decode("utf-8")
        logger.info("Файл успешно прочитан, размер: %d байт", len(decoded))
    except Exception as e:
        logger.error("Ошибка чтения файла: %s", str(e))
        raise HTTPException(status_code=400, detail="Ошибка чтения файла: " + str(e))

    # Создаем CSV-ридер; разделитель – запятая, кавычка – "
    csv_reader = csv.DictReader(io.StringIO(decoded), delimiter=',', quotechar='"')

    session: Session = SessionLocal()

    # Инициализация статистики импорта
    imported_users = 0
    total_csv_courses = 0  # сколько курсов встретилось во всех строках CSV
    total_courses_found = 0  # сколько курсов (после нормализации) нашли в БД
    total_associations = 0  # сколько связей создано

    try:
        # Заранее загружаем все курсы из БД и создаем mapping: нормализованное название -> объект Course
        courses_in_db = session.query(Course).all()
        logger.info("Загружено %d курсов из БД", len(courses_in_db))
        course_mapping = {}
        for course in courses_in_db:
            norm_name = normalize_course_name(course.name)
            course_mapping[norm_name] = course
            logger.debug("Курс из БД: %s -> нормализовано в %s", course.name, norm_name)

        # Обработка строк CSV
        row_count = 0
        for row in csv_reader:
            row_count += 1
            logger.debug("Обработка строки #%d: %s", row_count, row)

            email = row.get("email")
            if not email:
                logger.warning("Строка #%d пропущена - отсутствует email", row_count)
                continue  # пропускаем строки без email

            email = email.strip()
            logger.info("Строка #%d: обработан email: %s", row_count, email)

            # Проверка существования пользователя с таким email
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                logger.info("Строка #%d: пользователь с email %s уже существует, пропускаем", row_count, email)
                continue

            # Создаем нового пользователя с паролем по умолчанию и ролью "user"
            new_user = User(
                email=email,
                password="default_password",
                role="user"
            )
            logger.info("Строка #%d: создается новый пользователь: %s", row_count, email)

            # Обработка поля "course"
            courses_field = row.get("course")
            if courses_field:
                courses_field = courses_field.strip()
                # Если строка окружена квадратными скобками, удаляем их
                if courses_field.startswith("[") and courses_field.endswith("]"):
                    courses_field = courses_field[1:-1]
                # Разбиваем строку по запятой
                course_names = [token.strip() for token in courses_field.split(",") if token.strip()]
                total_csv_courses += len(course_names)
                logger.info("Строка #%d: найдено %d названий курсов: %s", row_count, len(course_names), course_names)
                # Используем множество для отслеживания добавленных курсов для данного пользователя
                added_courses = set()
                for cname in course_names:
                    norm_cname = normalize_course_name(cname)
                    logger.debug("Нормализованное название курса \"%s\" -> \"%s\"", cname, norm_cname)
                    if norm_cname in course_mapping:
                        total_courses_found += 1
                        course_obj = course_mapping[norm_cname]
                        if course_obj.id not in added_courses:
                            new_user.courses.append(course_obj)
                            added_courses.add(course_obj.id)
                            total_associations += 1
                            logger.info("Строка #%d: к пользователю %s привязан курс: %s (ID=%s)",
                                        row_count, email, course_obj.name, course_obj.id)
                    else:
                        logger.warning("Строка #%d: курс \"%s\" (нормализовано \"%s\") не найден в БД",
                                       row_count, cname, norm_cname)
            else:
                logger.info("Строка #%d: поле course пустое", row_count)

            session.add(new_user)
            imported_users += 1

        session.commit()
        logger.info("Импорт завершён. Всего обработано строк: %d", row_count)
        return {
            "message": f"Импорт завершён: создано {imported_users} новых пользователей.",
            "total_users_imported": imported_users,
            "total_csv_courses": total_csv_courses,
            "total_courses_found_in_db": total_courses_found,
            "total_courses_associations_created": total_associations
        }
    except Exception as e:
        session.rollback()
        logger.exception("Ошибка при импорте: %s", str(e))
        raise HTTPException(status_code=500, detail="Ошибка при импорте: " + str(e))
    finally:
        session.close()