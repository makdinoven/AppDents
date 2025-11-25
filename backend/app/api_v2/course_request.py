from fastapi import APIRouter, HTTPException, Request
from ..schemas_v2.course_requests import CourseRequestIn, CourseRequestOut
from ..services_v2.course_requests import send_course_request_email

router = APIRouter()


@router.post("/course-request", response_model=CourseRequestOut)
async def create_course_request(payload: CourseRequestIn, request: Request):
    """Приём заявок на курсы от пользователей"""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    # Получаем домен из заголовка Host
    domain = request.headers.get("host", "unknown")

    sent_to, user_email = await send_course_request_email(
        payload.user_id, payload.text, domain
    )

    return {"status": "ok", "sent_to": sent_to, "user_email": user_email}
