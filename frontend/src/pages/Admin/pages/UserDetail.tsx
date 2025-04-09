import s from "./DetailPage.module.scss";
import DetailHeader from "../modules/common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../modules/common/DetailBottom/DetailBottom.tsx";
import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { adminApi } from "../../../api/adminApi/adminApi.ts";
import Loader from "../../../components/ui/Loader/Loader.tsx";
import AdminField from "../modules/common/AdminField/AdminField.tsx";
import { t } from "i18next";
import { UserType } from "../types.ts";
import MultiSelect from "../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import { ROLES } from "../../../common/helpers/commonConstants.ts";

const UserDetail = () => {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<UserType | null>(null);
  const navigate = useNavigate();
  const [courses, setCourses] = useState<any>(null);
  const { userId } = useParams();

  useEffect(() => {
    if (userId) {
      fetchAllData(userId);
    }
  }, [userId]);

  const fetchAllData = async (userId: any) => {
    setLoading(true);
    try {
      const [userRes, coursesRes] = await Promise.all([
        adminApi.getUser(userId),
        adminApi.getCoursesList(),
      ]);
      setUser(userRes.data);
      setCourses(coursesRes.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data", error);
    }
  };

  const handleChange = (e: any) => {
    const { name, value } = e;
    setUser((prev: any) => {
      if (!prev) return prev;
      return { ...prev, [name]: value };
    });
  };

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete this user?`)) return;
    try {
      await adminApi.deleteUser(userId);
      navigate(-1);
    } catch (error) {
      console.error("Error deleting user:", error);
    }
  };

  const handleSave = async () => {
    try {
      console.log(user);
      await adminApi.updateUser(userId, user);
      navigate(-1);
    } catch (error) {
      console.error("Error updating author:", error);
    }
  };

  return (
    <div className={s.detail_container}>
      <DetailHeader title={"admin.users.edit"} />
      {loading ? (
        <Loader />
      ) : (
        <>
          <div className={s.list}>
            <div className={s.two_items}>
              <AdminField
                type="input"
                id="email"
                placeholder={t("admin.users.email.placeholder")}
                label={t("admin.users.email")}
                value={user?.email}
                onChange={handleChange}
              />
              <AdminField
                type="input"
                id="password"
                placeholder={t("admin.users.password.placeholder")}
                label={t("admin.users.password")}
                value={user?.password ? user?.password : ""}
                onChange={handleChange}
              />
            </div>

            <MultiSelect
              isSearchable={false}
              id={"role"}
              options={ROLES}
              placeholder={"Choose a language"}
              label={t("admin.landings.role")}
              selectedValue={user?.role ? user?.role : "user"}
              isMultiple={false}
              onChange={handleChange}
              valueKey="value"
              labelKey="label"
            />
            <MultiSelect
              id={"courses"}
              options={courses}
              placeholder={"Choose an course"}
              label={t("admin.landings.courses")}
              selectedValue={user?.courses ? user?.courses : ""}
              isMultiple={true}
              onChange={handleChange}
              valueKey="id"
              labelKey="name"
            />
          </div>

          <DetailBottom
            deleteLabel={"admin.users.delete"}
            handleSave={handleSave}
            handleDelete={handleDelete}
          />
        </>
      )}
    </div>
  );
};

export default UserDetail;
