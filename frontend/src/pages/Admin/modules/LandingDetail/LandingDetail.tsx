import s from "../CourseDetail/CourseDetail.module.scss";
import EditLanding from "../EditLanding/EditLanding.tsx";
import DetailHeader from "../common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../common/DetailBottom/DetailBottom.tsx";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Trans } from "react-i18next";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import EditLesson from "../EditLesson/EditLesson.tsx";
import Loader from "../../../../components/ui/Loader/Loader.tsx";

const initialLanding = {
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
  lessons: [
    {
      id: 1,
      program_text: "",
      short_link: "",
      duration: "",
      lesson_name: "Introducing Invisalign® System",
    },
    {
      id: 2,
      program_text: "",
      short_link: "",
      duration: "",
      lesson_name: "Introducing Invisalign® System 2",
    },
  ],
};

const LandingDetail = () => {
  const { landingId } = useParams();
  // const [loading, setLoading] = useState<boolean>(false);
  const [landing, setLanding] = useState<any | null>(null);
  const handleSave = () => {};

  useEffect(() => {
    if (landingId) {
      // fetchCourseData();
      setLanding(initialLanding);
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
            {landing.lessons.length > 0 ? (
              landing.lessons.map((lesson: any, index: number) => (
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
