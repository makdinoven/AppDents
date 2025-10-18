import s from "./CartItem.module.scss";
import { TrashCan } from "../../../assets/icons/index.ts";
import ViewLink from "../../../components/ui/ViewLink/ViewLink.tsx";
import { Path } from "../../../routes/routes.ts";
import LoaderOverlay from "../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import FormattedAuthorsDesc from "../../../common/helpers/FormattedAuthorsDesc.tsx";
import {
  CartItemBookType,
  CartItemCourseType,
  CartItemKind,
} from "../../../api/cartApi/types.ts";

interface CartItemProps {
  loading?: boolean;
  language: string;
  item: CartItemCourseType | CartItemBookType;
  type: CartItemKind;
  onDelete: (value: number, type: CartItemKind) => void;
}

const CartItem = ({
  loading,
  item,
  type,
  onDelete,
  language,
}: CartItemProps) => {
  const visibleAuthors = item?.authors
    ?.slice(0, 3)
    .filter((author) => author.photo);
  const isBook = type === "BOOK";

  return (
    <li className={`${s.item} ${isBook ? s.book : ""}`}>
      {loading && <LoaderOverlay />}
      <button onClick={() => onDelete(item.id, type)} className={s.delete_btn}>
        <TrashCan />
      </button>

      <div className={s.item_middle}>
        <div
          className={`${s.img_wrapper} ${!item.preview_photo ? s.no_photo : ""} ${s[type.toLowerCase()]}`}
        >
          {item?.preview_photo && (
            <img src={item.preview_photo} alt={`${type} photo`} />
          )}
        </div>
        <div className={s.text_wrapper}>
          <h4 lang={language.toLowerCase()}>{item.landing_name}</h4>
          <div className={s.course_authors}>
            {visibleAuthors?.length > 0 && (
              <ul className={s.authors_photos_list}>
                {visibleAuthors?.map((author) => (
                  <li
                    key={author.id}
                    style={{ backgroundImage: `url("${author.photo}")` }}
                    className={s.author_photo}
                  ></li>
                ))}
              </ul>
            )}
            <p>
              <FormattedAuthorsDesc authors={item.authors} />
            </p>
          </div>
        </div>
      </div>
      <div className={s.item_bottom}>
        <ViewLink
          className={s.link}
          link={
            isBook
              ? `${Path.bookLandingClient}/${item.page_name}`
              : `${Path.landingClient}/${item.page_name}`
          }
          text={`view${type.toLowerCase() === "landing" ? "Course" : type.charAt(0).toUpperCase() + type.slice(1).toLowerCase()}`}
        />
        <div className={s.prices}>
          <span className={s.new_price}>${item.new_price}</span>
          <span className={`${s.old_price} crossed-15`}>${item.old_price}</span>
        </div>
      </div>
    </li>
  );
};

export default CartItem;
