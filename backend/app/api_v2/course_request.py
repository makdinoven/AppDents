from fastapi import APIRouter, HTTPException
from ..schemas_v2.course_requests import CourseRequestIn, CourseRequestOut
from ..services_v2.course_requests import send_course_request_email

router = APIRouter()


@router.post("/course-request", response_model=CourseRequestOut)
def create_course_request(payload: CourseRequestIn):
    """Приём заявок на курсы от пользователей"""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        sent_to, user_email = send_course_request_email(payload.user_id, payload.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ok", "sent_to": sent_to, "user_email": user_email}
