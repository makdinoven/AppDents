import { useEffect, useState } from "react";
import s from "./ProfessorPageSkeleton.module.scss";

const ProfessorPageSkeleton = () => {
  const [screenWidth, setScreenWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [screenWidth]);

  const renderBuySection = () => {
    return (
      <section className={s.buy_section}>
        <div className={s.professor_access}></div>
        <p className={s.buy_section_desc}></p>
        <div className={s.buy_button}></div>
      </section>
    );
  };

  return (
    <>
      <section className={s.professor_hero}>
        {screenWidth < 577 && <h1 className={s.professor_name}></h1>}
        <div className={s.professor_info}>
          {screenWidth > 577 && <h1 className={s.professor_name}></h1>}
          <p className={s.professor_description}></p>
        </div>
        <div className={s.card_wrapper}>
          <div className={s.card}>
            <div className={s.card_header}></div>
            <div className={s.card_body}>
              <div className={s.photo}></div>
            </div>
            <div className={s.card_bottom}></div>
          </div>
        </div>
      </section>
      {renderBuySection()}
    </>
  );
};

export default ProfessorPageSkeleton;
