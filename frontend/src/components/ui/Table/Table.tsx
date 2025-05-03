import s from "./Table.module.scss";
import { Path } from "../../../routes/routes.ts";

interface TableProps<T extends Record<string, any>> {
  data: T[];
  columnLabels?: Partial<Record<keyof T, string>>;
}

const Table = <T extends Record<string, any>>({
  data,
  columnLabels = {},
}: TableProps<T>) => {
  if (!data || data.length === 0) return <div className={s.empty}>No data</div>;

  const headers = Object.keys(data[0]).filter(
    (key) => key !== "slug" && key !== "landing_slug",
  );

  return (
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
                <td key={key}>
                  {key === "landing_name" ? (
                    <a
                      href={`${Path.landing}/${row.slug ? row.slug : row.landing_slug}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {row[key]}
                    </a>
                  ) : typeof row[key] === "boolean" ? (
                    row[key] ? (
                      <span className="highlight">Yes</span>
                    ) : (
                      <span className="error">No</span>
                    )
                  ) : (
                    row[key]
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Table;
