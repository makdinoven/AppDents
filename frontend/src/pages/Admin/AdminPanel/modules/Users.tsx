import { useEffect, useState } from "react";
// import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import PanelItem from "./PanelItem/PanelItem.tsx";
import s from "../AdminPanel.module.scss";
import Search from "../../../../components/ui/Search/Search.tsx";
import { Path } from "../../../../routes/routes.ts";
import { useSearch } from "../../../../common/hooks/useSearch.ts";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import { Trans } from "react-i18next";

interface UserType {
  email: string;
  id: number;
}

const Users = () => {
  const [users, setUsers] = useState<UserType[]>([]);
  const {
    searchQuery,
    setSearchQuery,
    filteredItems: filteredUsers,
  } = useSearch(users, ["email"]);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      // const res = await adminApi.getUsers();
      // const sortedUsers = res.data.sort((a: any, b: any) => b.id - a.id);
      // setUsers(sortedUsers);

      setUsers([
        { email: "TEST user", id: 1111 },
        {
          email: "TEST user 2",
          id: 11121,
        },
      ]);
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  const addUser = () => {};

  return (
    <div className={s.list}>
      <div className={s.list_header}>
        <Search
          placeholder={t("admin.users.search")}
          value={searchQuery}
          onChange={(e: any) => setSearchQuery(e.target.value)}
        />

        <PrettyButton text={t("admin.users.create")} onClick={addUser} />
      </div>
      {!users || !users.length ? (
        <Loader />
      ) : (
        <>
          {filteredUsers.length > 0 ? (
            filteredUsers.map((user: { id: number; email: string }) => (
              <PanelItem
                name={user.email}
                key={user.id}
                link={`${Path.userDetail}/${user.id}`}
              />
            ))
          ) : (
            <Trans i18nKey={"admin.users.notFound"} />
          )}
        </>
      )}
    </div>
  );
};

export default Users;
