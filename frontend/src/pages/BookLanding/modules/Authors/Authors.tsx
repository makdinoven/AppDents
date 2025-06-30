import s from "./Authors.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";

const Authors = () => {
  return (
    <section id={"book-authors"} className={s.authors}>
      <SectionHeader name={"bookLanding.aboutAuthor"} />
    </section>
  );
};

export default Authors;
