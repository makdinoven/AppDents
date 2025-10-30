import s from "./ProfessorPage.module.scss";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import { useParams, useSearchParams } from "react-router-dom";
import { useDispatch } from "react-redux";
import { useEffect, useState } from "react";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import CardsList from "../../components/ProductsSection/CardsList/CardsList.tsx";
import SectionHeader from "../../components/ui/SectionHeader/SectionHeader.tsx";
import ProductsSection from "../../components/ProductsSection/ProductsSection.tsx";
import { useScreenWidth } from "../../common/hooks/useScreenWidth.ts";
import ExpandableText from "../../components/ui/ExpandableText/ExpandableText.tsx";
import ProfessorPageSkeleton from "../../components/ui/Skeletons/ProfessorPageSkeleton/ProfessorPageSkeleton.tsx";
import { setPaymentData } from "../../store/slices/paymentSlice.ts";
import { AppDispatchType } from "../../store/store.ts";
import { PaymentDataModeType } from "../../common/hooks/usePaymentPageHandler.ts";
import {
  PAGE_SOURCES,
  PAYMENT_MODE_KEY,
} from "../../common/helpers/commonConstants.ts";
import { CartItemType } from "../../api/cartApi/types.ts";
import SimpleBuySection from "./modules/SimpleBuySection/SimpleBuySection.tsx";
import ProfessorBuySection from "./modules/BuySection/ProfessorBuySection.tsx";

const ProfessorPage = () => {
  const [searchParams] = useSearchParams();
  const dispatch = useDispatch<AppDispatchType>();
  const paymentModalMode = searchParams.get(PAYMENT_MODE_KEY);
  const { professorId } = useParams();
  const [professor, setProfessor] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const screenWidth = useScreenWidth();

  useEffect(() => {
    fetchProfessorData();
  }, [professorId]);

  const fetchProfessorData = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getProfessorDetail(Number(professorId));
      setProfessor(res.data);
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    if (professor && paymentModalMode) {
      setPaymentDataCustom(paymentModalMode as PaymentDataModeType);
    }
  }, [professor, paymentModalMode]);

  const setPaymentDataCustom = (mode: PaymentDataModeType) => {
    const transformedCourses = professor.landings.map(
      (l: any): CartItemType => ({
        item_type: "LANDING",
        data: {
          id: l.id,
          landing_name: l.landing_name,
          authors: l.authors,
          page_name: l.slug,
          old_price: Number(l.old_price),
          new_price: Number(l.new_price),
          preview_photo: l.main_image,
          course_ids: l.course_ids,
          lessons_count: l.lessons_count,
        },
      }),
    );

    const transformedBooks = professor.book_landings.map(
      (b: any): CartItemType => ({
        item_type: "BOOK",
        data: {
          id: b.id,
          landing_name: b.landing_name,
          authors: b?.authors,
          page_name: b.slug,
          old_price: b?.old_price,
          new_price: b?.new_price,
          preview_photo: b.main_image,
          book_ids: b.book_ids,
        },
      }),
    );

    let paymentItems;
    const data = {
      landing_ids: [],
      book_landing_ids: [],
      course_ids: [],
      book_ids: [],
      price_cents: 0,
      new_price: 0,
      old_price: 0,
      source: PAGE_SOURCES.professor,
      from_ad: false,
    };

    const {
      course_ids,
      landing_ids,
      total_new_price,
      total_old_price,
      book_ids,
      book_landing_ids,
      total_books_price,
      total_books_old_price,
      total_courses_books_old_price,
      total_courses_books_price,
    } = professor;

    switch (mode) {
      case "COURSES":
        data.course_ids = course_ids;
        data.landing_ids = landing_ids;
        data.price_cents = total_new_price * 100;
        data.new_price = total_new_price;
        data.old_price = total_old_price;
        paymentItems = transformedCourses;
        break;
      case "BOOKS":
        data.book_ids = book_ids;
        data.book_landing_ids = book_landing_ids;
        data.price_cents = total_books_price * 100;
        data.new_price = total_books_price;
        data.old_price = total_books_old_price;
        paymentItems = transformedBooks;
        break;
      case "BOTH":
        data.book_ids = book_ids;
        data.book_landing_ids = book_landing_ids;
        data.price_cents = total_courses_books_price * 100;
        data.new_price = total_courses_books_price;
        data.old_price = total_courses_books_old_price;
        paymentItems = [...transformedBooks, ...transformedCourses];
        break;
    }

    dispatch(
      setPaymentData({
        data,
        render: {
          new_price: data.new_price,
          old_price: data.old_price,
          items: paymentItems,
        },
      }),
    );
  };

  return (
    <>
      <BackButton />

      <div className={s.professor_page}>
        {loading || !professor ? (
          <ProfessorPageSkeleton />
        ) : (
          <>
            <section className={s.professor_hero}>
              {screenWidth < 577 && (
                <h1 className={s.professor_name}>{professor.name}</h1>
              )}
              <div className={s.professor_info}>
                {screenWidth > 577 && (
                  <h1 className={s.professor_name}>{professor.name}</h1>
                )}
                <ExpandableText
                  lines={screenWidth > 577 ? 10 : 3}
                  textClassName={s.professor_description}
                  text={professor.description}
                  color={"primary"}
                />
              </div>
              {professor.photo && (
                <div className={s.card_wrapper}>
                  <div className={s.card}>
                    <div className={s.card_header}></div>
                    <div className={s.card_body}>
                      <div className={s.photo}>
                        <img src={professor.photo} alt="Professor image" />
                      </div>
                    </div>
                    <div className={s.card_bottom}></div>
                  </div>
                </div>
              )}
            </section>
          </>
        )}
        {professor && (
          <>
            {professor.landings.length > 0 &&
            professor.book_landings.length > 0 ? (
              <ProfessorBuySection
                setPaymentDataCustom={setPaymentDataCustom}
                prices={{
                  books: {
                    old: professor.total_books_old_price,
                    new: professor.total_books_price,
                  },
                  courses: {
                    old: professor.total_old_price,
                    new: professor.total_new_price,
                  },
                  both: {
                    old: professor.total_courses_books_old_price,
                    new: professor.total_courses_books_price,
                  },
                }}
              />
            ) : (
              professor.landings.length > 0 && (
                <SimpleBuySection
                  paymentMode="COURSES"
                  setPaymentDataCustom={setPaymentDataCustom}
                  new_price={professor.total_new_price}
                  old_price={professor.total_old_price}
                />
              )
            )}

            <div className={s.professor_cards}>
              <SectionHeader name={"professor.professorsCourses"} />
              <CardsList
                productCardFlags={{ isClient: true }}
                cardType={"course"}
                filter={"all"}
                loading={false}
                cards={professor.landings}
                showSeeMore={false}
                showEndOfList={false}
              />
            </div>
            {professor.landings.length > 0 && (
              <SimpleBuySection
                paymentMode={"COURSES"}
                setPaymentDataCustom={setPaymentDataCustom}
                new_price={professor.total_new_price}
                old_price={professor.total_old_price}
              />
            )}

            <div className={s.professor_cards}>
              <SectionHeader name={"professor.professorsBooks"} />
              <CardsList
                productCardFlags={{ isClient: true }}
                cardType={"book"}
                filter={"all"}
                loading={false}
                cards={professor.book_landings}
                showSeeMore={false}
                showEndOfList={false}
              />
            </div>
            {professor.book_landings.length > 0 && (
              <SimpleBuySection
                paymentMode={"BOOKS"}
                setPaymentDataCustom={setPaymentDataCustom}
                new_price={professor.total_books_price}
                old_price={professor.total_books_old_price}
              />
            )}

            <ProductsSection
              productCardFlags={{ isClient: true, isOffer: true }}
              showSort={true}
              sectionTitle={"other.otherCourses"}
              pageSize={6}
            />
          </>
        )}
      </div>
    </>
  );
};

export default ProfessorPage;
