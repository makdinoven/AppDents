import s from "./CourseProgram.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Trans } from "react-i18next";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";
import ProgramContent from "../LessonsProgram/modules/ProgramContent/ProgramContent.tsx";

const CourseProgram = ({ data }: { data: any }) => {
  return (
    <div className={s.course_program}>
      <SectionHeader name={"landing.courseProgram"} />

      <div className={s.card}>
        <div className={s.card_header}>
          <div className={s.card_header_background}>{data.name}</div>
          <span>{data.lessonsCount}</span>
        </div>
        <div className={s.card_body}>
          <ProgramContent
            programData={data.program}
            textClassName={s.text}
            listClassName={s.arrows_list}
          />
        </div>
        <div className={s.card_bottom}>
          <div className={s.card_bottom_background}></div>
          <ul className={s.lessons_list}>
            <div className={s.column}>
              {data.lessons_names
                .slice(0, Math.floor(data.lessons_names.length / 2))
                .map((name: string) => (
                  <li key={name}>{name}</li>
                ))}
            </div>
            <div className={s.column}>
              {data.lessons_names
                .slice(Math.floor(data.lessons_names.length / 2))
                .map((name: string) => (
                  <li key={name}>{name}</li>
                ))}
            </div>
          </ul>
        </div>
      </div>
      <p className={s.program_p}>
        <Trans
          i18nKey="landing.youCanBuyEntireCourse"
          values={{ new_price: data.new_price, old_price: data.old_price }}
          components={{
            1: <span className="highlight" />,
            2: <span className="highlight" />,
          }}
        />
      </p>
      <div className={s.btn_wrapper}>
        <ArrowButton>
          <Trans
            i18nKey="landing.buyFor"
            values={{
              new_price: data.new_price,
              old_price: data.old_price,
            }}
            components={{
              1: <span className="crossed" />,
              2: <span className="highlight" />,
            }}
          />
        </ArrowButton>
      </div>
    </div>
  );
};

export default CourseProgram;
