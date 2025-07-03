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
import Table from "../../../components/ui/Table/Table.tsx";
import { Alert } from "../../../components/ui/Alert/Alert.tsx";
import { ErrorIcon } from "../../../assets/icons";
import PrettyButton from "../../../components/ui/PrettyButton/PrettyButton.tsx";
import { Trans } from "react-i18next";

const UserDetail = () => {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<UserType | null>(null);
  const [amountToAdd, setAmountToAdd] = useState<number>(0);
  const [balance, setBalance] = useState<number>(0);
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
        adminApi.getCoursesList({ size: 100000 }),
      ]);
      setUser(userRes.data);
      setCourses(coursesRes.data.items);
      setBalance(Number(userRes.data.balance));
      setLoading(false);
    } catch (error: any) {
      Alert(
        `Error fetching user data, error message: ${error.message}`,
        <ErrorIcon />
      );
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
      await adminApi.updateUser(userId, user);
      navigate(-1);
    } catch (error) {
      console.error("Error updating user:", error);
    }
  };

  const handleChangeBalance = async () => {
    const amount = Number(amountToAdd);
    if (isNaN(amount) || amount === 0) return;

    const data = {
      user_id: Number(userId),
      amount,
      meta: { reason: "bonus" },
    };

    try {
      await adminApi.changeUserBalance(data);
      setBalance(Number(balance) + amount);
      setAmountToAdd(0);
      alert(`Successfully updated user balance`);
    } catch {
      alert(`Error updating user`);
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
            {!!user?.purchases.length && (
              <Table
                data={user.purchases}
                columnLabels={{
                  id: "ID",
                  course_id: "Course ID",
                  landing_name: "Landing",
                  created_at: "Date",
                  from_ad: "Ad",
                  amount: "Amount",
                }}
              />
            )}

            <p>
              <Trans
                i18nKey={"admin.users.balance"}
                values={{ balance: balance }}
              />
            </p>

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
              <div className={s.input_button_wrapper}>
                <AdminField
                  inputType="number"
                  type="input"
                  id="balance"
                  placeholder={t("admin.users.balance.placeholder")}
                  label={t("admin.users.balance.add")}
                  value={amountToAdd}
                  onChange={(e: any) => setAmountToAdd(e.value)}
                />
                <PrettyButton
                  onClick={handleChangeBalance}
                  text={"admin.users.changeBalance"}
                />
              </div>
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
