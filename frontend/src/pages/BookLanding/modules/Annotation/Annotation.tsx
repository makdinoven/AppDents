import s from "./Annotation.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import ExpandableText from "../../../../components/ui/ExpandableText/ExpandableText.tsx";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";

const Annotation = ({ text }: { text: string }) => {
  const screenWidth = useScreenWidth();

  return (
    <section className={s.annotation}>
      <SectionHeader name={"bookLanding.annotation"} />
      <ExpandableText
        textClassName={s.annotation_text}
        lines={screenWidth > 577 ? 10 : 6}
        text={text}
        color={"primary"}
      />
    </section>
  );
};

export default Annotation;
