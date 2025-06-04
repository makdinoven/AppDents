import s from "./CartItem.module.scss";
import { TrashCan } from "../../../assets/logos/index";
import ViewLink from "../../../components/ui/ViewLink/ViewLink.tsx";
import { Path } from "../../../routes/routes.ts";
import LoaderOverlay from "../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import FormattedAuthorsDesc from "../../../common/helpers/FormattedAuthorsDesc.tsx";
import { CartLandingType } from "../../../api/cartApi/types.ts";

interface CartItemProps {
  loading?: boolean;
  item: CartLandingType;
  type: string;
  onDelete: (value: number) => void;
}

const CartItem = ({ loading, item, type, onDelete }: CartItemProps) => {
  const visibleAuthors = item?.authors
    ?.slice(0, 3)
    .filter((author) => author.photo);

  return (
    <li className={s.item}>
      {loading && <LoaderOverlay />}
      <button onClick={() => onDelete(item.id)} className={s.delete_btn}>
        <TrashCan />
      </button>

      <div className={s.item_middle}>
        <div className={`${s.img_wrapper} ${s[type.toLowerCase()]}`}>
          {item?.preview_photo && (
            <img src={item.preview_photo} alt={`${type} photo`} />
          )}
        </div>
        <div className={s.text_wrapper}>
          <h4>{item.landing_name}</h4>
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
          link={`${Path.landingClient}/${item.page_name}`}
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
