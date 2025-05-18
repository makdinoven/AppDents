import s from "./CourseProgram.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Trans } from "react-i18next";
import ProgramContent from "../LessonsProgram/modules/ProgramContent/ProgramContent.tsx";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";
import LineWrapper from "../../../../components/ui/LineWrapper/LineWrapper.tsx";

const CourseProgram = ({
  data: {
    lessons_names,
    program,
    name,
    lessonsCount,
    new_price,
    old_price,
    renderBuyButton,
  },
}: {
  data: any;
}) => {
  const screenWidth = useScreenWidth();

  const renderLessonsList = () => {
    return (
      <>
        {screenWidth > 576 ? (
          <>
            <div className={s.column}>
              {lessons_names
                .slice(0, Math.floor(lessons_names.length / 2))
                .map((name: string) => (
                  <li key={name}>{name}</li>
                ))}
            </div>
            <div className={s.column}>
              {lessons_names
                .slice(Math.floor(lessons_names.length / 2))
                .map((name: string) => (
                  <li key={name}>{name}</li>
                ))}
            </div>
          </>
        ) : (
          <div className={s.column}>
            {lessons_names.map((name: string) => (
              <li key={name}>{name}</li>
            ))}
          </div>
        )}
      </>
    );
  };

  return (
    <div id={"course-program"} className={s.course_program}>
      <div className={s.buy_course}>
        <p className={s.program_p}>
          <Trans
            i18nKey="landing.youCanBuyEntireCourse"
            values={{ new_price: new_price, old_price: old_price }}
            components={{
              1: <span className="highlight" />,
              2: <span className="highlight" />,
            }}
          />
        </p>
        {renderBuyButton}
      </div>

      <SectionHeader name={"landing.courseProgram"} />

      <div className={s.card}>
        <div className={s.card_header}>
          <div className={s.card_header_background}>
            {screenWidth >= 768 ? <h6>{name}</h6> : null}
          </div>
          <span className={s.lessons_count}>{lessonsCount}</span>
        </div>
        <div className={s.card_body}>
          {screenWidth < 768 ? <h6>{name}</h6> : null}
          <ProgramContent
            programData={program}
            textClassName={s.text}
            listClassName={s.arrows_list}
          />
        </div>
        <div className={s.card_bottom}>
          <div className={s.card_bottom_background}></div>
          <ul className={s.lessons_list}>{renderLessonsList()}</ul>
        </div>
      </div>
      <p className={s.program_p}>
        <Trans
          i18nKey="landing.youCanBuyEntireCourse"
          values={{ new_price: new_price, old_price: old_price }}
          components={{
            1: <span className="highlight" />,
            2: <span className="highlight" />,
          }}
        />
      </p>
      <LineWrapper>{renderBuyButton}</LineWrapper>
    </div>
  );
};

export default CourseProgram;
