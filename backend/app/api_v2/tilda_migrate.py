from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, Course, Landing
import csv, io, re, unicodedata
from difflib import SequenceMatcher
try:
    from rapidfuzz import process, fuzz
    RAPID = True
except ImportError:
    RAPID = False

router = APIRouter()

# ---------- РУЧНЫЕ СООТВЕТСТВИЯ ---------- #
MANUAL_OVERRIDES = {
    # нормализованное название → ID курса
    "3step":                           245,
    "jeffreypokesonocclusion":        133,   # от "JEFFREY P. OKESON. OCCLUSION"
    "zblcimmediatemasterclass":       234,   # от "ZBLC Immediate MasterClass"
    "bopt":                            41,   # от "BOPT"
}
# ----------------------------------------- #

def strip_accents(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()

def norm_exact(t: str) -> str:
    t = strip_accents(t.lower())
    return re.sub(r"[^a-z0-9]", "", t)

def norm_tokens(t: str) -> str:
    t = strip_accents(t.lower())
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s{2,}", " ", t).strip()

def best_match(q: str, choices: list[str], thr: int = 70):
    if RAPID:
        _, score, idx = process.extractOne(q, choices, scorer=fuzz.token_set_ratio)
        return idx if score >= thr else None
    # fallback на difflib
    best_i, best_s = None, 0
    for i, c in enumerate(choices):
        s = SequenceMatcher(None, q, c).ratio() * 100
        if s > best_s:
            best_i, best_s = i, s
    return best_i if best_s >= thr else None

@router.post("/admin/import-purchases-csv", summary="Импорт покупок из CSV (ручные маппинги + fuzzy)")
def import_purchases_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = file.file.read().decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(content), delimiter=',', quotechar='"')

    db_courses = db.query(Course).all()
    exact_map  = {norm_exact(c.name): c for c in db_courses}
    clean_lst  = [norm_tokens(c.name) for c in db_courses]
    token_sets = [set(s.split()) for s in clean_lst]

    total, new_links = 0, 0
    users_nf, courses_nf = [], []

    for row in reader:
        total += 1
        if len(row) < 6:
            continue

        email = row[0].strip().strip('"')
        user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
        if not user:
            users_nf.append(email); continue

        for raw in [s.strip() for s in row[5].strip().strip('"').split(",") if s.strip()]:
            key_exact = norm_exact(raw)

            # --- 0. ручная привязка ---
            course = None
            if key_exact in MANUAL_OVERRIDES:
                course = db.query(Course).get(MANUAL_OVERRIDES[key_exact])

            # --- 1. точное совпадение по нормализованному имени ---
            if not course:
                course = exact_map.get(key_exact)

            # --- 2. подмножество токенов ---
            if not course:
                q_tokens = set(norm_tokens(raw).split())
                idx = next((i for i, ts in enumerate(token_sets) if q_tokens.issubset(ts)), None)
                if idx is not None:
                    course = db_courses[idx]

            # --- 3. RapidFuzz / difflib ---
            if not course:
                idx = best_match(norm_tokens(raw), clean_lst, thr=70)
                course = db_courses[idx] if idx is not None else None

            if not course:
                courses_nf.append(raw); continue

            if course not in user.courses:
                user.courses.append(course)
                new_links += 1
                for ln in (
                    db.query(Landing)
                      .filter(Landing.courses.any(Course.id == course.id))
                      .all()
                ):
                    ln.sales_count = (ln.sales_count or 0) + 1

        db.commit()

    return {
        "processed_rows": total,
        "users_not_found_count": len(users_nf),
        "courses_not_found_count": len(courses_nf),
        "new_user_course_links": new_links,
        "users_not_found": users_nf,
        "courses_not_found": courses_nf,
    }
