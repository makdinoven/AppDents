import s from "../Landing/Landing.module.scss";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import Faq from "../Landing/modules/Faq/Faq.tsx";
import BookLandingHero from "./modules/BookLandingHero/BookLandingHero.tsx";
import ContentOverview from "./modules/ContentOverview/ContentOverview.tsx";
import AudioSection from "./modules/Audio/AudioSection.tsx";
import BuySection from "../../components/CommonComponents/BuySection/BuySection.tsx";
import { FORMATS } from "../../common/helpers/commonConstants.ts";
import Professors from "./modules/Professors/Professors.tsx";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";

const BookLanding = () => {
  const [data, setData] = useState<any>([]);
  const [loading] = useState(false);
  const landingPath = useParams();
  useEffect(() => {
    fetch(
      `http://test.dent-s.com/api/books/landing/slug/zero-bone-loss-concepts-book`,
    )
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        setData(data);
      })
      .catch((error) => {
        console.error("There was a problem with the fetch operation:", error);
      });
  }, [landingPath]);

  return (
    <>
      <div className={s.landing_top}>
        <BackButton />
      </div>
      <div className={s.landing} id="portal_parent">
        <BookLandingHero data={data} loading={loading} />
        <ContentOverview books={data.books} portalParentId="portal_parent" />
        <BuySection
          type="download"
          isFullWidth={true}
          oldPrice={data.old_price}
          newPrice={data.new_price}
          formats={FORMATS}
        />
        <AudioSection audioUrl="" title="NYSORA Nerve Block Manual" />
        <Professors professors={data.authors} />
        <Faq type={"book"} />
      </div>
    </>
  );
};

export default BookLanding;
