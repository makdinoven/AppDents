import s from "./LanguagesFilter.module.scss";
import { LANGUAGES } from "../../../../shared/common/helpers/commonConstants.ts";
import LangLogo, {
  LanguagesType,
} from "../../../../shared/components/ui/LangLogo/LangLogo.tsx";

const LanguagesFilter = ({
  selectedLanguages,
  loading,
  onChange,
}: {
  selectedLanguages: LanguagesType[];
  loading: boolean;
  urlKey?: string;
  onChange: (langs: LanguagesType[]) => void;
}) => {
  const handleClick = (lang: LanguagesType) => {
    let newValue: LanguagesType[];

    if (selectedLanguages.includes(lang)) {
      if (selectedLanguages.length > 1) {
        // не даём выключить последний язык
        newValue = selectedLanguages.filter((l) => l !== lang);
      } else {
        newValue = selectedLanguages;
      }
    } else {
      newValue = [...selectedLanguages, lang];
    }

    onChange(newValue);
  };

  return (
    <ul className={s.languages_list}>
      {LANGUAGES.map((lang) => (
        <li key={lang.value}>
          <LangLogo
            isChecked={selectedLanguages.includes(lang.value as LanguagesType)}
            isHoverable={!loading}
            className={s.lang_logo}
            lang={lang.value as LanguagesType}
            onClick={() => !loading && handleClick(lang.value as LanguagesType)}
          />
        </li>
      ))}
    </ul>
  );
};

export default LanguagesFilter;
