import s from "./Landing.module.scss";
import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import {
  capitalizeText,
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

const Landing = () => {
  const [landing, setLanding] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const { landingPath } = useParams();

  useEffect(() => {
    fetchLandingData();
  }, [landingPath]);

  useEffect(() => {
    console.log(landing);
  }, [landing]);

  const fetchLandingData = async () => {
    try {
      const res = await mainApi.getLanding(landingPath);
      setLanding({
        ...res.data,
        lessons_info: normalizeLessons(res.data.lessons_info),
      });
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  const heroData = {
    landing_name: landing?.landing_name,
    authors:
      landing?.authors.length > 0
        ? `By ${
            landing?.authors
              ?.slice(0, 3)
              .map((author: any) => capitalizeText(author.name))
              .join(", ") + (landing?.authors.length > 3 ? ` ${t("etAl")}` : "")
          }`
        : null,
    old_price: landing?.old_price,
    new_price: landing?.new_price,
    photo: landing?.preview_photo,
  };

  const discountPercentage = Math.round(
    ((landing?.old_price - landing?.new_price) / landing?.old_price) * 100,
  );

  const aboutData = {
    lessonsCount: `${landing?.lessons_info.length} ${t("landing.lessons")}`,
    professorsCount: `${landing?.authors.length} ${t("landing.professors")}`,
    discount: `${discountPercentage}% ${t("landing.discount")}`,
    savings: `$${landing?.old_price - landing?.new_price} ${t("landing.savings")}`,
    access: t("landing.access"),
  };

  const courseProgramData = {
    name: landing?.landing_name,
    lessonsCount: `${landing?.lessons_info.length} ${t("landing.onlineLessons")}`,
    program: landing?.course_program,
    lessons_names: landing?.lessons_info.map(
      (lesson: any, index: number) => `${++index}. ${lesson.name}`,
    ),

    old_price: landing?.old_price,
    new_price: landing?.new_price,
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
          <LessonsProgram data={landing?.lessons_info} />
          <Professors data={landing?.professors} />
          <section className={s.offer}></section>
        </div>
      )}
    </>
  );
};

export default Landing;
