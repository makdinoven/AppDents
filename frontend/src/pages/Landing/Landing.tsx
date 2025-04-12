import s from "./Landing.module.scss";
import { useLocation, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import {
  calculateDiscount,
  formatAuthorsDesc,
  getPricesData,
  keepFirstTwoWithInsert,
  normalizeLessons,
} from "../../common/helpers/helpers.ts";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
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
import { getMe } from "../../store/actions/userActions.ts";
import { Path } from "../../routes/routes.ts";
import { BASE_URL } from "../../common/helpers/commonConstants.ts";
import { setLanguage } from "../../store/slices/userSlice.ts";

const Landing = () => {
  const [landing, setLanding] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const { landingPath } = useParams();
  const formattedAuthorsDesc = formatAuthorsDesc(landing?.authors);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { isLogged, email } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const location = useLocation();
  const currentUrl = window.location.origin + location.pathname;
  const dispatch = useDispatch<AppDispatchType>();
  const isFromMySite = () => {
    const referrer = document.referrer;
    if (!referrer) return false;

    try {
      const referrerUrl = new URL(referrer);
      const mySiteHost = "dent-s.com";

      return (
        referrerUrl.hostname.endsWith(mySiteHost) ||
        referrerUrl.hostname === mySiteHost
      );
    } catch (e) {
      return false;
    }
  };
  useEffect(() => {
    dispatch(getMe());
  }, [dispatch]);

  useEffect(() => {
    fetchLandingData();
  }, [landingPath]);

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const fetchLandingData = async () => {
    try {
      const res = await mainApi.getLanding(landingPath);
      setLanding({
        ...res.data,
        lessons_info: normalizeLessons(res.data.lessons_info),
      });
      dispatch(setLanguage(res.data.language));
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  const handlePayment = async (form: any) => {
    const dataToSend = {
      ...paymentData,
      user_email: isLogged ? email : form.email,
    };
    try {
      const res = await mainApi.buyCourse(dataToSend);
      const checkoutUrl = res.data.checkout_url;

      if (checkoutUrl) {
        const newTab = window.open(checkoutUrl, "_blank");

        if (!newTab || newTab.closed || typeof newTab.closed === "undefined") {
          window.location.href = checkoutUrl;
        } else {
          handleCloseModal();
        }
      } else {
        console.error("Checkout URL is missing");
      }
    } catch (error) {
      console.log(error);
    }
  };

  const renderBuyButton = (variant: "full" | "default") => (
    <ArrowButton onClick={handleOpenModal}>
      <Trans
        i18nKey={
          variant === "default" ? "landing.buyFor" : "landing.buyForFull"
        }
        values={{
          ...getPricesData(landing),
        }}
        components={{
          1: <span className="crossed" />,
          2: <span className="highlight" />,
        }}
      />
    </ArrowButton>
  );

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

  const paymentData = {
    course_ids: landing?.course_ids,
    price_cents: landing?.new_price * 100,
    region: landing?.language,
    success_url: `${BASE_URL}${Path.successPayment}`,
    cancel_url: currentUrl,
  };

  return (
    <>
      {isFromMySite() && <BackButton />}
      {loading ? (
        <Loader />
      ) : (
        <div className={s.landing}>
          <LandingHero data={heroData} />
          <About data={aboutData} />
          <CourseProgram data={courseProgramData} />
          <LessonsProgram data={lessonsProgramData} />
          <Professors data={landing?.authors} />
          <Offer data={offerData} />
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
            price={`$${landing?.new_price}`}
            courseName={landing?.landing_name}
            isLogged={isLogged}
            handlePayment={handlePayment}
          />
        </ModalWrapper>
      )}
    </>
  );
};

export default Landing;
