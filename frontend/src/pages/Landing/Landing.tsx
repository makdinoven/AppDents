import s from "./Landing.module.scss";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import {
  calculateDiscount,
  getPricesData,
  keepFirstTwoWithInsert,
  normalizeLessons,
} from "../../common/helpers/helpers.ts";
import Loader from "../../components/ui/Loader/Loader.tsx";
import LandingHero from "./modules/LandingHero/LandingHero.tsx";
import { t } from "i18next";
import About from "./modules/About/About.tsx";
import CourseProgram from "./modules/CourseProgram/CourseProgram.tsx";
import LessonsProgram from "./modules/LessonsProgram/LessonsProgram.tsx";
import Professors from "./modules/Professors/Professors.tsx";
import Offer from "./modules/Offer/Offer.tsx";
import { Trans } from "react-i18next";
import ModalWrapper from "../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import PaymentModal from "../../components/Modals/PaymentModal/PaymentModal.tsx";
import ArrowButton from "../../components/ui/ArrowButton/ArrowButton.tsx";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { Path } from "../../routes/routes.ts";
import { BASE_URL } from "../../common/helpers/commonConstants.ts";
import { setLanguage } from "../../store/slices/userSlice.ts";
import CoursesSection from "../../components/CommonComponents/CoursesSection/CoursesSection.tsx";
import FormattedAuthorsDesc from "../../common/helpers/FormattedAuthorsDesc.tsx";
import PrettyButton from "../../components/ui/PrettyButton/PrettyButton.tsx";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import Faq from "./modules/Faq/Faq.tsx";
import {
  closeModal,
  openModal,
  setLessonsCount,
  setPrices,
} from "../../store/slices/landingSlice.ts";
import { getCourses } from "../../store/actions/userActions.ts";
import VideoSection from "./modules/VideoSection/VideoSection.tsx";

const Landing = () => {
  const [landing, setLanding] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const { landingPath } = useParams();
  const formattedAuthorsDesc = (
    <FormattedAuthorsDesc authors={landing?.authors} />
  );
  const navigate = useNavigate();
  const location = useLocation();
  const currentUrl = window.location.origin + location.pathname;
  const dispatch = useDispatch<AppDispatchType>();
  const { role, isLogged, courses } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const isModalOpen = useSelector(
    (state: AppRootStateType) => state.landing.isModalOpen,
  );
  const [isModalFree, setIsModalFree] = useState(false);
  const isPromotionLanding =
    location.pathname.includes(Path.landing) &&
    !location.pathname.includes(Path.landingClient);

  const isFromFacebook = useMemo(() => {
    const searchParams = new URLSearchParams(location.search);
    return searchParams.has("fbclid") || isPromotionLanding;
  }, [location.search]);
  const isAdmin = role === "admin";

  const basePath = location.pathname
    .replace(/^\/|\/$/g, "")
    .split("/")
    .slice(0, -1)
    .join("/");

  const isVideo = basePath === Path.videoLanding;
  const isClient =
    basePath === Path.landingClient || basePath === Path.freeLandingClient;
  const isFree =
    basePath === Path.freeLanding || basePath === Path.freeLandingClient;

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

  const handleOpenModal = (isModalFree?: boolean) => {
    if (isModalFree) {
      setIsModalFree(true);
    }
    dispatch(openModal());
  };

  const handleCloseModal = () => {
    dispatch(closeModal());
    setIsModalFree(false);
  };

  const fetchLandingData = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getLanding(landingPath);
      setLanding({
        ...res.data,
        lessons_info: normalizeLessons(res.data.lessons_info),
      });
      dispatch(setLanguage(res.data.language));
      dispatch(
        setPrices({
          newPrice: res.data.new_price,
          oldPrice: res.data.old_price,
        }),
      );
      dispatch(setLessonsCount({ lessonsCount: res.data.lessons_count }));
      setLoading(false);
    } catch (error) {
      console.error(error);
      setLoading(false);
    }
  };

  const trackFacebookAd = () => {
    mainApi.trackFacebookAd(landingPath!);
  };

  const renderBuyButton = (variant: "full" | "default") => {
    if (!isFree) {
      return (
        <ArrowButton onClick={() => handleOpenModal(false)}>
          <Trans
            i18nKey={
              variant === "default" ? "landing.buyFor" : "landing.buyForFull"
            }
            values={{
              ...getPricesData(landing),
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
          <ArrowButton onClick={() => handleOpenModal(false)}>
            <Trans
              i18nKey={
                variant === "default" ? "landing.buyFor" : "landing.buyForFull"
              }
              values={{
                ...getPricesData(landing),
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
            onClick={() => handleOpenModal(true)}
            text={"freeCourse.tryFirstLesson"}
          />
        </div>
      );
    }
  };

  const heroData = {
    landing_name: landing?.landing_name,
    authors: formattedAuthorsDesc,
    photo: landing?.preview_photo || null,
    renderBuyButton: renderBuyButton("default"),
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

  const courseProgramData = {
    name: landing?.landing_name,
    lessonsCount: landing?.lessons_count
      ? keepFirstTwoWithInsert(landing?.lessons_count)
      : `0 ${t("landing.onlineLessons")}`,
    program: landing?.course_program,
    lessons_names: landing?.lessons_info.map((lesson: any) => lesson.name),
    renderBuyButton: renderBuyButton("default"),
    ...getPricesData(landing),
  };

  const lessonsProgramData = {
    lessons: landing?.lessons_info,
    renderBuyButton: renderBuyButton("full"),
  };

  const offerData = {
    landing_name: landing?.landing_name,
    authors: formattedAuthorsDesc,
    renderBuyButton: renderBuyButton("default"),
  };

  const videoSectionData = {
    lessons: landing?.lessons_info,
    renderBuyButton: renderBuyButton("default"),
    about: aboutData,
    course_program: landing?.course_program,
    landing_name: landing?.landing_name,
    authors: landing?.authors,
    ...getPricesData(landing),
  };

  const paymentData = {
    from_ad: isPromotionLanding,
    landing_ids: [landing?.id],
    course_ids: landing?.course_ids,
    price_cents: landing?.new_price * 100,
    total_new_price: landing?.new_price,
    total_old_price: landing?.old_price,
    region: landing?.language,
    success_url: `${BASE_URL}${Path.successPayment}`,
    cancel_url: currentUrl,
    courses: [
      {
        name: landing?.landing_name,
        new_price: landing?.new_price,
        old_price: landing?.old_price,
      },
    ],
  };

  return (
    <>
      <div className={s.landing_top}>
        {isClient && <BackButton />}
        {isAdmin && isClient && (
          <div className={s.admin_btns}>
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

            <PrettyButton
              variant="primary"
              text={"admin.landings.edit"}
              onClick={() => navigate(`${Path.landingDetail}/${landing.id}`)}
            />
          </div>
        )}
      </div>
      {loading ? (
        <Loader />
      ) : (
        <div className={s.landing}>
          {!isVideo ? (
            <>
              <LandingHero data={heroData} />
              <About data={aboutData} />
              <CourseProgram data={courseProgramData} />
              <LessonsProgram data={lessonsProgramData} />
              <Professors data={landing?.authors} />
              <Offer data={offerData} />
            </>
          ) : (
            <>
              <VideoSection data={videoSectionData} />
            </>
          )}

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
        </div>
      )}

      {isModalOpen && (
        <ModalWrapper
          variant="dark"
          title={"yourOrder"}
          cutoutPosition="none"
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        >
          <PaymentModal
            isFree={isModalFree}
            paymentData={paymentData}
            handleCloseModal={handleCloseModal}
          />
        </ModalWrapper>
      )}
    </>
  );
};

export default Landing;
