import s from "./ProgramContent.module.scss";
import CircleArrow from "../../../../../../common/Icons/CircleArrow.tsx";
import { processProgramText } from "../../../../../../common/helpers/helpers.ts";

const ProgramContent = ({
  programData,
  textClassName,
  listClassName,
}: {
  programData: any;
  textClassName: string;
  listClassName: string;
}) => {
  const { regularLines, bulletPointGroups } = processProgramText(programData);

  return (
    <div className={s.program_content}>
      <div className={textClassName}>
        {regularLines.map((line, index) => (
          <p key={index}>{line}</p>
        ))}
      </div>
      {bulletPointGroups.length > 0 && (
        <ul className={listClassName}>
          {bulletPointGroups.map((group, index) => (
            <li className={s.list_item} key={index}>
              <span>
                <CircleArrow />
              </span>
              <div>
                {group.text}
                {group.points.length > 0 && (
                  <ul>
                    {group.points.map((point, idx) => (
                      <li key={idx}>{point}</li>
                    ))}
                  </ul>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ProgramContent;
