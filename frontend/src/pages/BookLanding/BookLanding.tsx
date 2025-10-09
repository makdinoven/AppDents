import s from "../Landing/Landing.module.scss";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import Faq from "../Landing/modules/Faq/Faq.tsx";
import BookLandingHero from "./modules/BookLandingHero/BookLandingHero.tsx";
import ContentOverview from "./modules/ContentOverview/ContentOverview.tsx";
import AudioSection from "./modules/Audio/AudioSection.tsx";
import BuySection from "../../components/CommonComponents/BuySection/BuySection.tsx";
import Professors from "./modules/Professors/Professors.tsx";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { BOOK_FORMATS } from "../../common/helpers/commonConstants.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import { setLanguage } from "../../store/slices/userSlice.ts";
import { useDispatch } from "react-redux";

const BookLanding = () => {
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(true);
  const [bookData, setBookData] = useState<any>(null);
  const { landingPath } = useParams();

  const fetchLandingData = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getBookLanding(landingPath);
      setBookData(res.data);
      dispatch(setLanguage(res.data.language));
      // mainApi.trackLandingVisit(res.data.id, isPromotionLanding);
      // const paymentData = {
      //     fromAd: isPromotionLanding,
      //     landingIds: [res.data.id],
      //     courseIds: res.data.course_ids,
      //     priceCents: !isWebinar ? res.data.new_price * 100 : 100,
      //     newPrice: !isWebinar ? res.data.new_price : 1,
      //     oldPrice: !isWebinar ? res.data.old_price : 49,
      //     region: res.data.language,
      //     source: isWebinar
      //         ? PAGE_SOURCES.webinarLanding
      //         : isVideo
      //             ? PAGE_SOURCES.videoLanding
      //             : undefined,
      //     courses: [
      //         {
      //             name: !isWebinar
      //                 ? res.data.landing_name
      //                 : normalizeLessons(res.data.lessons_info)[0].name,
      //             newPrice: !isWebinar ? res.data.new_price : 1,
      //             oldPrice: !isWebinar ? res.data.old_price : 49,
      //             lessonsCount: res.data.lessons_count,
      //             img: res.data.preview_photo,
      //         },
      //     ],
      // };

      // dispatch(setPaymentData(paymentData));
      setLoading(false);
    } catch (error) {
      console.error(error);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (landingPath) {
      fetchLandingData();
    }
  }, [landingPath]);

  const renderSections = () => {
    return (
      <>
        <BookLandingHero data={bookData} loading={loading} />
        {bookData && (
          <>
            <ContentOverview
              books={bookData.books}
              portalParentId="portal_parent"
            />
            <BuySection
              type="buy"
              isFullWidth={true}
              oldPrice={bookData.old_price}
              newPrice={bookData.new_price}
              formats={BOOK_FORMATS}
            />
            <AudioSection audioUrl="" title="NYSORA Nerve Block Manual" />
            <Professors professors={bookData.authors} />
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
      </div>
    </>
  );
};

export default BookLanding;
