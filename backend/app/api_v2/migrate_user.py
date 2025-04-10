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