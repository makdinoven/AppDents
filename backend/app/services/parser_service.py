# services/parser_service.py
import re
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models.models import Landing, Course, Section, Module, Author, LanguageEnum
from ..core.config import settings


def parse_and_save(html_content: str, language: LanguageEnum):
    soup = BeautifulSoup(html_content, 'lxml')

    # ============================
    # 1. Извлечение данных для лендинга
    # ============================
    # Заголовок лендинга: ищем блок с field="title" и классом, содержащим "t017__title"
    title_tag = soup.find("div", attrs={"field": "title", "class": lambda v: v and "t017__title" in v})
    raw_landing_title = title_tag.get_text() if title_tag else "Без названия"
    landing_title = " ".join(raw_landing_title.split())  # удаляем лишние пробелы и переносы

    # Основной текст (описание курса: содержимое блока с field="bdescr")
    bdescr_tag = soup.find(attrs={"field": "bdescr"})
    raw_main_text = bdescr_tag.get_text() if bdescr_tag else ""
    main_text = " ".join(raw_main_text.split())

    # Общая длительность курса (из элемента с field="li_title__0267814275022")
    landing_duration = ""
    duration_tag = soup.find(attrs={"field": "li_title__0267814275022"})
    if duration_tag:
        raw_duration_text = duration_tag.get_text()
        landing_duration = " ".join(raw_duration_text.split())
        m = re.search(r'Duration:\s*(.+)', landing_duration)
        if m:
            landing_duration = m.group(1).strip()
        else:
            landing_duration = ""

    # Извлечение цен из блока с классом t185__text и field="text"
    price = ""
    old_price = ""
    price_info_tag = soup.find("div", class_="t185__text", attrs={"field": "text"})
    if price_info_tag:
        raw_price_text = price_info_tag.get_text()
        price_text = " ".join(raw_price_text.split())
        numbers = re.findall(r'\d+', price_text)
        if len(numbers) >= 2:
            price = numbers[0]  # новая цена
            old_price = numbers[1]  # старая цена

    # Извлечение основной картинки (из тега <img> с классом, содержащим t1066__img)
    main_image = ""
    img_tag = soup.find("img", class_=lambda v: v and "t1066__img" in v)
    if img_tag:
        main_image = img_tag.get("data-original") or img_tag.get("src") or ""

    landing_obj = Landing(
        language=language,
        course_id=None,
        title=landing_title,
        tag="",
        main_image=main_image,
        duration=landing_duration,
        old_price=old_price if old_price else None,
        price=price if price else None,
        main_text=main_text,
        # Если в вашей модели нет поля slug, его не передаем!
    )

    # ============================
    # 2. Извлечение модулей
    # ============================
    # Информация о модулях извлекается в два этапа:
    # а) Из блоков с классом "t812__pricelist-item" получаем название и длительность
    module_info_blocks = soup.select("div.t812__pricelist-item")
    modules_info = []
    for block in module_info_blocks:
        title_div = block.find("div", class_="t812__pricelist-item__title")
        raw_title = title_div.get_text() if title_div else ""
        mod_title = " ".join(raw_title.split())
        price_div = block.find("div", class_="t812__pricelist-item__price")
        raw_mod_duration = price_div.get_text() if price_div else ""
        mod_duration = " ".join(raw_mod_duration.split())
        modules_info.append({"title": mod_title, "duration": mod_duration})

    # б) Из блоков с классом "t230__text" (field="text") получаем программный текст
    program_text_blocks = soup.select("div.t230__text[field='text']")
    program_texts = []
    for block in program_text_blocks:
        raw_text = block.get_text(separator=" ", strip=True)
        # Извлекаем программный текст до маркера "Duration:" (если он есть)
        program_text = raw_text.split("Duration:")[0].strip()
        program_texts.append(program_text)

    # в) Из блоков с классом "t230__wrap-video" извлекаем ссылки на короткие видео
    video_blocks = soup.select("div.t230__wrap-video div.t-video-lazyload")
    video_links = []
    for vb in video_blocks:
        if vb.has_attr("data-videolazy-id"):
            video_links.append(vb["data-videolazy-id"])
        else:
            video_links.append("")

    # Определяем количество модулей по минимальному числу найденных элементов
    num_modules = min(len(modules_info), len(program_texts), len(video_links))
    modules = []
    for i in range(num_modules):
        mod = Module(
            section_id=None,  # Привяжем ниже
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
    # Название секции будет таким же, как название курса/лендинга
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
    # Сначала пытаемся найти блоки типа 1 (множественные авторы) – с классом "t524__wrappercenter"
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
        # Если блоков типа 1 нет, пытаемся найти тип 2 (один автор) – блок с классом "t545"
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
            # Если лендинг с таким же заголовком и языком уже существует, откатываем транзакцию
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
        # Если блок with завершился без ошибок – транзакция зафиксирована
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
