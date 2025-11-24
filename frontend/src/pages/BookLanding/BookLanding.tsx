import s from "../Landing/Landing.module.scss";
import BackButton from "../../shared/components/ui/BackButton/BackButton.tsx";
import Faq from "../Landing/modules/Faq/Faq.tsx";
import BookLandingHero from "./modules/BookLandingHero/BookLandingHero.tsx";
import ContentOverview from "./modules/ContentOverview/ContentOverview.tsx";
import BuySection from "../../shared/components/BuySection/BuySection.tsx";
import Professors from "./modules/Professors/Professors.tsx";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { BOOK_FORMATS } from "../../shared/common/helpers/commonConstants.ts";
import { mainApi } from "../../shared/api/mainApi/mainApi.ts";
import { setLanguage } from "../../shared/store/slices/userSlice.ts";
import { useDispatch } from "react-redux";
import ProductsSection from "../../shared/components/ProductsSection/ProductsSection.tsx";
import { setPaymentData } from "../../shared/store/slices/paymentSlice.ts";
import { usePaymentPageHandler } from "../../shared/common/hooks/usePaymentPageHandler.ts";
import { LanguagesType } from "../../shared/components/ui/LangLogo/LangLogo.tsx";
import { CartItemKind } from "../../shared/api/cartApi/types.ts";
import { getFbc, getFbp } from "../../shared/common/helpers/helpers.ts";
import {
  initFacebookPixel,
  initLanguagePixel,
  trackPageView,
} from "../../shared/common/helpers/facebookPixel.ts";
import { PATHS } from "../../app/routes/routes.ts";
import NotFoundPage from "../NotFoundPage/NotFoundPage.tsx";

const BookLanding = () => {
  const { openPaymentModal } = usePaymentPageHandler();
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(true);
  const [bookData, setBookData] = useState<any>(null);
  const { slug } = useParams();
  const [errorStatus, setErrorStatus] = useState<null | number>(null);
  const isPromotionLanding =
    location.pathname.includes(PATHS.BOOK_LANDING.clearPattern) &&
    !location.pathname.includes(PATHS.BOOK_LANDING_CLIENT.clearPattern);
  const isFromFacebook = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.has("fbclid") || isPromotionLanding;
  }, [location.search]);

  const trackFacebookAd = () => {
    mainApi.trackFacebookAdBook(slug!, getFbc(), getFbp());
    trackPageView();
  };

  useEffect(() => {
    if (isPromotionLanding) {
      if (bookData) {
        initLanguagePixel(bookData.language);
        initFacebookPixel();
      }
    }
  }, [bookData, isPromotionLanding]);

  const fetchLandingData = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getBookLanding(slug);
      setBookData(res.data);
      dispatch(setLanguage(res.data.language));
      mainApi.trackBookLandingVisit(res.data.id, isPromotionLanding);

      const {
        new_price,
        old_price,
        book_ids,
        id,
        language,
        landing_name,
        authors,
        page_name,
        books,
      } = res.data;

      dispatch(
        setPaymentData({
          data: {
            new_price,
            old_price,
            course_ids: [],
            landing_ids: [],
            book_ids,
            book_landing_ids: [id],
            price_cents: new_price * 100,
            from_ad: isPromotionLanding,
            region: language as LanguagesType,
          },
          render: {
            new_price,
            old_price,
            items: [
              {
                item_type: "BOOK" as CartItemKind,
                data: {
                  id,
                  landing_name,
                  authors,
                  page_name,
                  old_price,
                  new_price,
                  preview_photo: books?.[0]?.cover_url,
                  book_ids: book_ids,
                },
              },
            ],
          },
        }),
      );
      setLoading(false);
    } catch (e: any) {
      setErrorStatus(e.status);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (slug) {
      if (isFromFacebook) {
        trackFacebookAd();
      }
      fetchLandingData();
    }
  }, [slug]);

  const openPayment = () => {
    openPaymentModal(slug, undefined, "BOOKS");
  };

  const renderSections = () => {
    return (
      <>
        <BookLandingHero
          openPayment={openPayment}
          data={bookData}
          loading={loading}
        />
        {bookData && (
          <>
            <ContentOverview books={bookData.books} />
            <BuySection
              openPayment={openPayment}
              type="buy"
              isFullWidth={true}
              oldPrice={bookData.old_price}
              newPrice={bookData.new_price}
              formats={BOOK_FORMATS}
            />
            {/*<AudioSection audioUrl="" title="NYSORA Nerve Block Manual" />*/}
            <Professors type={"book"} professors={bookData.authors} />
            <Faq type={"book"} />
          </>
        )}
      </>
    );
  };

  return !errorStatus && errorStatus !== 404 ? (
    <>
      {!isPromotionLanding && (
        <div className={s.landing_top}>
          <BackButton />
        </div>
      )}

      <div className={s.landing} id="portal_parent">
        {renderSections()}
        {!loading && (
          <ProductsSection
            showSort={true}
            sectionTitle={"other.otherBooks"}
            pageSize={4}
            productCardFlags={{ isClient: !isPromotionLanding, isOffer: true }}
            cardType={"book"}
          />
        )}
      </div>
    </>
  ) : (
    <NotFoundPage />
  );
};

export default BookLanding;
