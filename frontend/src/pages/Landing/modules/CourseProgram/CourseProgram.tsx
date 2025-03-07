import s from "./CourseProgram.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import CircleArrow from "../../../../common/Icons/CircleArrow.tsx";
import { Trans } from "react-i18next";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";

const CourseProgram = ({ data }: { data: any }) => {
  const lines = data.program.split("\n");
  const bulletPoints: string[] = [];

  const formattedProgram = lines
    .filter((line: any) => {
      if (line.trim().startsWith("-") || line.trim().startsWith("–")) {
        bulletPoints.push(line.trim().substring(1).trim());
        return false;
      }
      return true;
    })
    .map((line: any, index: number) => <p key={index}>{line}</p>);

  return (
    <div className={s.course_program}>
      <SectionHeader name={"landing.courseProgram"} />

      <div className={s.card}>
        <div className={s.card_header}>
          <div className={s.card_header_inner}>{data.name}</div>
          <span>{data.lessonsCount}</span>
        </div>
        <div className={s.card_body}>
          <div className={s.text}>{formattedProgram}</div>
          <ul className={s.arrows_list}>
            {bulletPoints.map((point, index) => (
              <li key={index}>
                <span>
                  <CircleArrow />
                </span>
                {point}
              </li>
            ))}
          </ul>
        </div>
        <div className={s.card_bottom}>
          <div className={s.card_bottom_inner}></div>
          <ul className={s.lessons_list}>
            <div className={s.column}>
              {data.lessons_names
                .slice(0, Math.ceil(data.lessons_names.length / 2))
                .map((name: string) => (
                  <li key={name}>{name}</li>
                ))}
            </div>
            <div className={s.column}>
              {data.lessons_names
                .slice(Math.ceil(data.lessons_names.length / 2))
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
          <span>
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
          </span>
        </ArrowButton>
      </div>
    </div>
  );
};

export default CourseProgram;
