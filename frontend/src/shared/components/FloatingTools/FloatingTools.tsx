import s from "./FloatingTools.module.scss";
import { useScroll } from "../../common/hooks/useScroll.ts";
import ScrollToTopButton from "./modules/ScrollToTopButton/ScrollToTopButton.tsx";
import SurveyWidget from "./modules/SurveyWidget/SurveyWidget.tsx";
import { userApi } from "../../api/userApi/userApi.ts";
import { useEffect, useState } from "react";
import { SurveyType } from "./types.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";

const FloatingTools = () => {
  const isScrolled = useScroll(1200);
  const [surveys, setSurveys] = useState<SurveyType[]>([]);
  const [currentSurveyIndex, setCurrentSurveyIndex] = useState(0);
  const currentSurvey = surveys[currentSurveyIndex];
  const { isLogged } = useSelector((state: AppRootStateType) => state.user);

  useEffect(() => {
    const handleFetchSurveys = async () => {
      try {
        const res = await userApi.getSurveys();

        const surveysResult = res.data.surveys.map(
          (survey: { slug: string; title_key: string }) => ({
            slug: survey.slug,
            titleKey: survey.title_key,
          }),
        );
        setSurveys(surveysResult);
        console.log(surveysResult);
      } catch (error) {
        console.error("Error fetching surveys", error);
      }
    };

    handleFetchSurveys();
  }, []);

  return (
    <div className={s.floating_tools}>
      <div className={s.content}>
        <ScrollToTopButton isVisible={isScrolled} />
        {isLogged && currentSurvey && (
          <SurveyWidget
            survey={currentSurvey}
            onComplete={() => setCurrentSurveyIndex((i) => i + 1)}
            isScrolled={isScrolled}
          />
        )}
      </div>
    </div>
  );
};
export default FloatingTools;
