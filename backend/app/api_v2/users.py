import secrets
import string
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload

from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, Purchase
from ..schemas_v2.course import CourseListResponse
from ..schemas_v2.user import ForgotPasswordRequest, UserCreateAdmin, UserShortResponse, UserDetailedResponse, \
    UserUpdateFull, UserDetailResponse, UserListPageResponse
from ..schemas_v2.user import UserCreate, UserRead, Token, UserUpdateRole, UserUpdatePassword, UserAddCourse, \
    UserRegistrationResponse
from ..services_v2.user_service import (
    create_user, authenticate_user, create_access_token,
    get_user_by_email, search_users_by_email, update_user_role, update_user_password, add_course_to_user,
    remove_course_from_user, delete_user, update_user_full, get_user_by_id, list_users_paginated,
    search_users_paginated, verify_password
)
from ..utils.email_sender import send_password_to_user, send_recovery_email

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

def generate_random_password(length=12) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@router.post("/register", response_model=UserRegistrationResponse)
def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    region: str = "EN",
    ref: str | None = Query(None, description="Referral code"),
    db: Session = Depends(get_db)
):
    """
    При регистрации можно передать ?ref=ABCD1234 – код пригласителя.
    """
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": { ... }}  # как было
        )

    inviter = db.query(User).filter(User.referral_code == ref).first() if ref else None
    random_pass = generate_random_password()
    user = create_user(
        db,
        email=user_data.email,
        password=random_pass,
        invited_by=inviter
    )

    background_tasks.add_task(send_password_to_user, user.email, random_pass, region)
    return {**UserRead.from_orm(user).dict(), "password": random_pass}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

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

    # Проверяем роль пользователя
    if user.role == 'admin':
        # Для админов проверяем пароль
        if not verify_password(form_data.password, user.password):
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

    # Для остальных пользователей пароль игнорируется
    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/search", response_model=List[UserRead], summary="Поиск  пользователей по email")
def search_users(email: str = Query(..., description="Часть email для поиска"), db: Session = Depends(get_db)):
    users = search_users_by_email(db, email)
    return users

@router.put("/{user_id}/role", response_model=UserRead, summary="Изменить роль пользователя")
def change_user_role(user_id: int, role_data: UserUpdateRole, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    user = update_user_role(db, user_id, role_data.role)
    return user


@router.put("/{user_id}/password", response_model=UserRead, summary="Изменить пароль пользователя")
def change_user_password(
        user_id: int,
        password_data: UserUpdatePassword,
        db: Session = Depends(get_db),
        region: str = 'EN',
        current_user: User = Depends(get_current_user)  # Зависимость для получения текущего пользователя
):
    # Проверяем: если пользователь не админ, то он может менять только свой пароль.
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="У вас нет прав для изменения пароля другого пользователя"
        )

    user = update_user_password(db, user_id, password_data.password, region)
    return user

@router.post("/admin/{user_id}/courses", summary="Добавить курс пользователю")
def add_course(user_id: int, course_data: UserAddCourse, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    add_course_to_user(db, user_id, course_data.course_id)
    return {"message": "Курс успешно добавлен пользователю"}

@router.post("/purchase", summary="Покупка курса (заглушка)", response_model=dict)
def purchase_course(purchase_data: UserAddCourse, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    add_course_to_user(db, current_user.id, purchase_data.course_id)
    return {"message": "Курс успешно куплен"}

@router.get("/me/courses", summary="Получить купленные курсы пользователя", response_model=List[CourseListResponse])
def get_purchased_courses(current_user: User = Depends(get_current_user)):
    purchased_courses = current_user.courses
    return purchased_courses

@router.post("/forgot-password", summary="Восстановление пароля", response_model=dict)
def forgot_password(
        forgot_data: ForgotPasswordRequest,
        background_tasks: BackgroundTasks,
        region: str = "EN",
        db: Session = Depends(get_db)
):
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
    update_user_password(db, user.id, new_password, region)
    return {"message": "New password send successfully", "new_password": new_password}

@router.post("/admin/users", response_model=UserRead, summary="Создать нового пользователя (Админ)")
def create_user_admin(
    user_data: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """
    Создаёт пользователя с переданным паролем и ролью.
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
    user = create_user(db, email=user_data.email, password=user_data.password, role=user_data.role)
    return UserRead.from_orm(user)

@router.get(
    "/admin/users",
    response_model=UserListPageResponse,
    summary="Список всех пользователей (Админ)"
)
def get_all_users(
    page: int = Query(1, ge=1, description="Номер страницы, начиная с 1"),
    size: int = Query(10, gt=0, description="Размер страницы"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
) -> dict:
    """
    Возвращает пагинированный список всех пользователей:
    {
      total: <общее число>,
      total_pages: <число страниц>,
      page: <текущая страница>,
      size: <размер страницы>,
      items: […UserShortResponse…]
    }
    """
    return list_users_paginated(db, page=page, size=size)


@router.get(
    "/admin/users/search",
    response_model=UserListPageResponse,
    summary="Поиск пользователей по email (Админ)"
)
def search_users(
    q: str = Query(..., min_length=1, description="Подстрока для поиска в email"),
    page: int = Query(1, ge=1, description="Номер страницы, начиная с 1"),
    size: int = Query(10, gt=0, description="Размер страницы"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
) -> dict:
    """
    То же, что /admin/users, но с фильтром по email:
    {
      total: <число совпадений>,
      total_pages: <число страниц>,
      page: <текущая страница>,
      size: <размер страницы>,
      items: […UserShortResponse…]
    }
    """
    return search_users_paginated(db, q=q, page=page, size=size)


@router.delete("/admin/{user_id}", summary="Удалить пользователя (Админ)")
def delete_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """
    Полностью удаляет пользователя из БД.
    """
    delete_user(db, user_id)
    return {"message": "Пользователь успешно удален"}

@router.delete("/admin/{user_id}/courses/{course_id}", summary="Удалить у пользователя купленный курс (Админ)")
def remove_user_course(
    user_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """
    Удаляет у пользователя уже купленный/добавленный курс.
    """
    remove_course_from_user(db, user_id, course_id)
    return {"message": "Курс успешно удален у пользователя"}

@router.get(
    "/admin/{user_id}/detail",
    response_model=UserDetailedResponse,
    summary="Детальная информация о пользователе (Админ)"
)
def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """
    Возвращает полную информацию о пользователе, включая роль,
    купленные курсы и все покупки с полями landing_slug и landing_name.
    """
    user = (
        db.query(User)
        .options(
            joinedload(User.courses),
            joinedload(User.purchases).joinedload(Purchase.landing)
        )
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not found",
                    "translation_key": "error.user_not_found",
                    "params": {"user_id": user_id}
                }
            }
        )
    return user

# 2) Полный PUT — обновляем все поля,
#    аналогично update_landing (вместо отдельных update_role, update_password и т.д.)
@router.put("/{user_id}", response_model=UserDetailResponse)
def update_user_full_route(
    user_id: int,
    user_data: UserUpdateFull,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """
    Полное обновление пользователя за один раз:
    email, role, password, привязка к списку курсов и т.д.
    """
    updated_user = update_user_full(db, user_id, user_data)
    return updated_user