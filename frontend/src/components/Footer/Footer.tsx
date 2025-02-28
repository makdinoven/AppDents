import s from "./Footer.module.scss";
import { Trans } from "react-i18next";
import { Link } from "react-router-dom";

type FooterItem = {
  type: string;
  link?: string;
  name: React.ReactNode;
};

type FooterSection = {
  name: string;
  list: FooterItem[];
};

const Footer = () => {
  const footerSections = [
    {
      name: "contacts",
      list: [
        { type: "title", name: <Trans i18nKey={"footer.contacts.title"} /> },
        { type: "item", name: <Trans i18nKey={"footer.contacts.address"} /> },
        {
          type: "item",
          name: <Trans i18nKey={"footer.contacts.phoneNumber"} />,
        },
        { type: "item", name: <Trans i18nKey={"footer.contacts.email"} /> },
      ],
    },
    {
      name: "polities",
      list: [
        { type: "title", name: <Trans i18nKey={"footer.polities"} /> },
        {
          type: "item",
          name: <Trans i18nKey={"footer.terms"} />,
          link: "/terms",
        },
        {
          type: "item",
          name: <Trans i18nKey={"footer.cookie"} />,
          link: "/cookie",
        },
        {
          type: "item",
          name: <Trans i18nKey={"footer.privacy"} />,
          link: "/privacy",
        },
      ],
    },
    {
      name: "product",
      list: [
        { type: "title", name: <Trans i18nKey={"footer.product"} /> },
        { type: "item", name: <Trans i18nKey={"footer.home"} />, link: "/" },
        {
          type: "item",
          name: <Trans i18nKey={"footer.tour"} />,
          link: "/tour",
        },
        {
          type: "item",
          name: <Trans i18nKey={"footer.templates"} />,
          link: "/templates",
        },
      ],
    },
  ];

  const renderFooterSection = (section: FooterSection) => {
    return (
      <ul className={s.list} key={section.name}>
        {section.list.map((item, index: number) =>
          item.type === "title" ? (
            <li key={index} className={s.list_title}>
              {item.name}
            </li>
          ) : (
            <li key={index} className={s.list_item}>
              {item?.link ? <Link to={item.link}>{item.name}</Link> : item.name}
            </li>
          ),
        )}
      </ul>
    );
  };

  return (
    <footer className={s.footer}>
      <div className={s.content}>
        {footerSections.map((section) => renderFooterSection(section))}
      </div>
    </footer>
  );
};

export default Footer;
