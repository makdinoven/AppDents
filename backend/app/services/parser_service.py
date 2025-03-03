# services/parser_service.py
import asyncio
import json
import logging
import re
import unicodedata
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from sqlalchemy import create_engine, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from ..models.models import Landing, Course, Section, Module, Author, LanguageEnum
from ..core.config import settings


def parse_and_save(html_content: str, language: LanguageEnum):
    soup = BeautifulSoup(html_content, 'lxml')

    # ============================
    # 1. Извлечение данных для лендинга
    # ============================
    # Заголовок лендинга: ищем элемент с field="title" и классом, содержащим "t017__title"
    title_tag = soup.find("div", attrs={"field": "title", "class": lambda v: v and "t017__title" in v})
    raw_landing_title = title_tag.get_text() if title_tag else "Без названия"
    landing_title = " ".join(raw_landing_title.split())

    # Основной текст: сначала пытаемся найти текст в блоке внутри контейнера t510__textwrapper с field="li_title__6597513368620"
    main_text_tag = soup.select_one("div.t510__textwrapper div[field='li_title__6597513368620']")
    if main_text_tag is None:
        main_text_tag = soup.find(attrs={"field": "bdescr"})
    raw_main_text = main_text_tag.get_text() if main_text_tag else ""
    main_text = " ".join(raw_main_text.split())

    # Общая длительность: пробуем сначала field="li_title__0267814275022", если нет – field="li_title__7984859014012"
    # Общая длительность курса: ищем сначала блок с field="li_title__0267814275022", если не найден – с field="li_title__7984859014012"
    # Общая длительность курса: ищем сначала блок с field="li_title__0267814275022", если не найден – с field="li_title__7984859014012"
    landing_duration = ""
    duration_tag = soup.find(attrs={"field": "li_title__0267814275022"})
    if duration_tag is None:
        duration_tag = soup.find(attrs={"field": "li_title__7984859014012"})
    if duration_tag:
        raw_duration_text = duration_tag.get_text()
        landing_duration = " ".join(raw_duration_text.split())
        # Обновленное регулярное выражение для английского, русского и испанского вариантов:
        m = re.search(r'(?:Duration:|Продолжительность:|Duración:)\s*(.+)', landing_duration)
        if m:
            landing_duration = m.group(1).strip()
        else:
            landing_duration = ""

    # Извлечение цен
    price = ""
    old_price = ""
    # 1. Попытка из блока t185__text (field="text")
    price_info_tag = soup.find("div", class_="t185__text", attrs={"field": "text"})
    if price_info_tag:
        raw_price_text = price_info_tag.get_text()
        price_text = " ".join(raw_price_text.split())
        numbers = re.findall(r'\d+', price_text)
        if len(numbers) >= 2:
            price = numbers[0]
            old_price = numbers[1]
    # 2. Если не нашли, пробуем из блока t142__wraptwo
    if not price and not old_price:
        price_alt_tag = soup.find("div", class_="t142__wraptwo")
        if price_alt_tag:
            span_tag = price_alt_tag.find("span", class_="t142__text")
            if span_tag:
                raw_alt_price = span_tag.get_text()
                normalized = unicodedata.normalize('NFKD', raw_alt_price)
                alt_numbers = re.findall(r'\d+', normalized)
                if len(alt_numbers) >= 2:
                    # Если больше двух чисел, объединяем все, кроме последнего, для old_price
                    if len(alt_numbers) > 2:
                        old_price = "".join(alt_numbers[:-1])
                        price = alt_numbers[-1]
                    else:
                        old_price = alt_numbers[0]
                        price = alt_numbers[1]

    # Извлечение основной картинки из тега, содержащего "t1066__img"
    main_image = ""
    img_tag = soup.find("img", class_=lambda v: v and "t1066__img" in v)
    if img_tag:
        main_image = img_tag.get("data-original") or img_tag.get("src") or ""

    # Создание объекта лендинга; для поля tag (теперь tag_id) передаем None
    landing_obj = Landing(
        language=language,
        course_id=None,
        title=landing_title,
        tag_id=None,
        main_image=main_image,
        duration=landing_duration,
        old_price=old_price if old_price else None,
        price=price if price else None,
        main_text=main_text
    )

    # ============================
    # 2. Извлечение модулей
    # ============================
    modules = []
    # a) Из блоков с классом "t812__pricelist-item"
    module_info_blocks = soup.select("div.t812__pricelist-item")
    modules_info = []
    if module_info_blocks:
        for block in module_info_blocks:
            title_div = block.find("div", class_="t812__pricelist-item__title")
            raw_title = title_div.get_text() if title_div else ""
            mod_title = " ".join(raw_title.split())
            price_div = block.find("div", class_="t812__pricelist-item__price")
            raw_mod_duration = price_div.get_text() if price_div else ""
            mod_duration = " ".join(raw_mod_duration.split())
            modules_info.append({"title": mod_title, "duration": mod_duration})
    else:
        # b) Если блоков t812 нет, пробуем из блоков с классом "t230"
        module_container_blocks = soup.select("div.t230")
        for block in module_container_blocks:
            title_elem = block.find("div", class_="t230__title", attrs={"field": "title"})
            if not title_elem:
                continue
            raw_title = title_elem.get_text() if title_elem else ""
            mod_title = " ".join(raw_title.split())
            modules_info.append({"title": mod_title, "duration": ""})

    # Программный текст для модулей из блоков с классом "t230__text" (field="text")
    program_text_blocks = soup.select("div.t230__text[field='text']")
    program_texts = []
    for block in program_text_blocks:
        raw_text = block.get_text(separator=" ", strip=True)
        program_text = raw_text.split("Duration:")[0].strip()
        program_texts.append(program_text)

    # Ссылки на короткие видео из блоков "t230__wrap-video"
    video_blocks = soup.select("div.t230__wrap-video div.t-video-lazyload")
    video_links = []
    for vb in video_blocks:
        if vb.has_attr("data-videolazy-id"):
            video_links.append(vb["data-videolazy-id"])
        else:
            video_links.append("")

    num_modules = min(len(modules_info), len(program_texts), len(video_links))
    for i in range(num_modules):
        mod = Module(
            section_id=None,
            title=modules_info[i]["title"],
            duration=modules_info[i]["duration"],
            program_text=program_texts[i],
            short_video_link=video_links[i],
            full_video_link=""
        )
        modules.append(mod)

    # ============================
    # 3. Создание курса и секции
    # ============================
    # Название секции совпадает с названием курса/лендинга
    course_obj = Course(
        name=landing_title,
        description=main_text
    )
    section_obj = Section(
        name=landing_title,
        course=course_obj
    )
    for mod in modules:
        mod.section = section_obj
    landing_obj.course = course_obj

    # ============================
    # 4. Извлечение авторов
    # ============================
    authors = []
    # Сначала ищем блоки типа 1 (множественные авторы) – с классом "t524__wrappercenter"
    type1_author_blocks = soup.find_all("div", class_="t524__wrappercenter")
    if type1_author_blocks:
        for block in type1_author_blocks:
            name_tag = block.find("div", class_="t524__persname")
            raw_author_name = name_tag.get_text() if name_tag else "Без имени"
            author_name = " ".join(raw_author_name.split())

            descr_tag = block.find("div", class_="t524__persdescr")
            raw_descr = descr_tag.get_text() if descr_tag else ""
            author_descr = " ".join(raw_descr.split())

            img_wrapper = block.find_previous("div", class_="t524__imgwrapper")
            author_photo = ""
            if img_wrapper:
                bgimg_div = img_wrapper.find("div", class_="t524__bgimg")
                if bgimg_div:
                    author_photo = bgimg_div.get("data-original") or ""
            authors.append(Author(
                name=author_name,
                description=author_descr,
                photo=author_photo
            ))
    else:
        # Если блоков типа 1 нет, ищем тип 2 (один автор) – блок с классом "t545"
        type2_author_block = soup.find("div", class_="t545")
        if type2_author_block:
            name_tag = type2_author_block.find("div", attrs={"field": "title"},
                                               class_=lambda v: v and "t545__title" in v)
            if name_tag:
                strong_tag = name_tag.find("strong")
                if strong_tag:
                    raw_author_name = strong_tag.get_text()
                else:
                    raw_author_name = name_tag.get_text()
            else:
                raw_author_name = "Без имени"
            author_name = " ".join(raw_author_name.split())

            descr_tag = type2_author_block.find("div", attrs={"field": "text"},
                                                class_=lambda v: v and "t545__text" in v)
            raw_descr = descr_tag.get_text() if descr_tag else ""
            author_descr = " ".join(raw_descr.split())

            img_tag = type2_author_block.find("div", class_=lambda v: v and "t545__blockimg" in v)
            author_photo = ""
            if img_tag:
                author_photo = img_tag.get("data-original") or ""
            authors.append(Author(
                name=author_name,
                description=author_descr,
                photo=author_photo
            ))
    landing_obj.authors = authors

    # ============================
    # 5. Сохранение в БД (единая транзакция)
    # ============================
    DATABASE_URL = (
        f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        with db.begin():
            existing = db.query(Landing).filter(
                Landing.title == landing_title,
                Landing.language == language
            ).first()
            if existing:
                raise Exception("Запись с таким лендингом уже существует.")

            db.add(course_obj)
            db.add(section_obj)
            for mod in modules:
                db.add(mod)
            db.add(landing_obj)
            for author in authors:
                db.add(author)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Порог схожести (от 0 до 100)
FUZZY_THRESHOLD = 74.9


def normalize_text(text: str) -> str:
    """
    Приводит строку к нижнему регистру и удаляет все символы, не являющиеся латинскими буквами или цифрами.
    Это включает удаление пробелов, тире, нижних подчёркиваний и других спецсимволов.
    """
    return re.sub(r'[^a-z0-9]', '', text.lower())


def extract_lessons_from_dump_content(content: str) -> list:
    """
    Принимает содержимое SQL-дампа (как строку) и извлекает уроки.
    Возвращает список словарей с ключами:
      - course_id, course_name, lesson_name, video_link
    """
    lessons_list = []
    logger.debug("Начало извлечения уроков из дампа.")
    record_pattern = re.compile(
        r"\(\s*(\d+)\s*,\s*'(.*?)'\s*,\s*'(.*?)'\s*,\s*'((?:\\.|[^'])*)'\s*\)",
        re.DOTALL
    )
    matches = list(record_pattern.finditer(content))
    logger.debug("Найдено %d записей в дампе.", len(matches))

    for match in matches:
        course_id = match.group(1)
        course_name = match.group(2)
        lessons_json_str = match.group(4)
        logger.debug("Обработка записи курса: id=%s, name=%s", course_id, course_name)

        try:
            unescaped = lessons_json_str.encode('utf-8').decode('unicode_escape')
            logger.debug("Unescaped JSON (первые 100 символов): %s", unescaped[:100])
        except Exception as e:
            logger.error("Ошибка при unescape JSON для курса '%s': %s", course_name, e)
            continue

        stripped = unescaped.lstrip()
        if stripped.startswith("{'"):
            logger.debug("Обнаружены одинарные кавычки, выполняется замена ключей на двойные.")
            unescaped = re.sub(r"(?<=\{|,)\s*'([^']+)'\s*:", r'"\1":', unescaped)
            logger.debug("После замены (первые 100 символов): %s", unescaped[:100])

        try:
            lessons_data = json.loads(unescaped)
            logger.debug("JSON успешно распарсен.")
        except Exception as e:
            logger.error("Ошибка парсинга JSON для курса '%s': %s", course_name, e)
            continue

        if isinstance(lessons_data, dict):
            sections = lessons_data.values()
            logger.debug("JSON имеет тип dict, секций: %d", len(lessons_data))
        elif isinstance(lessons_data, list):
            sections = lessons_data
            logger.debug("JSON имеет тип list, секций: %d", len(lessons_data))
        else:
            logger.error("Непредвиденная структура JSON для курса '%s': %s", course_name, type(lessons_data))
            continue

        for section in sections:
            lessons = section.get("lessons", [])
            logger.debug("Найдено %d уроков в секции.", len(lessons))
            for lesson in lessons:
                lesson_name = lesson.get("lesson_name")
                video_link = lesson.get("video_link")
                if lesson_name and video_link:
                    lessons_list.append({
                        "course_id": course_id,
                        "course_name": course_name,
                        "lesson_name": lesson_name,
                        "video_link": video_link
                    })
                    logger.debug("Извлечен урок: '%s' с ссылкой: %s", lesson_name, video_link)
                else:
                    logger.warning("Пропущен урок, отсутствует lesson_name или video_link.")

    logger.debug("Извлечение уроков завершено. Всего уроков: %d", len(lessons_list))
    return lessons_list


async def update_modules_from_lessons(lessons_list: list, db: AsyncSession) -> dict:
    """
    Асинхронно сравнивает lesson_name из дампа с полным значением title из таблицы Module,
    используя нечеткое сравнение после нормализации строк (приведение к нижнему регистру и удаление спецсимволов).

    Выбираются только те модули, у которых поле full_video_link пустое и лендинг с языком en.
    Если совпадение выше порога, обновляется поле full_video_link модуля.

    Для уроков, где обновление не произошло, сохраняется информация о лучшем совпадении.
    В конце список неприсвоенных уроков сортируется по best_score (по убыванию).

    Возвращает словарь с количеством обновленных записей, отсортированным списком неприсвоенных уроков
    и количеством записей, для которых обновление не произошло.
    """
    updated_count = 0
    unmatched_details = []
    logger.debug("Начало асинхронного обновления модулей в базе данных.")

    # Выбираем только модули, у которых full_video_link пустое и лендинг с языком en
    result = await db.execute(
        select(Module)
        .join(Module.section)
        .join(Section.course)
        .join(Course.landing)
        .filter(
            or_(Module.full_video_link == None, Module.full_video_link == ''),
            Landing.language == LanguageEnum.EN
        )
    )
    modules = result.scalars().all()
    logger.debug("Получено модулей из базы (пустые full_video_link и en лендинги): %d", len(modules))

    for lesson in lessons_list:
        lesson_name = lesson["lesson_name"]
        video_link = lesson["video_link"]
        logger.debug("Сопоставление урока '%s' с выбранными модулями.", lesson_name)
        best_match = None
        best_score = 0

        # Приводим lesson_name к нормализованной форме
        normalized_lesson = normalize_text(lesson_name)
        tasks = [
            asyncio.to_thread(
                fuzz.ratio,
                normalized_lesson,
                normalize_text(module.title)
            )
            for module in modules
        ]
        scores = await asyncio.gather(*tasks)
        for i, score in enumerate(scores):
            if score > best_score:
                best_score = score
                best_match = modules[i]

        logger.debug("Лучшее совпадение для '%s': %s с score %d",
                     lesson_name,
                     best_match.title if best_match else None,
                     best_score)
        if best_match and best_score >= FUZZY_THRESHOLD:
            logger.info("Обновление модуля '%s' - назначение full_video_link: %s", best_match.title, video_link)
            best_match.full_video_link = video_link
            db.add(best_match)
            updated_count += 1
        else:
            detail = {
                "lesson_name": lesson_name,
                "video_link": video_link,
                "best_match_title": best_match.title if best_match else None,
                "best_score": best_score
            }
            unmatched_details.append(detail)
            logger.warning("Не найдено подходящего совпадения для урока '%s'. Лучшее совпадение: %s с score %d",
                           lesson_name,
                           best_match.title if best_match else "Нет",
                           best_score)

    # Сортировка неприсвоенных уроков по best_score (по убыванию)
    unmatched_details = sorted(unmatched_details, key=lambda x: x["best_score"], reverse=True)

    await db.commit()
    logger.debug("Асинхронное обновление модулей завершено. Изменений сохранено в базе.")
    logger.debug("Список неприсвоенных уроков (отсортированный по best_score): %s", unmatched_details)

    not_updated_count = len(unmatched_details)
    return {
        "updated": updated_count,
        "unmatched": unmatched_details,
        "not_updated_count": not_updated_count
    }


async def process_dump_and_update_from_content(file_content: str, db: AsyncSession) -> dict:
    """
    Асинхронно обрабатывает содержимое SQL-дампа, извлекает уроки и обновляет таблицу Module.
    """
    logger.debug("Начало асинхронной обработки содержимого дампа.")
    lessons_list = extract_lessons_from_dump_content(file_content)
    logger.debug("Извлечение уроков завершено. Всего извлечено: %d", len(lessons_list))
    result = await update_modules_from_lessons(lessons_list, db)
    logger.debug("Асинхронный процесс обновления завершён. Результат: %s", result)
    return result