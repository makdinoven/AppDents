import { useRef, useState } from "react";
import s from "./Faq.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Trans } from "react-i18next";
import BackArrow from "../../../../assets/Icons/BackArrow.tsx";

const Faq = ({ type = "course" }: { type: "course" | "book" }) => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const answerRefs = useRef<(HTMLDivElement | null)[]>([]);

  const faqItemsCourse = [
    { question: "1_question", answer: { text: "1_answer", links: [""] } },
    { question: "2_question", answer: { text: "2_answer", links: [""] } },
    { question: "3_question", answer: { text: "3_answer", links: [""] } },
    { question: "4_question", answer: { text: "4_answer", links: [""] } },
    { question: "5_question", answer: { text: "5_answer", links: [""] } },
    { question: "6_question", answer: { text: "6_answer", links: [""] } },
    { question: "7_question", answer: { text: "7_answer", links: [""] } },
    {
      question: "8_question",
      answer: { text: "8_answer", links: ["https://dent-s.com/"] },
    },
    {
      question: "9_question",
      answer: {
        text: "9_answer",
        links: [
          "https://dent-s.com/password-reset",
          "https://dent-s.com/login",
        ],
      },
    },
  ];

  const faqItemsBook = [
    {
      question: "1_question_book",
      answer: { text: "1_answer_book", links: [""] },
    },
    {
      question: "2_question_book",
      answer: { text: "2_answer_book", links: [""] },
    },
    { question: "3_question", answer: { text: "3_answer", links: [""] } },
    { question: "4_question", answer: { text: "4_answer", links: [""] } },
    { question: "6_question", answer: { text: "6_answer", links: [""] } },
    {
      question: "8_question",
      answer: { text: "8_answer", links: ["https://dent-s.com/"] },
    },
    {
      question: "9_question",
      answer: {
        text: "9_answer",
        links: [
          "https://dent-s.com/password-reset",
          "https://dent-s.com/login",
        ],
      },
    },
  ];

  const items = type === "course" ? faqItemsCourse : faqItemsBook;

  const toggleItem = (index: number) => {
    setOpenIndex((prevIndex) => (prevIndex === index ? null : index));
  };

  return (
    <section id="course-faq" className={s.faq_container}>
      <SectionHeader name="landing.faq.faq" />

      <ul className={s.faq_list}>
        {items.map((item, index) => (
          <li
            key={index}
            className={`${s.faq_item} ${openIndex === index ? s.opened : ""}`}
          >
            <button
              type="button"
              className={s.faq_question_button}
              onClick={() => toggleItem(index)}
            >
              <div className={s.faq_question}>
                <span className={s.question_number}>{index + 1}.</span>
                <Trans i18nKey={`landing.faq.${item.question}`} />
              </div>
              <BackArrow />
            </button>
            <div
              ref={(el) => {
                answerRefs.current[index] = el;
              }}
              className={s.faq_answer_wrapper}
              style={{
                maxHeight:
                  openIndex === index
                    ? `${answerRefs.current[index]?.scrollHeight}px`
                    : "0px",
              }}
            >
              <div className={s.faq_answer}>
                <Trans
                  i18nKey={`landing.faq.${item.answer.text}`}
                  components={{
                    link1: (
                      <a
                        href={item.answer.links[0]}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={s.faq_link}
                      />
                    ),
                    link2: (
                      <a
                        href={item.answer.links[1]}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={s.faq_link}
                      />
                    ),
                  }}
                />
              </div>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
};

export default Faq;
