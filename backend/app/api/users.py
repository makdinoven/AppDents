# backend/app/api/users.py
import secrets
import string
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.user_service import (
    create_user, authenticate_user, create_access_token, decode_access_token,
    get_user_by_email, get_user_by_id, search_users_by_email, update_user_role, update_user_password, add_course_to_user
)
from app.schemas.user import (
    UserCreate, UserLogin, UserRead, Token,
    UserUpdateRole, UserUpdatePassword, UserAddCourse
)
from app.models.models import User

from app.schemas.course import CourseResponse

from ..dependencies.role_checker import require_roles

from ..dependencies.auth import get_current_user
from ..schemas.user import ForgotPasswordRequest, UserRegistrationResponse
from ..utils.email_sender import send_password_to_user, send_recovery_email
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
def generate_random_password(length=12) -> str:
    """
    Генерация случайного пароля заданной длины.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/register", response_model=UserRegistrationResponse)
def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Регистрирует нового пользователя, генерирует случайный пароль,
    сохраняет его в БД в зашифрованном виде и отправляет письмо с паролем.
    На этапе разработки возвращает пароль в ответе.
    """
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "EMAIL_EXIST",
                    "message": f"User with email {user_data.email} already exists.",
                    "translation_key": "error.email_exist",
                    "params": {"email": user_data.email}
                }
            }
        )

    # Генерируем новый пароль
    random_pass = generate_random_password()

    # Создаем пользователя (пароль сохраняется в зашифрованном виде)
    user = create_user(db, email=user_data.email, password=random_pass)

    # Фоновая задача для отправки письма (в будущем будет отправка пароля по почте)
    background_tasks.add_task(send_password_to_user, user.email, random_pass)

    # Преобразуем пользователя в pydantic-схему и добавляем пароль в ответ
    user_read = UserRead.from_orm(user)
    return {**user_read.dict(), "password": random_pass}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Incorrect username or password",
                    "translation_key": "error.invalid_credentials",
                    "params": {}
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Генерация JWT
    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}



@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Возвращает текущего пользователя (информация из JWT).
    """
    return current_user

# Поиск пользователей по части email
@router.get("/search", response_model=list[UserRead], summary="Поиск пользователей по email")
def search_users(email: str = Query(..., description="Часть email для поиска"), db: Session = Depends(get_db)):
    users = search_users_by_email(db, email)
    return users

# Изменение роли пользователя
@router.put("/{user_id}/role", response_model=UserRead, summary="Изменить роль пользователя")
def change_user_role(user_id: int, role_data: UserUpdateRole, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    try:
        user = update_user_role(db, user_id, role_data.role)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Изменение пароля пользователя (новый пароль хэшируется и сохраняется)
@router.put("/{user_id}/password", response_model=UserRead, summary="Изменить пароль пользователя")
def change_user_password(user_id: int, password_data: UserUpdatePassword, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    try:
        user = update_user_password(db, user_id, password_data.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Добавление курса пользователю (создаётся запись в таблице UserCourses)
@router.post("/{user_id}/courses", summary="Добавить курс пользователю")
def add_course(user_id: int, course_data: UserAddCourse, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
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


@router.post("/forgot-password", summary="Восстановление пароля", response_model=dict)
def forgot_password(
        forgot_data: ForgotPasswordRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """
    Принимает email пользователя.
    Если пользователь найден, генерирует новый пароль, обновляет его в БД
    (в зашифрованном виде), отправляет письмо с новым паролем на указанный адрес и
    возвращает новый пароль в ответе (временное решение).

    Если пользователь не найден, вызывает исключение.
    """
    user = get_user_by_email(db, forgot_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": f"Пользователь с email {forgot_data.email} не найден",
                    "translation_key": "error.user_not_found",
                    "params": {"email": forgot_data.email}
                }
            }
        )
    new_password = generate_random_password()
    # Обновляем пароль пользователя (функция update_user_password хэширует пароль)
    update_user_password(db, user.id, new_password)
    # Отправляем новый пароль на почту в фоне
    background_tasks.add_task(send_recovery_email, user.email, new_password)
    return {"message": "New password send successfully", "new_password": new_password}
