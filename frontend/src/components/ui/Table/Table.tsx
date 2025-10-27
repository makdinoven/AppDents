import s from "./Table.module.scss";
import { Path } from "../../../routes/routes.ts";
import { formatIsoToLocalDatetime } from "../../../common/helpers/helpers.ts";
import LoaderOverlay from "../LoaderOverlay/LoaderOverlay.tsx";

interface TableProps<T extends Record<string, any>> {
  loading?: boolean;
  title?: string;
  data: T[];
  columnLabels?: Partial<Record<keyof T, string>>;
  landingLinkByIdPath?: string;
  structured?: boolean;
  showIndex?: boolean; // 👈 новый проп
}

const Table = <T extends Record<string, any>>({
  loading,
  title,
  data,
  columnLabels = {},
  landingLinkByIdPath,
  structured = true,
  showIndex = true, // 👈 по умолчанию нумерация включена
}: TableProps<T>) => {
  if (!data || data.length === 0) return <div className={s.empty}>No data</div>;

  const excludedKeys = [
    "slug",
    "landing_slug",
    "inviter_id",
    "referral_id",
    "course_id",
    "user_id",
    "color",
  ];

  const colors = new Map([
    [0, s.green],
    [1, `${s.green} ${s.pale}`],
    [2, s.blue],
    [3, `${s.blue} ${s.pale}`],
    [4, s.purple],
    [5, `${s.purple} ${s.pale}`],
  ]);

  const headers = Object.keys(data[0]).filter(
    (key) => !excludedKeys.includes(key),
  );

  const renderCell = (key: string, value: any, row: T) => {
    if (key === "landing_name") {
      if (landingLinkByIdPath) {
        return <a href={`${landingLinkByIdPath}/${row.id}`}>{value}</a>;
      }

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

    if (
      key === "registered_at" ||
      key === "created_at" ||
      key === "paid_at" ||
      key === "stage_started_at" ||
      key === "quarantine_ends_at"
    ) {
      return formatIsoToLocalDatetime(value, false);
    }

    if (typeof value === "boolean") {
      return value ? (
        <span className="highlight">Yes</span>
      ) : (
        <span className="error">No</span>
      );
    }

    if (key === "assignee") {
      return (
        <div className={s.custom_cell}>
          <span>Staff: {value.staff_name}</span>
          {value.account_name && <span>Ad account: {value.account_name}</span>}
        </div>
      );
    }

    if (value === null || value === undefined) return "";
    if (typeof value === "object") return JSON.stringify(value);

    return value;
  };

  const paintCell = (index: number): string => {
    if (!structured || index < 3) return "";
    const color = colors.get(index % colors.size);
    return color || "";
  };

  return (
    <div className={s.table_component}>
      {title && <h4 className={s.table_title}>{title}</h4>}
      <div className={s.table_wrapper}>
        {loading && <LoaderOverlay />}
        <table className={s.table}>
          <thead>
            <tr>
              {showIndex && <th>#</th>} {/* 👈 добавлено условие */}
              {headers.map((key) => (
                <th key={key}>{columnLabels[key as keyof T] || key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIdx) => (
              <tr key={rowIdx} className={row.color ? s[row.color] : ""}>
                {showIndex && ( // 👈 добавлено условие
                  <td style={{ paddingLeft: row.color ? "15px" : "" }}>
                    {rowIdx + 1}
                  </td>
                )}
                {headers.map((key, index) => (
                  <td
                    key={key}
                    className={paintCell(index)}
                    style={
                      typeof row[key] === "number"
                        ? { textAlign: "center" }
                        : undefined
                    }
                  >
                    {renderCell(key, row[key], row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Table;
