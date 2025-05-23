import s from "./Footer.module.scss";
import { Trans } from "react-i18next";
import { Link } from "react-router-dom";
import { t } from "i18next";
import { Path } from "../../routes/routes";
import { NAV_BUTTONS } from "../../common/helpers/commonConstants.ts";
import NavButton from "../Header/modules/NavButton/NavButton.tsx";

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
          link: `${Path.termsOfUse}`,
        },
        {
          type: "item",
          name: <Trans i18nKey={"footer.privacy"} />,
          link: `${Path.privacyPolicy}`,
        },
        {
          type: "item",
          name: <Trans i18nKey={"footer.cookie"} />,
          link: `${Path.cookiePolicy}`,
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
      <div className={s.footer_container}>
        <div className={s.content}>
          {footerSections.map((section) => renderFooterSection(section))}

          <nav className={s.nav_buttons}>
            {NAV_BUTTONS.map((btn) => (
              <NavButton
                key={btn.text}
                appearance={"footer"}
                icon={btn.icon}
                text={btn.text}
                link={btn.link}
              />
            ))}
          </nav>
        </div>
        <p className={s.copyright}>
          <Trans i18nKey={"footer.copyright"} />
        </p>
      </div>
    </footer>
  );
};

export default Footer;
