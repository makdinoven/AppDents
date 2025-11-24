import s from "./Tabs.module.scss";
import TabButton from "./TabButton/TabButton.tsx";
import { useSearchParams } from "react-router-dom";
import { useEffect } from "react";

const Tabs = ({
  queryKey,
  mainTab,
  tabs,
}: {
  queryKey: string;
  mainTab: string;
  tabs: any[];
}) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromParams = searchParams.get(queryKey);

  useEffect(() => {
    if (!tabFromParams) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set(queryKey, mainTab);
      setSearchParams(newParams);
    }
  }, [tabFromParams, searchParams, setSearchParams]);

  const activeTab = tabFromParams || mainTab;

  const handleSelectTab = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(queryKey, value);
    setSearchParams(newParams);
  };

  return (
    <div className={s.btns_container}>
      {tabs.map((tab, i) => (
        <TabButton
          key={i}
          text={tab.name}
          isActive={tab.value === activeTab}
          onClick={() => handleSelectTab(tab.value)}
        />
      ))}
    </div>
  );
};

export default Tabs;
