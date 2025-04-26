import s from "./Footer.module.scss";
import { Trans } from "react-i18next";
import { Link } from "react-router-dom";
import { t } from "i18next";

type FooterItem = {
  type: string;
  link?: string;
  isExternal?: boolean;
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
        {
          type: "item",
          name: <Trans i18nKey={"footer.contacts.address"} />,
          link: `https://www.google.com/maps?q=${t("footer.contacts.address")}`,
          isExternal: true,
        },
        {
          type: "item",
          name: <Trans i18nKey={"footer.contacts.phoneNumber"} />,
          link: `tel:${t("footer.contacts.phoneNumber")}`,
        },
        {
          type: "item",
          name: <Trans i18nKey={"footer.contacts.email"} />,
          link: `mailto:${t("footer.contacts.email")}`,
        },
      ],
    },
    {
      name: "polities",
      list: [
        { type: "title", name: <Trans i18nKey={"footer.polities"} /> },
        {
          type: "item",
          name: <Trans i18nKey={"footer.terms"} />,
          link: "http://project11845297.tilda.ws/page60744947.html",
          isExternal: true,
        },
        {
          type: "item",
          name: <Trans i18nKey={"footer.privacy"} />,
          link: "https://project11845297.tilda.ws/page60745015.html",
          isExternal: true,
        },
        {
          type: "item",
          name: <Trans i18nKey={"footer.cookie"} />,
          link: "http://project11845297.tilda.ws/page60744983.html",
          isExternal: true,
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
              {item?.link ? (
                item?.isExternal ? (
                  <a href={item.link} target="_blank" rel="noopener noreferrer">
                    {item.name}
                  </a>
                ) : (
                  <Link to={item.link}>{item.name}</Link>
                )
              ) : (
                item.name
              )}
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
      {/*<div className={s.logo}>*/}
      {/*  <DentsLogo />*/}
      {/*</div>*/}
    </footer>
  );
};

export default Footer;
