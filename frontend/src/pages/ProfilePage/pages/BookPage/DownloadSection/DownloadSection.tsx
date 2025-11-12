import React, { useState } from "react";
import s from "./DownloadSection.module.scss";
import { Trans } from "react-i18next";

type FormatType = { file_format: string; download_url: string };

interface DownloadSectionProps {
  formats: FormatType[];
}

const DownloadSection: React.FC<DownloadSectionProps> = ({
  formats,
}: DownloadSectionProps) => {
  const [activeFormat, setActiveFormat] = useState<FormatType>(formats?.[0]);

  const handleFormatChange = (format: FormatType) => {
    setActiveFormat(format);
  };

  return (
    <div className={s.section_wrapper}>
      <section className={s.section}>
        <p className={s.text}>
          <Trans
            i18nKey={"bookLanding.chooseFormat"}
            components={[<span className={s.highlight} />]}
          />
        </p>
        <a
          href={activeFormat.download_url}
          target="_blank"
          rel="noopener"
          className={s.button}
        >
          <Trans i18nKey="bookLanding.download" /> {activeFormat.file_format}
        </a>
        <ul className={s.format_buttons}>
          {formats?.map((format: FormatType) => {
            return (
              <li key={format.file_format}>
                <button
                  onClick={() => handleFormatChange(format)}
                  className={activeFormat === format ? s.active : ""}
                >
                  {format.file_format}
                </button>
              </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
};

export default DownloadSection;
