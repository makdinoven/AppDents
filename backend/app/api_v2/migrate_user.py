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
      - удаляет пробельные символы по краям,
      - заменяет несколько пробелов одним,
      - удаляет пунктуацию и спецсимволы,
      - убирает оставшиеся пробелы.
    """
    normalized = name.lower().strip()  # перевод в нижний регистр и удаление краевых пробелов
    normalized = re.sub(r'\s+', ' ', normalized)  # замена нескольких пробелов одним
    normalized = re.sub(r'[^\w\s]', '', normalized)  # удаление символов, кроме букв, цифр и пробелов
    normalized = normalized.replace(" ", "")  # окончательное удаление пробелов
    return normalized


@app.post("/import-users-courses-2")
async def import_users_courses_2(file: UploadFile = File(...)):
    """
    Импортирует пользователей из CSV‑файла, где данные представлены в виде:

      "email","name","status","created_at","updated_at","courses"

    Пример строки:
      "vladkravchenko@tutamail.com","Test User","Active","2024-06-19 14:12:45","2024-08-15 15:45:13","Tratamiento de impactacion. Protocolos de la doctora, ошибки и решения в лечении,AUTHOR'S COURSE OF ARNALDO CASTELLUСCI,TMJ radiology and occlusion,TADS AND ALIGNERS.,Ortodoncia BioFisiológica - Donde empezó la verdadera Evolución,ACABADO EN ORTODONCIA: ESTÉTICA EN LOS DETАЛЯХ,Mastery of Primary and Secondary MASTOPEXY,JEFFREY P. OKESON. OCCLUSION, TMJ DYSFUNCTIONS AND OROFACIAL PAIN FROM А TO Z,Онлайн-школа композитной реставрации с демонстрациями на пациентах,The ALL-ON-X – Implant Ninja"

    Логика импорта:
      - Проверяется, существует ли пользователь с данным email. Если да — строка пропускается.
      - Создаётся новый пользователь с паролем по умолчанию ("default_password") и ролью "user".
      - Из шестого поля разбираются названия курсов (разделитель — запятая). Для каждого названия производится нормализация
        (чтобы повысить вероятность совпадения с записями в БД).
      - Заранее из БД загружаются все курсы, и для каждого вычисляется нормализованное название.
      - Если после нормализации название из CSV совпадает с нормализованным названием курса в БД, курс привязывается к пользователю.

    В ответе возвращается подробная статистика импорта:
      - Количество импортированных пользователей,
      - Общее число курсов, полученных из CSV,
      - Количество курсов, найденных в БД,
      - Количество созданных связей (ассоциаций) пользователей с курсами.
    """
    # Чтение содержимого файла
    try:
        content = await file.read()
        decoded = content.decode("utf-8")
        logger.info("Файл успешно прочитан, размер: %d байт", len(decoded))
    except Exception as e:
        logger.error("Ошибка чтения файла: %s", str(e))
        raise HTTPException(status_code=400, detail="Ошибка чтения файла: " + str(e))

    # Определяем имена столбцов, так как в файле отсутствует заголовок
    fieldnames = ["email", "name", "status", "created_at", "updated_at", "courses"]
    csv_reader = csv.DictReader(io.StringIO(decoded), fieldnames=fieldnames, delimiter=',', quotechar='"')

    session: Session = SessionLocal()

    # Инициализация статистики импорта
    imported_users = 0
    total_csv_courses = 0  # общее количество курсов, полученных из CSV (суммарно по всем строкам)
    total_courses_found = 0  # количество курсов, сопоставленных с записями в БД
    total_associations = 0  # количество созданных связей (ассоциаций) пользователей с курсами
    row_count = 0

    try:
        # Загрузка всех курсов из БД для сопоставления
        courses_in_db = session.query(Course).all()
        logger.info("Загружено %d курсов из БД", len(courses_in_db))
        course_mapping = {}
        for course in courses_in_db:
            norm_name = normalize_course_name(course.name)
            course_mapping[norm_name] = course
            logger.debug("Курс из БД: '%s' -> нормализовано в '%s'", course.name, norm_name)

        # Обработка строк CSV
        for row in csv_reader:
            row_count += 1
            logger.debug("Обработка строки #%d: %s", row_count, row)

            email = row.get("email")
            if not email:
                logger.warning("Строка #%d пропущена — отсутствует email", row_count)
                continue
            email = email.strip()
            logger.info("Строка #%d: обработан email: %s", row_count, email)

            # Проверка: если пользователь с таким email уже существует, пропускаем
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                logger.info("Строка #%d: пользователь с email %s уже существует, пропускаем", row_count, email)
                continue

            # Создание нового пользователя с паролем по умолчанию и ролью "user"
            new_user = User(
                email=email,
                password="default_password",
                role="user"
            )
            logger.info("Строка #%d: создается новый пользователь %s", row_count, email)

            # Обработка поля с курсами (шестое поле CSV)
            courses_field = row.get("courses")
            if courses_field:
                courses_field = courses_field.strip()
                # Разбиваем строку по запятой
                course_names = [token.strip() for token in courses_field.split(",") if token.strip()]
                total_csv_courses += len(course_names)
                logger.info("Строка #%d: найдено %d названий курсов: %s", row_count, len(course_names), course_names)
                added_courses = set()  # для отслеживания, чтобы не дублировать привязки
                for cname in course_names:
                    norm_cname = normalize_course_name(cname)
                    logger.debug("Нормализовано '%s' -> '%s'", cname, norm_cname)
                    if norm_cname in course_mapping:
                        total_courses_found += 1
                        course_obj = course_mapping[norm_cname]
                        if course_obj.id not in added_courses:
                            new_user.courses.append(course_obj)
                            added_courses.add(course_obj.id)
                            total_associations += 1
                            logger.info("Строка #%d: к пользователю %s привязан курс '%s' (ID=%s)",
                                        row_count, email, course_obj.name, course_obj.id)
                    else:
                        logger.warning("Строка #%d: курс '%s' (нормализовано '%s') не найден в БД",
                                       row_count, cname, norm_cname)
            else:
                logger.info("Строка #%d: поле 'courses' пустое", row_count)

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