import re

from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from sqlalchemy.orm import Session
import csv
import io

from ..db.database import SessionLocal
from ..models.models_v2 import User, Course


app = FastAPI()

router = APIRouter()
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
      - Переводит строку в нижний регистр,
      - Удаляет лишние пробелы,
      - Убирает все символы, кроме букв и цифр (то есть удаляет пунктуацию и спецсимволы),
      - Удаляет оставшиеся пробелы, чтобы получить компактную строку.
    """
    normalized = name.lower().strip()  # нижний регистр и удаление пробелов по краям
    normalized = re.sub(r'\s+', ' ', normalized)  # замена множественных пробелов одним
    normalized = re.sub(r'[^\w\s]', '', normalized)  # удаление пунктуации и специальных символов
    normalized = normalized.replace(" ", "")  # удаление всех пробелов
    return normalized


@app.post("/import-users-courses")
async def import_users_courses(file: UploadFile = File(...)):
    """
    Импортирует пользователей из CSV-файла, где данные идут в следующем порядке (разделитель — табуляция):
      1. email
      2. full name
      3. status
      4. created_at
      5. updated_at
      6. courses – список названий курсов, разделённых запятыми

    Для каждого пользователя:
      - Если пользователь с таким email уже существует, строка пропускается.
      - Создаётся новый пользователь с:
          - email из CSV,
          - паролем, установленным по умолчанию ("default_password"),
          - ролью "user".
      - Из поля courses разбираются названия курсов. Каждое название нормализуется.
      - Если после нормализации находится соответствующий курс в БД (также нормализованное имя), он привязывается к пользователю.

    В ответе возвращается подробная статистика импорта:
      - Количество импортированных пользователей,
      - Общее количество курсов, найденных в CSV,
      - Количество курсов, найденных в БД по нормализованным названиям,
      - Количество созданных связей (ассоциаций) пользователей с курсами.
    """
    # Проверяем расширение файла (можно доработать проверку)
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Допустимы только CSV файлы.")

    session: Session = SessionLocal()
    # Статистика импорта
    imported_users = 0
    total_csv_courses = 0
    total_courses_found = 0
    total_courses_assigned = 0

    try:
        # Читаем содержимое файла и декодируем
        content = await file.read()
        decoded = content.decode("utf-8")

        # Предполагаем, что CSV не содержит заголовок, поэтому задаём имена столбцов
        fieldnames = ["email", "name", "status", "created_at", "updated_at", "courses"]
        csv_reader = csv.DictReader(io.StringIO(decoded), delimiter='\t', fieldnames=fieldnames)

        # Для повышения эффективности – один раз загружаем все курсы из БД
        courses_in_db = session.query(Course).all()
        # Создаём mapping: normalized_name -> Course
        course_mapping = {}
        for course in courses_in_db:
            norm_name = normalize_course_name(course.name)
            course_mapping[norm_name] = course

        for row in csv_reader:
            email = row.get("email")
            if not email:
                continue  # пропускаем строки без email

            # Если пользователь с данным email уже существует – пропускаем импорт
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                continue

            # Создаём нового пользователя с паролем по умолчанию и ролью "user"
            new_user = User(
                email=email,
                password="default_password",  # установите подходящий пароль по умолчанию
                role="user"
            )

            # Обработка курса: поле courses – строка с названиями, разделёнными запятыми
            courses_field = row.get("courses")
            if courses_field:
                # Разбиваем строку по запятой
                course_names = [token.strip() for token in courses_field.split(",") if token.strip()]
                total_csv_courses += len(course_names)
                # Для каждого названия нормализуем и пытаемся найти в mapping
                for course_name in course_names:
                    norm_course = normalize_course_name(course_name)
                    if norm_course in course_mapping:
                        total_courses_found += 1
                        course_obj = course_mapping[norm_course]
                        # Привязываем курс к пользователю, если ещё не привязан
                        if course_obj not in new_user.courses:
                            new_user.courses.append(course_obj)
                            total_courses_assigned += 1

            session.add(new_user)
            imported_users += 1

        session.commit()
        return {
            "message": f"Импортировано {imported_users} новых пользователей.",
            "total_users_imported": imported_users,
            "total_csv_courses": total_csv_courses,
            "total_courses_found_in_db": total_courses_found,
            "total_courses_assigned": total_courses_assigned
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при импорте: {str(e)}")
    finally:
        session.close()