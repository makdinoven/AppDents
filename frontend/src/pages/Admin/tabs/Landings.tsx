import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import AdminList from "./modules/AdminList/AdminList.tsx";
import { Path } from "../../../routes/routes.ts";

// const initialLanding: LandingType = {
//   id: 1,
//   title: "TEST",
//   old_price: 0,
//   price: 0,
//   main_image: "",
//   main_text: "",
//   language: "en",
//   tag_id: 1,
//   authors: [],
//   sales_count: 0,
// };

const landings = [
  {
    id: 1,
    title: "TEST LANDING",
    old_price: 0,
    price: 0,
    main_image: "",
    main_text: "",
    language: "en",
    tag_id: 1,
    authors: [],
    sales_count: 0,
  },
  {
    id: 2,
    title: "TEST LANDING 2",
    old_price: 0,
    price: 0,
    main_image: "",
    main_text: "",
    language: "en",
    tag_id: 1,
    authors: [],
    sales_count: 0,
  },
];

const Landings = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  // const courses = useSelector((state: AppRootStateType) => state.admin.courses);
  // const dispatch = useDispatch<AppDispatchType>();

  return (
    <>
      <AdminList<any>
        items={landings}
        searchField="name"
        itemName="title"
        itemLink={(landing) => `${Path.landingDetail}/${landing.id}`}
        loading={loading}
        onFetch={() => console.log("fetch")}
        onCreate={() => console.log("create course")}
        searchPlaceholder="admin.landings.search"
        createButtonText="admin.landings.create"
        notFoundText="admin.landings.notFound"
      />
    </>
  );
};

export default Landings;
