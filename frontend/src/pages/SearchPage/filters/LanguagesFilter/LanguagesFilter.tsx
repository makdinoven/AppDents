import s from "./LanguagesFilter.module.scss";
import { LANGUAGES } from "../../../../shared/common/helpers/commonConstants.ts";
import LangLogo, {
  LanguagesType,
} from "../../../../shared/components/ui/LangLogo/LangLogo.tsx";
import { useLocation, useSearchParams } from "react-router-dom";

const LanguagesFilter = ({
  selectedLanguages,
  loading,
  urlKey,
}: {
  selectedLanguages: LanguagesType[];
  loading: boolean;
  urlKey: string;
}) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();

  const handleClick = (lang: LanguagesType) => {
    let newValue: LanguagesType[];
    if (selectedLanguages.includes(lang)) {
      if (selectedLanguages.length > 1) {
        newValue = selectedLanguages.filter((l) => l !== lang);
      } else {
        newValue = selectedLanguages;
      }
    } else {
      newValue = [...selectedLanguages, lang];
    }
    searchParams.delete(urlKey);
    newValue.forEach((l) => searchParams.append(urlKey, l));
    setSearchParams(searchParams, {
      replace: true,
      ...(location.state?.backgroundLocation
        ? { state: { backgroundLocation: location.state.backgroundLocation } }
        : {}),
    });
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
