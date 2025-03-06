import s from "./Landing.module.scss";
import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import { normalizeLessons } from "../../common/helpers/helpers.ts";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import Title from "../../components/CommonComponents/Title/Title.tsx";
import { Trans } from "react-i18next";
import Loader from "../../components/ui/Loader/Loader.tsx";

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
  return (
    <>
      <BackButton />
      {loading ? (
        <Loader />
      ) : (
        <div className={s.landing}>
          <section className={s.hero}>
            <div className={s.card}>
              <div className={s.card_header}></div>
              <div className={s.card_body}></div>
              <div className={s.card_bottom}></div>
            </div>
            <Title>
              <Trans i18nKey={"onlineCourse"} />
            </Title>
          </section>
          <section className={s.about}></section>
          <section className={s.program}></section>
          <section className={s.lessons}></section>
          <section className={s.professors}></section>
          <section className={s.offer}></section>
        </div>
      )}
    </>
  );
};

export default Landing;
