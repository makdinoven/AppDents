import s from "../Landing/Landing.module.scss";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import Faq from "../Landing/modules/Faq/Faq.tsx";
import BookLandingHero from "./modules/BookLandingHero/BookLandingHero.tsx";
import ContentOverview from "./modules/ContentOverview/ContentOverview.tsx";
import BuySection from "../../components/CommonComponents/BuySection/BuySection.tsx";
import Professors from "./modules/Professors/Professors.tsx";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { BOOK_FORMATS } from "../../common/helpers/commonConstants.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import { setLanguage } from "../../store/slices/userSlice.ts";
import { useDispatch } from "react-redux";
import ProductsSection from "../../components/ProductsSection/ProductsSection.tsx";
import { setPaymentData } from "../../store/slices/paymentSlice.ts";
import { usePaymentPageHandler } from "../../common/hooks/usePaymentPageHandler.ts";
import { LanguagesType } from "../../components/ui/LangLogo/LangLogo.tsx";
import { CartItemKind } from "../../api/cartApi/types.ts";
import { Path } from "../../routes/routes.ts";
import { getFbc, getFbp } from "../../common/helpers/helpers.ts";
import { trackPageView } from "../../common/helpers/facebookPixel.ts";

const BookLanding = () => {
  const { openPaymentModal } = usePaymentPageHandler();
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(true);
  const [bookData, setBookData] = useState<any>(null);
  const { landingPath } = useParams();
  const isPromotionLanding =
    location.pathname.includes(Path.bookLanding) &&
    !location.pathname.includes(Path.bookLandingClient);
  const isFromFacebook = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.has("fbclid") || isPromotionLanding;
  }, [location.search]);

  const trackFacebookAd = () => {
    mainApi.trackFacebookAdBook(landingPath!, getFbc(), getFbp());
    trackPageView();
  };

  const fetchLandingData = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getBookLanding(landingPath);
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
            from_ad: false,
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
    } catch (error) {
      console.error(error);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (landingPath) {
      if (isFromFacebook) {
        trackFacebookAd();
      }
      fetchLandingData();
    }
  }, [landingPath]);

  const openPayment = () => {
    openPaymentModal(landingPath, undefined, "BOOKS");
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
            <ContentOverview
              books={bookData.books}
              portalParentId="portal_parent"
            />
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

  return (
    <>
      <div className={s.landing_top}>
        <BackButton />
      </div>
      <div className={s.landing} id="portal_parent">
        {renderSections()}
        {!loading && (
          <ProductsSection
            showSort={true}
            sectionTitle={"other.otherBooks"}
            pageSize={4}
            productCardFlags={{ isClient: true, isOffer: true }}
            cardType={"book"}
          />
        )}
      </div>
    </>
  );
};

export default BookLanding;
