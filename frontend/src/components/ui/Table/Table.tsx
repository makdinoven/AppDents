import s from "./Table.module.scss";

interface TableProps<T extends Record<string, any>> {
  data: T[];
  columnLabels?: Partial<Record<keyof T, string>>;
}

const Table = <T extends Record<string, any>>({
  data,
  columnLabels = {},
}: TableProps<T>) => {
  if (!data || data.length === 0) return <div className={s.empty}>No data</div>;

  const headers = Object.keys(data[0]);

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
                  {typeof row[key] === "boolean" ? (
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
