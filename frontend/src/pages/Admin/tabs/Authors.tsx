import { useEffect, useState } from "react";
// import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import PanelItem from "../modules/common/PanelItem/PanelItem.tsx";
import s from "../AdminPanel/AdminPanel.module.scss";
import Search from "../../../components/ui/Search/Search.tsx";
import { Path } from "../../../routes/routes.ts";
import { useSearch } from "../../../common/hooks/useSearch.ts";
import Loader from "../../../components/ui/Loader/Loader.tsx";
import PrettyButton from "../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import { Trans } from "react-i18next";

interface AuthorType {
  email: string;
  id: number;
}

const Authors = () => {
  const [authors, setAuthors] = useState<AuthorType[]>([]);
  const {
    searchQuery,
    setSearchQuery,
    filteredItems: filteredAuthors,
  } = useSearch(authors, ["email"]);

  useEffect(() => {
    fetchAuthors();
  }, []);

  const fetchAuthors = async () => {
    try {
      // const res = await adminApi.getAuthors();
      // const sortedAuthors = res.data.sort((a: any, b: any) => b.id - a.id);
      // setAuthors(sortedAuthors);

      setAuthors([
        { email: "TEST author", id: 1111 },
        {
          email: "TEST author 2",
          id: 11121,
        },
      ]);
    } catch (error) {
      console.error("Error fetching authors:", error);
    }
  };

  const addAuthor = () => {};

  return (
    <div className={s.list}>
      <div className={s.list_header}>
        <Search
          placeholder={t("admin.authors.search")}
          value={searchQuery}
          onChange={(e: any) => setSearchQuery(e.target.value)}
        />

        <PrettyButton text={t("admin.authors.create")} onClick={addAuthor} />
      </div>
      {!authors || !authors.length ? (
        <Loader />
      ) : (
        <>
          {filteredAuthors.length > 0 ? (
            filteredAuthors.map((author: { id: number; email: string }) => (
              <PanelItem
                name={author.email}
                key={author.id}
                link={`${Path.authorDetail}/${author.id}`}
              />
            ))
          ) : (
            <Trans i18nKey={"admin.authors.notFound"} />
          )}
        </>
      )}
    </div>
  );
};

export default Authors;
