import React, { useState } from "react";
import s from "./BuySection.module.scss";
import { Trans, useTranslation } from "react-i18next";
import { ToothPatch } from "../../../assets";

interface BuySectionProps {
  type: "download" | "buy";
  formats: string[];
  isFullWidth?: boolean;
  oldPrice: string;
  newPrice: string;
}

const BuySection: React.FC<BuySectionProps> = ({
  type = "buy",
  formats,
  isFullWidth = false,
  oldPrice,
  newPrice,
}: BuySectionProps) => {
  const [activeFormat, setActiveFormat] = useState(formats[0]);
  const { t } = useTranslation();

  const isBuy = type === "buy";
  const isDownload = type === "download";
  const buy = isBuy ? "buy" : "";

  const handleFormatChange = (format: string) => {
    setActiveFormat(format);
  };

  return (
    <div className={s.section_wrapper}>
      <section
        className={`${s.buy_section} ${isFullWidth ? s.full_width : ""} ${s[buy]}`}
      >
        <p
          className={`${s.buy_text}  ${isFullWidth ? s.full_width : ""} ${s[buy]}`}
        >
          <Trans
            i18nKey={
              isDownload ? "bookLanding.chooseFormat" : "bookLanding.buyText"
            }
            values={{ oldPrice: oldPrice, newPrice: newPrice }}
            components={[<span className={s.highlight} />]}
          />
        </p>
        <button className={`${s.buy_button} ${s[buy]}`} onClick={() => {}}>
          {isDownload ? (
            <p>
              {t("bookLanding.download")}
              <span style={{ marginLeft: "10px" }}>{activeFormat}</span>
            </p>
          ) : (
            <p className={s.prices}>
              {t("buyFor")} <span className={s.old_price}>${oldPrice}</span>
              <span className={s.new_price}>${newPrice}</span>
            </p>
          )}
        </button>
        {isDownload && (
          <ul className={s.format_buttons}>
            {formats.map((format: string) => {
              return (
                <li
                  key={format}
                  className={`${activeFormat === format ? s.active : ""}  ${isFullWidth ? s.full_width : ""}`}
                >
                  <button onClick={() => handleFormatChange(format)}>
                    {format}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>
      {isFullWidth && <ToothPatch className={s.tooth} />}
    </div>
  );
};

export default BuySection;
