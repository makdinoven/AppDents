import s from "./ProfessorPage.module.scss";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import { useParams, useSearchParams } from "react-router-dom";
import { useDispatch } from "react-redux";
import { useEffect, useState } from "react";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import CardsList from "../../components/ProductsSection/CardsList/CardsList.tsx";
import SectionHeader from "../../components/ui/SectionHeader/SectionHeader.tsx";
import ProductsSection from "../../components/ProductsSection/ProductsSection.tsx";
import { Trans } from "react-i18next";
import ArrowButton from "../../components/ui/ArrowButton/ArrowButton.tsx";
import { Clock } from "../../assets/icons/index.ts";
import { useScreenWidth } from "../../common/hooks/useScreenWidth.ts";
import ExpandableText from "../../components/ui/ExpandableText/ExpandableText.tsx";
import ProfessorPageSkeleton from "../../components/ui/Skeletons/ProfessorPageSkeleton/ProfessorPageSkeleton.tsx";
import { setPaymentData } from "../../store/slices/paymentSlice.ts";
import { AppDispatchType } from "../../store/store.ts";
import {
  PaymentDataModeType,
  usePaymentPageHandler,
} from "../../common/hooks/usePaymentPageHandler.ts";
import {
  PAGE_SOURCES,
  PAYMENT_MODE_KEY,
} from "../../common/helpers/commonConstants.ts";
import { CartItemType } from "../../api/cartApi/types.ts";

const ProfessorPage = () => {
  const { openPaymentModal } = usePaymentPageHandler();
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

    const transformedBooks = professor.books.map(
      (b: any): CartItemType => ({
        item_type: "BOOK",
        data: {
          id: b.id,
          landing_name: b.title,
          authors: b?.authors, //TODO настоящих авторов запихнуть когда будет бэк
          page_name: b.slug,
          old_price: b?.old_price, //TODO настоящую цену запихнуть когда будет бэк
          new_price: b?.new_price, //TODO настоящую цену запихнуть когда будет бэк
          preview_photo: b.cover_url,
          book_ids: [b.id],
        },
      }),
    );

    let paymentItems;

    switch (mode) {
      case "COURSES":
        paymentItems = transformedCourses;
        break;
      case "BOOKS":
        paymentItems = transformedBooks;
        break;
      case "BOTH":
        paymentItems = [...transformedBooks, ...transformedCourses];
        break;
    }

    dispatch(
      setPaymentData({
        data: {
          landing_ids: professor.landings.map((l: { id: number }) => l.id),
          book_landing_ids: professor.books.map((b: { id: number }) => b.id),
          course_ids: professor.course_ids,
          book_ids: professor.book_ids ? professor.book_ids : [],
          price_cents: professor.total_new_price * 100,
          new_price: professor.total_new_price,
          old_price: professor.total_old_price,
          source: PAGE_SOURCES.professor,
          from_ad: false,
        },
        render: {
          new_price: professor.total_new_price,
          old_price: professor.total_old_price,
          items: paymentItems,
        },
      }),
    );
  };

  const handleOpenModal = (paymentDataMode: PaymentDataModeType) => {
    setPaymentDataCustom(paymentDataMode);
    openPaymentModal(undefined, undefined, paymentDataMode);
  };

  const renderBuySection = (paymentDataMode: PaymentDataModeType) => {
    if (professor.landings.length <= 0) return null;
    return (
      <section className={s.buy_section}>
        <div className={s.professor_access}>
          <Clock />
          <p>
            <Trans i18nKey="professor.accessToAllCourses" />
          </p>
        </div>
        <p className={s.buy_section_desc}>
          <Trans
            i18nKey="professor.youCanBuyAllCourses"
            values={{
              new_price: professor.total_new_price,
              old_price: professor.total_old_price,
            }}
            components={{
              1: <span className="highlight" />,
              2: <span className="crossed" />,
            }}
          />
        </p>
        <ArrowButton onClick={() => handleOpenModal(paymentDataMode)}>
          <Trans
            i18nKey={"professor.getAllCourses"}
            values={{
              new_price: professor.total_new_price,
            }}
            components={{
              1: <span className="highlight" />,
            }}
          />
        </ArrowButton>
      </section>
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
            {renderBuySection("COURSES")}
          </>
        )}
        {professor && (
          <>
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
            {renderBuySection("COURSES")}

            {renderBuySection("BOOKS")}

            {renderBuySection("BOTH")}
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
