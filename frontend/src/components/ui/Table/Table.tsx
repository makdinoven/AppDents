import s from "./Table.module.scss";
import { Path } from "../../../routes/routes.ts";
import { formatIsoToLocalDatetime } from "../../../common/helpers/helpers.tsx";

interface TableProps<T extends Record<string, any>> {
  title?: string;
  data: T[];
  columnLabels?: Partial<Record<keyof T, string>>;
}

const Table = <T extends Record<string, any>>({
  title,
  data,
  columnLabels = {},
}: TableProps<T>) => {
  if (!data || data.length === 0) return <div className={s.empty}>No data</div>;

  const excludedKeys = [
    "slug",
    "landing_slug",
    "inviter_id",
    "referral_id",
    "course_id",
    "user_id",
  ];
  const headers = Object.keys(data[0]).filter(
    (key) => !excludedKeys.includes(key),
  );

  const renderCell = (key: string, value: any, row: T) => {
    if (key === "landing_name") {
      const slug = row.slug || row.landing_slug;
      return (
        <a
          href={`/${Path.landingClient}/${slug}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          {value}
        </a>
      );
    }

    if (
      key === "email" ||
      key === "inviter_email" ||
      key === "referral_email"
    ) {
      const id =
        key === "email" || key === "inviter_email"
          ? row.inviter_id
            ? row.inviter_id
            : row.user_id
          : row.referral_id;

      return (
        <a
          href={`${Path.userDetail}/${id}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          {value}
        </a>
      );
    }

    if (key === "registered_at" || key === "created_at" || key === "paid_at") {
      return formatIsoToLocalDatetime(value);
    }

    if (typeof value === "boolean") {
      return value ? (
        <span className="highlight">Yes</span>
      ) : (
        <span className="error">No</span>
      );
    }

    return value;
  };

  return (
    <>
      {title && <h4 className={s.table_title}>{title}</h4>}
      <div className={s.table_wrapper}>
        <table className={s.table}>
          <thead>
            <tr>
              <th>#</th>
              {headers.map((key) => (
                <th key={key}>{columnLabels[key as keyof T] || key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIdx) => (
              <tr key={rowIdx}>
                <td>{rowIdx + 1}</td>
                {headers.map((key) => (
                  <td key={key}>{renderCell(key, row[key], row)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default Table;
