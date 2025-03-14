import s from "./ProgramContent.module.scss";
import { renderProgramText } from "../../../../../../common/helpers/renderProgramText.tsx";

const ProgramContent = ({
  programData,
  textClassName,
  listClassName,
}: {
  programData: any;
  textClassName: string;
  listClassName: string;
}) => {
  return (
    <div className={s.program_content}>
      {renderProgramText(
        programData,
        textClassName,
        listClassName,
        s.list_item,
      )}
    </div>
  );
};

export default ProgramContent;
