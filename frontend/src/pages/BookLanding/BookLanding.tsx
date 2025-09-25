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
  const [data, setData] = useState<any>(null);
  const [loading] = useState(false);
  const landingPath = useParams();

  useEffect(() => {
    fetch(
      `https://test.dent-s.com/api/books/landing/slug/zero-bone-loss-concepts-book`,
    )
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        console.log(data);
        setData(data);
      })
      .catch((error) => {
        console.error("There was a problem with the fetch operation:", error);
      });
  }, [landingPath]);

  const booksM = [
    {
      id: 2,
      title: "AAAA",
      slug: "zero-bone-loss-concepts-book",
      cover_url: "https://example.com/covers/zblc.jpg",
      preview_pdf_url:
        "https://cdn.dent-s.com/books/zero-bone-loss-concepts-book/preview/preview_15p.pdf",
    },
    {
      id: 2,
      title: "Zero Bone Loss Concepts (Book)",
      slug: "zero-bone-loss-concepts-book",
      cover_url: "https://example.com/covers/zblc.jpg",
      preview_pdf_url:
        "https://cdn.dent-s.com/books/zero-bone-loss-concepts-book/preview/preview_15p.pdf",
    },
    {
      id: 2,
      title: "DDDDDDDDDDDDDDDDDDDDD",
      slug: "zero-bone-loss-concepts-book",
      cover_url: "https://example.com/covers/zblc.jpg",
      preview_pdf_url:
        "https://cdn.dent-s.com/books/zero-bone-loss-concepts-book/preview/preview_15p.pdf",
    },
  ];

  const renderSections = () => {
    if (data) {
      return (
        <>
          <BookLandingHero data={data} loading={loading} />
          <ContentOverview books={booksM} portalParentId="portal_parent" />
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
        </>
      );
    }
  };

  return (
    <>
      <div className={s.landing_top}>
        <BackButton />
      </div>
      <div className={s.landing} id="portal_parent">
        {renderSections()}
      </div>
    </>
  );
};

export default BookLanding;
