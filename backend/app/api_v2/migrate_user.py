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
    Роут принимает CSV-файл с данными пользователей. Для каждой записи он:
    - Проверяет наличие пользователя с таким email (уникальность email);
    - Создаёт нового пользователя (без использования id из дампа);
    - Читает из поля 'course' идентификаторы курсов (один или несколько, разделённых запятыми);
    - Для каждого найденного ID пытается найти соответствующий курс в БД и присоединяет его к пользователю.
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
                continue  # Если email отсутствует, пропускаем запись

            # Проверяем, есть ли уже пользователь с таким email
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                continue  # Пропускаем запись, если пользователь уже существует

            # Создаём нового пользователя.
            # Обратите внимание: не задаём значение id – оно будет автоинкрементным.
            new_user = User(
                email=email,
                password=row.get("password"),
                role=row.get("role")
            )

            # Обработка поля "course" – ожидаем, что там может быть список ID курсов, разделённых запятыми.
            course_field = row.get("course")
            if course_field:
                # Разбиваем строку по запятым и оставляем только числовые значения
                course_ids = [token.strip() for token in course_field.split(",") if token.strip().isdigit()]
                for cid in course_ids:
                    course = session.query(Course).filter(Course.id == int(cid)).first()
                    if course:
                        # Связываем пользователя с курсом через отношение many-to-many
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
