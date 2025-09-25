import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../../store/store.ts";
import { useDispatch, useSelector } from "react-redux";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import { toggleBookLandingVisibility } from "../../../../../store/slices/adminSlice.ts";
import { ParamsType } from "../../../../../api/adminApi/types.ts";
import AdminList from "../../../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../../../routes/routes.ts";
import { generateId } from "../../../../../common/helpers/helpers.ts";
import {
  createBookLanding,
  getBookLandings,
  searchBookLandings,
} from "../../../../../store/actions/adminActions.ts";

const INITIAL_BOOK_LANDING = {
  landing_name: `New book landing ${generateId()}`,
  is_hidden: true,
  page_name: `book-${generateId()}`,
};

const AdminBookLandingsList = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const bookLandings = useSelector(
    (state: AppRootStateType) => state.admin.bookLandings,
  );
  const dispatch = useDispatch<AppDispatchType>();

  const handleToggleBookVisibility = (id: number, isHidden: boolean) => {
    try {
      adminApi.toggleBookLandingVisibility(id, isHidden);
      dispatch(toggleBookLandingVisibility({ id, isHidden }));
    } catch (error) {
      dispatch(toggleBookLandingVisibility({ id, isHidden: !isHidden }));
      console.log(error);
    }
  };

  const loadData = (params: ParamsType) => {
    if (params.q) {
      dispatch(searchBookLandings(params));
    } else {
      dispatch(getBookLandings(params));
    }
  };

  return (
    <>
      <AdminList<any>
        data={bookLandings}
        itemName={"landing_name"}
        itemLink={(book) => `${Path.bookLandingDetail}/${book.id}`}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createBookLanding(INITIAL_BOOK_LANDING))}
        showToggle={true}
        showLanguageFilter={true}
        handleToggle={(id: number, isHidden: boolean) =>
          handleToggleBookVisibility(id, isHidden)
        }
      />
    </>
  );
};

export default AdminBookLandingsList;
