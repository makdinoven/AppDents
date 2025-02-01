# backend/app/api/users.py
import secrets
import string
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.user_service import (
    create_user, authenticate_user, create_access_token, decode_access_token,
    get_user_by_email, get_user_by_id, search_users_by_email, update_user_role,
    update_user_name, update_user_password, add_course_to_user
)
from app.schemas.user import (
    UserCreate, UserLogin, UserRead, Token,
    UserUpdateRole, UserUpdateName, UserUpdatePassword, UserAddCourse
)
from app.models.models import User

from app.schemas.course import CourseResponse

router = APIRouter()

def generate_random_password(length=12) -> str:
    """
    Генерация случайного пароля заданной длины.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Извлекаем JWT из заголовка Authorization, валидируем,
    возвращаем объект пользователя. Если нет прав, выбрасываем 401.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    try:
        token_data = decode_access_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).get(token_data.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

@router.post("/register", response_model=UserRead)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрируем пользователя, генерируем пароль, отправляем на почту (или нет).
    """
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    # Генерируем пароль
    random_pass = generate_random_password()

    # Создаём запись в БД (по умолчанию role="user")
    user = create_user(db, email=user_data.email, password=random_pass, name=user_data.name or "")

    # Отправляем пароль на почту (заглушка, нужно подключать реальную логику):
    # send_password_to_user(user.email, random_pass)

    return user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Генерируем JWT
    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Возвращает текущего пользователя (информация из JWT).
    """
    return current_user

@router.get("/admin-only")
def admin_only(current_user: User = Depends(get_current_user)):
    """
    Пример эндпоинта только для админа.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admins only.")
    return {"message": "Hello, Admin!"}

# --- Новые маршруты для управления пользователями ---

# Поиск пользователей по части email
@router.get("/search", response_model=list[UserRead], summary="Поиск пользователей по email")
def search_users(email: str = Query(..., description="Часть email для поиска"), db: Session = Depends(get_db)):
    users = search_users_by_email(db, email)
    return users

# Изменение роли пользователя
@router.put("/{user_id}/role", response_model=UserRead, summary="Изменить роль пользователя")
def change_user_role(user_id: int, role_data: UserUpdateRole, db: Session = Depends(get_db)):
    try:
        user = update_user_role(db, user_id, role_data.role)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Изменение имени пользователя
@router.put("/{user_id}/name", response_model=UserRead, summary="Изменить имя пользователя")
def change_user_name(user_id: int, name_data: UserUpdateName, db: Session = Depends(get_db)):
    try:
        user = update_user_name(db, user_id, name_data.name)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Изменение пароля пользователя (новый пароль хэшируется и сохраняется)
@router.put("/{user_id}/password", response_model=UserRead, summary="Изменить пароль пользователя")
def change_user_password(user_id: int, password_data: UserUpdatePassword, db: Session = Depends(get_db)):
    try:
        user = update_user_password(db, user_id, password_data.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Добавление курса пользователю (создаётся запись в таблице UserCourses)
@router.post("/{user_id}/courses", summary="Добавить курс пользователю")
def add_course(user_id: int, course_data: UserAddCourse, db: Session = Depends(get_db)):
    try:
        user_course = add_course_to_user(db, user_id, course_data.course_id, course_data.price_at_purchase)
        return {"message": "Курс успешно добавлен пользователю", "user_course_id": user_course.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Заглушка для покупки курса текущим пользователем (используем JWT)
@router.post("/purchase", summary="Покупка курса (заглушка)", response_model=dict)
def purchase_course(purchase_data: UserAddCourse, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Имитирует покупку курса текущим пользователем. Создаёт запись в таблице UserCourses.
    """
    try:
        user_course = add_course_to_user(db, current_user.id, purchase_data.course_id, purchase_data.price_at_purchase)
        return {"message": "Курс успешно куплен", "user_course_id": user_course.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Получение купленных курсов текущего пользователя
@router.get("/me/courses", summary="Получить купленные курсы пользователя", response_model=List[CourseResponse])
def get_purchased_courses(current_user: User = Depends(get_current_user)):
    """
    Возвращает список курсов, купленных текущим пользователем.
    Из объекта пользователя (User) извлекаем связь с UserCourses и возвращаем данные курса.
    """
    purchased_courses = [user_course.course for user_course in current_user.courses]
    return purchased_courses