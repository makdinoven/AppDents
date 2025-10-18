import React, { useState } from "react";
import s from "./BuySection.module.scss";
import { Trans, useTranslation } from "react-i18next";
import { ToothPatch } from "../../../assets";
import { Alert } from "../../ui/Alert/Alert.tsx";

interface BuySectionProps {
  type: "download" | "buy";
  formats?: string[];
  isFullWidth?: boolean;
  oldPrice?: string;
  newPrice?: string;
  downloadInfo?: (format: string) => { url: string; name: string };
  openPayment?: () => void;
}

const BuySection: React.FC<BuySectionProps> = ({
  type = "buy",
  formats,
  isFullWidth = false,
  oldPrice,
  newPrice,
  downloadInfo,
  openPayment,
}: BuySectionProps) => {
  const [activeFormat, setActiveFormat] = useState(formats?.[0] || "PDF");
  const { t } = useTranslation();

  const isBuy = type === "buy";
  const isDownload = type === "download";
  const buy = isBuy ? "buy" : "";

  const handleFormatChange = (format: string) => {
    setActiveFormat(format);
  };

  const handleDownload = async (format: string) => {
    if (!downloadInfo) {
      return;
    }
    const { url, name } = downloadInfo(format);

    if (!url || url === "#") {
      return;
    }

    try {
      const file = await fetch(url);
      const blob = await file.blob();

      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `${name}.${format.toLowerCase()}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      window.URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error("Download error: ", error);
      Alert(t("downloadError"));
    }
  };

  const onClick = isBuy ? openPayment : () => handleDownload(activeFormat);

  return (
    <div className={s.section_wrapper}>
      <section
        className={`${s.buy_section} ${isFullWidth ? s.full_width : ""} ${s[buy]}`}
      >
        {!isFullWidth && newPrice && oldPrice && (
          <div className={s.price}>
            <span className={s.new_price}>${newPrice}</span>
            <span className={s.old_price}>${oldPrice}</span>
          </div>
        )}
        <p className={`${s.buy_text} ${s[buy]}`}>
          <Trans
            i18nKey={
              isDownload ? "bookLanding.chooseFormat" : "bookLanding.buyText"
            }
            values={{ oldPrice: oldPrice, newPrice: newPrice }}
            components={[<span className={s.highlight} />]}
          />
        </p>
        <button onClick={onClick} className={`${s.buy_button} ${s[buy]}`}>
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
            {formats?.map((format: string) => {
              return (
                <li key={format}>
                  <button
                    onClick={() => handleFormatChange(format)}
                    className={`${activeFormat === format ? s.active : ""} ${isFullWidth ? s.full_width : ""}`}
                  >
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
