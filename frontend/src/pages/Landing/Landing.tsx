import s from "./Landing.module.scss";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import {
  calculateDiscount,
  getBasePath,
  getPaymentType,
  getPricesData,
  keepFirstTwoWithInsert,
  normalizeLessons,
} from "../../common/helpers/helpers.ts";
import LandingHero from "./modules/LandingHero/LandingHero.tsx";
import { t } from "i18next";
import About from "./modules/About/About.tsx";
import CourseProgram from "./modules/CourseProgram/CourseProgram.tsx";
import LessonsProgram from "./modules/LessonsProgram/LessonsProgram.tsx";
import Professors from "./modules/Professors/Professors.tsx";
import Offer from "./modules/Offer/Offer.tsx";
import { Trans } from "react-i18next";
import ArrowButton from "../../components/ui/ArrowButton/ArrowButton.tsx";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { Path } from "../../routes/routes.ts";
import {
  BASE_URL,
  PAGE_SOURCES,
} from "../../common/helpers/commonConstants.ts";
import { setLanguage } from "../../store/slices/userSlice.ts";
import CoursesSection from "../../components/CommonComponents/CoursesSection/CoursesSection.tsx";
import FormattedAuthorsDesc from "../../common/helpers/FormattedAuthorsDesc.tsx";
import PrettyButton from "../../components/ui/PrettyButton/PrettyButton.tsx";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import Faq from "./modules/Faq/Faq.tsx";
import { getCourses } from "../../store/actions/userActions.ts";
import VideoSection from "./modules/VideoSection/VideoSection.tsx";
import {
  initLowPricePixel,
  trackLowPricePageView,
} from "../../common/helpers/facebookPixel.ts";
import { setPaymentData } from "../../store/slices/paymentSlice.ts";
import { usePaymentPageHandler } from "../../common/hooks/usePaymentPageHandler.ts";

const Landing = () => {
  const { openPaymentModal } = usePaymentPageHandler();
  const [landing, setLanding] = useState<any | null>(null);
  const [firstLesson, setFirstLesson] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const { landingPath } = useParams();
  const formattedAuthorsDesc = (
    <FormattedAuthorsDesc authors={landing?.authors} />
  );
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch<AppDispatchType>();
  const { role, isLogged, courses } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const isPromotionLanding =
    location.pathname.includes(Path.landing) &&
    !location.pathname.includes(Path.landingClient);

  const isFromFacebook = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.has("fbclid") || isPromotionLanding;
  }, [location.search]);
  const isAdmin = role === "admin";
  const basePath = getBasePath(location.pathname);

  const isVideo = basePath === Path.videoLanding;
  const isClient =
    basePath === Path.landingClient || basePath === Path.freeLandingClient;
  const isFree =
    basePath === Path.freeLanding || basePath === Path.freeLandingClient;
  const isWebinar = basePath === Path.webinarLanding;

  useEffect(() => {
    if (isLogged && isFree && !isAdmin) {
      dispatch(getCourses());
    }
  }, [isLogged]);

  useEffect(() => {
    if (courses.length > 0 && isFree && !isAdmin) {
      navigate(
        isClient
          ? `/${Path.landingClient}/${landingPath}`
          : `${Path.landing}/${landingPath}`,
      );
    }
  }, [courses]);

  useEffect(() => {
    if (isFromFacebook) {
      trackFacebookAd();
    }
    fetchLandingData();
  }, [landingPath]);

  const fetchLandingData = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getLanding(landingPath);
      setLanding({
        ...res.data,
        lessons_info: normalizeLessons(res.data.lessons_info),
      });
      dispatch(setLanguage(res.data.language));
      mainApi.trackLandingVisit(res.data.id, isPromotionLanding);
      const paymentData = {
        fromAd: isPromotionLanding,
        landingIds: [res.data.id],
        courseIds: res.data.course_ids,
        priceCents: !isWebinar ? res.data.new_price * 100 : 100,
        newPrice: !isWebinar ? res.data.new_price : 1,
        oldPrice: !isWebinar ? res.data.old_price : 49,
        region: res.data.language,
        source: isWebinar
          ? PAGE_SOURCES.webinarLanding
          : isVideo
            ? PAGE_SOURCES.videoLanding
            : undefined,
        courses: [
          {
            name: !isWebinar
              ? res.data.landing_name
              : normalizeLessons(res.data.lessons_info)[0].name,
            newPrice: !isWebinar ? res.data.new_price : 1,
            oldPrice: !isWebinar ? res.data.old_price : 49,
            lessonsCount: res.data.lessons_count,
            img: res.data.preview_photo,
          },
        ],
      };

      dispatch(setPaymentData(paymentData));
      setLoading(false);
    } catch (error) {
      console.error(error);
      setLoading(false);
    }
  };

  const trackFacebookAd = () => {
    mainApi.trackFacebookAd(landingPath!);
  };

  const handleNavigateToPayment = (isButtonFree: boolean) => {
    if (landing) {
      openPaymentModal(
        landing.page_name,
        getPaymentType(isButtonFree, undefined, isWebinar),
      );
    }
  };

  const renderBuyButton = (variant: "full" | "default") => {
    if (!isFree) {
      return (
        <ArrowButton onClick={() => handleNavigateToPayment(false)}>
          <Trans
            i18nKey={
              variant === "default" ? "landing.buyFor" : "landing.buyForFull"
            }
            values={{
              ...getPricesData(landing, isWebinar),
            }}
            components={{
              1: <span className="crossed-15" />,
              2: <span className="highlight" />,
            }}
          />
        </ArrowButton>
      );
    } else {
      return (
        <div className={s.buy_and_free_btns}>
          <ArrowButton onClick={() => handleNavigateToPayment(false)}>
            <Trans
              i18nKey={
                variant === "default" ? "landing.buyFor" : "landing.buyForFull"
              }
              values={{
                ...getPricesData(landing, isWebinar),
              }}
              components={{
                1: <span className="crossed-15" />,
                2: <span className="highlight" />,
              }}
            />
          </ArrowButton>
          <span className={s.or}>
            <Trans i18nKey={"or"} />
          </span>
          <PrettyButton
            className={s.free_btn}
            variant={"primary"}
            onClick={() => handleNavigateToPayment(true)}
            text={"freeCourse.tryFirstLesson"}
          />
        </div>
      );
    }
  };

  useEffect(() => {
    if (landing) {
      setFirstLesson(landing?.lessons_info[0]);

      const price = Number(landing?.new_price);
      if (price < 2 || isWebinar) {
        initLowPricePixel();
        trackLowPricePageView();
      }
    }
  }, [landing]);

  const heroData = {
    landing_name: !isWebinar ? landing?.landing_name : firstLesson?.name,
    authors: formattedAuthorsDesc,
    photo: !isWebinar ? landing?.preview_photo || null : firstLesson?.preview,
    renderBuyButton: renderBuyButton("default"),
    isWebinar: isWebinar,
  };

  const aboutData = {
    lessonsCount: landing?.lessons_count
      ? landing.lessons_count
      : `0 ${t("landing.lessons", { count: landing?.lessons_count })}`,
    professorsCount: `${landing?.authors.length} ${t("landing.professors", { count: landing?.authors.length })}`,
    discount: t("landing.discount", {
      count: calculateDiscount(landing?.old_price, landing?.new_price),
    }),
    savings: `$${landing?.old_price - landing?.new_price} ${t("landing.savings")}`,
    access: t("landing.access"),
    duration: `${t("landing.duration")} ${landing?.duration ? landing?.duration : "0"}`,
  };

  const aboutDataWebinar = {
    discount: t("landing.discount", {
      count: calculateDiscount(49, 1),
    }),
    access: t("landing.access"),
    duration: `${t("landing.duration")} ${firstLesson?.duration ? firstLesson?.duration : "0"}`,
  };

  const courseProgramData = {
    name: landing?.landing_name,
    lessonsCount: landing?.lessons_count
      ? keepFirstTwoWithInsert(landing?.lessons_count)
      : `0 ${t("landing.onlineLessons")}`,
    program: landing?.course_program,
    lessons_names: landing?.lessons_info.map((lesson: any) => lesson.name),
    renderBuyButton: renderBuyButton("default"),
    ...getPricesData(landing, isWebinar),
  };

  const lessonsProgramData = {
    lessons: !isWebinar
      ? landing?.lessons_info
      : landing?.lessons_info.slice(0, 1),
    renderBuyButton: renderBuyButton(isWebinar ? "default" : "full"),
    isWebinar: isWebinar,
  };

  const offerData = {
    landing_name: !isWebinar ? landing?.landing_name : firstLesson?.name,
    authors: formattedAuthorsDesc,
    renderBuyButton: renderBuyButton("default"),
    isWebinar: isWebinar,
  };

  const videoSectionData = {
    lessons: landing?.lessons_info,
    renderBuyButton: renderBuyButton("default"),
    about: aboutData,
    course_program: landing?.course_program,
    landing_name: landing?.landing_name,
    authors: landing?.authors,
    handleNavigateToPayment: () => handleNavigateToPayment(false),
    ...getPricesData(landing, isWebinar),
  };

  return (
    <>
      <div className={s.landing_top}>
        {isClient && <BackButton />}
        {isAdmin && isClient && (
          <div className={s.admin_btns}>
            <PrettyButton
              variant="primary"
              text={"admin.landings.edit"}
              onClick={() => navigate(`${Path.landingDetail}/${landing.id}`)}
            />
            <a
              href={`${BASE_URL}${Path.landing}/${landingPath}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <PrettyButton variant="default" text={"promo link"} />
            </a>
            <a
              href={`${BASE_URL}/${Path.videoLanding}/${landingPath}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <PrettyButton variant="default" text={"video link"} />
            </a>
            <a
              href={`${BASE_URL}/${Path.freeLanding}/${landingPath}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <PrettyButton variant="default" text={"promo free link"} />
            </a>
            <a
              href={`${BASE_URL}/${Path.webinarLanding}/${landingPath}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <PrettyButton variant="default" text={"webinar link"} />
            </a>
          </div>
        )}
      </div>
      <div lang={landing?.language.toLowerCase()} className={s.landing}>
        {!isVideo ? (
          <>
            <LandingHero data={heroData} loading={loading} />
            {!loading && (
              <>
                <About data={isWebinar ? aboutDataWebinar : aboutData} />
                {!isWebinar && <CourseProgram data={courseProgramData} />}
                <LessonsProgram data={lessonsProgramData} />
                <Professors data={landing?.authors} />
                <Offer data={offerData} />
              </>
            )}
          </>
        ) : (
          <>{!loading && <VideoSection data={videoSectionData} />}</>
        )}
        {!loading && (
          <>
            <Faq />
            <CoursesSection
              isFree={isFree}
              isOffer={true}
              isClient={isClient}
              isVideo={isVideo}
              showSort={true}
              sectionTitle={"similarCourses"}
              pageSize={4}
            />
          </>
        )}
      </div>
    </>
  );
};

export default Landing;
