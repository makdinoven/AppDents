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
import { Trans, useTranslation } from "react-i18next";
import ModalWrapper from "../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import PaymentModal from "../../components/Modals/PaymentModal.tsx";
import ArrowButton from "../../components/ui/ArrowButton/ArrowButton.tsx";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { getMe } from "../../store/actions/userActions.ts";

const Landing = () => {
  const { i18n } = useTranslation();
  const [landing, setLanding] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const { landingPath } = useParams();
  const formattedAuthorsDesc = formatAuthorsDesc(landing?.authors);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const changeLanguage = (lang: string) => {
    i18n.changeLanguage(lang);
  };
  const { isLogged, email } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const location = useLocation();
  const currentUrl = window.location.origin + location.pathname;
  const dispatch = useDispatch<AppDispatchType>();

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
      changeLanguage(res.data.language.toLowerCase());
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
          alert(
            "The opening of the tab is blocked. The link will open in this tab.",
          );
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

  const renderBuyButton = () => (
    <ArrowButton onClick={handleOpenModal}>
      <Trans
        i18nKey="landing.buyFor"
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
    renderBuyButton: renderBuyButton(),
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
    renderBuyButton: renderBuyButton(),
    ...getPricesData(landing),
  };

  const lessonsProgramData = {
    lessons: landing?.lessons_info,
    renderBuyButton: renderBuyButton(),
  };

  const offerData = {
    landing_name: landing?.landing_name,
    authors: formattedAuthorsDesc,
    renderBuyButton: renderBuyButton(),
  };

  const paymentData = {
    course_ids: landing?.course_ids,
    price_cents: landing?.new_price * 100,
    region: landing?.language,
    success_url: currentUrl,
    cancel_url: currentUrl,
  };

  return (
    <>
      <BackButton />
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
          title={`${t("buy")}: ${landing?.landing_name}`}
          cutoutPosition="none"
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        >
          <PaymentModal isLogged={isLogged} handlePayment={handlePayment} />
        </ModalWrapper>
      )}
    </>
  );
};

export default Landing;
