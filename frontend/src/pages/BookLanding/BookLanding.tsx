import s from "../Landing/Landing.module.scss";
import { useEffect, useState } from "react";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import LandingHero from "../Landing/modules/LandingHero/LandingHero.tsx";
import BookImg from "../../assets/BOOK_IMG.png";
import Annotation from "./modules/Annotation/Annotation.tsx";
import Pages from "./modules/Pages/Pages.tsx";
import Authors from "./modules/Authors/Authors.tsx";
import Loader from "../../components/ui/Loader/Loader.tsx";
import ArrowButton from "../../components/ui/ArrowButton/ArrowButton.tsx";
import { Trans } from "react-i18next";
import Faq from "../Landing/modules/Faq/Faq.tsx";
import CoursesSection from "../../components/CommonComponents/CoursesSection/CoursesSection.tsx";
import { useLocation } from "react-router-dom";
import { Path } from "../../routes/routes.ts";
import About from "../Landing/modules/About/About.tsx";
import { t } from "i18next";
import { calculateDiscount } from "../../common/helpers/helpers.ts";

const BookLanding = () => {
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const location = useLocation();
  const isClient = location.pathname.includes(Path.bookLandingClient);

  useEffect(() => {
    setLoading(false);
  }, []);

  const handleOpenModal = () => {
    setIsModalOpen(true);
    console.log(isModalOpen);
  };

  const renderBuyButton = () => {
    return (
      <ArrowButton onClick={() => handleOpenModal()}>
        <Trans
          i18nKey={"landing.buyFor"}
          values={{
            old_price: 19,
            new_price: 8,
          }}
          components={{
            1: <span className="crossed-15" />,
            2: <span className="highlight" />,
          }}
        />
      </ArrowButton>
    );
  };

  const heroData = {
    landing_name: "Damon 2.0 How to treat all common malocclusions",
    authors: "By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.",
    photo: BookImg,
    renderBuyButton: renderBuyButton(),
  };

  const aboutData = {
    lessonsCount: `20 ${t("landing.lessons", { count: 2 })}`,
    professorsCount: `10 ${t("landing.professors", { count: 2 })}`,
    discount: t("landing.discount", {
      count: calculateDiscount(20, 10),
    }),
    savings: `$${20 - 10} ${t("landing.savings")}`,
    access: t("landing.access"),
  };

  const pagesData = {
    renderBuyButton: renderBuyButton(),
    new_price: 10,
    old_price: 10,
  };

  const annotation =
    "This book provides a comprehensive and evidence-based overview of current advances and challenges in modern medicine. Combining clinical experience with the latest scientific research, it offers valuable insights into diagnosis, treatment, and prevention strategies across a wide range of medical fields.\n" +
    "Designed for medical professionals, researchers, and students, the book covers key topics such as patient-centered care, innovations in medical technology, public health issues, and ethical considerations in clinical practice. Each chapter is authored by leading experts and includes real-world case studies, updated guidelines, and critical reflections on future developments in healthcare.\n" +
    "Whether used as a textbook, a reference guide, or a source for professional development, this publication is an essential resource for anyone involved in the rapidly evolving landscape of global medicine.";

  return (
    <>
      <div className={s.landing_top}>
        <BackButton />
      </div>
      {loading ? (
        <Loader />
      ) : (
        <div className={s.landing}>
          <LandingHero type={"book"} data={heroData} />
          <Annotation text={annotation} />
          <About type={"book"} data={aboutData} />
          <Pages data={pagesData} />
          <Authors />
          <Faq type={"book"} />
          <CoursesSection
            isOffer={true}
            isClient={isClient}
            isBook={true}
            showSort={true}
            sectionTitle={"similarBooks"}
            pageSize={4}
          />
        </div>
      )}
    </>
  );
};

export default BookLanding;
