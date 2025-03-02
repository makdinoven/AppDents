import s from "../CourseDetail/CourseDetail.module.scss";
import EditLanding from "../EditLanding/EditLanding.tsx";
import { LandingType } from "../../types.ts";
import DetailHeader from "../DetailHeader/DetailHeader.tsx";
import DetailBottom from "../DetailBottom/DetailBottom.tsx";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Trans } from "react-i18next";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import EditLesson from "../EditLesson/EditLesson.tsx";
import Loader from "../../../../components/ui/Loader/Loader.tsx";

const initialLanding: LandingType = {
  id: 1,
  title: "TEST",
  old_price: 0,
  price: 0,
  main_image: "",
  main_text: "",
  language: "en",
  tag_id: 1,
  authors: [],
  sales_count: 0,
};

const initialLessons = [
  {
    id: 1,
    video_link: "https://play.boomstream.com/2TVBV98F",
    lesson_name: "Introducing Invisalign® System",
  },
  {
    id: 2,
    video_link: "https://play.boomstream.com/Pe80MGMv",
    lesson_name:
      "How to fill an Invisalign® prescription: Enhancing communication and predictability",
  },
];

const LandingDetail = () => {
  const { landingId } = useParams();
  // const [loading, setLoading] = useState<boolean>(false);
  const [landing, setLanding] = useState<any | null>(null);
  const [lessons, setLessons] = useState<any | null>(null);
  const handleSave = () => {};

  useEffect(() => {
    if (landingId) {
      // fetchCourseData();
      setLanding(initialLanding);
      setLessons(initialLessons);
      // setLoading(false);
    }
  }, [landingId]);

  const handleDeleteLanding = () => {
    console.log("delete Landing");
  };

  return (
    <div className={s.detail_container}>
      <DetailHeader title={"admin.landings.edit"} />
      {!landing ? (
        <Loader />
      ) : (
        <>
          <EditLanding landing={landing} setLanding={setLanding} />
          <div className={s.list}>
            <div className={s.list_header}>
              <h2>
                <Trans i18nKey={"admin.lessons"} />
              </h2>
              <PrettyButton
                variant={"primary"}
                text={t("admin.lessons.add")}
                onClick={() => console.log("add lesson")}
              />
            </div>
            {lessons.length > 0 ? (
              lessons.map((lesson: any, index: number) => (
                <EditLesson
                  type={"landing"}
                  key={index}
                  lesson={lesson}
                  setCourse={setLanding}
                  handleDelete={() => console.log("delete lesson")}
                />
              ))
            ) : (
              <div>
                <Trans i18nKey={"admin.sections.noLessons"} />
              </div>
            )}
          </div>

          <DetailBottom
            deleteLabel={"admin.courses.delete"}
            handleSave={handleSave}
            handleDelete={() => handleDeleteLanding()}
          />
        </>
      )}
    </div>
  );
};
export default LandingDetail;
