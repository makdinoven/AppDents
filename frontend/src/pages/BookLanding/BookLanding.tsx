import s from "../Landing/Landing.module.scss";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import Faq from "../Landing/modules/Faq/Faq.tsx";

const BookLanding = () => {
  return (
    <>
      <div className={s.landing_top}>
        <BackButton />
      </div>

      <div className={s.landing}>
        <Faq type={"book"} />
      </div>
    </>
  );
};

export default BookLanding;
