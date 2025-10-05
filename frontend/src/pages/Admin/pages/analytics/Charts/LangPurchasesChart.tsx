import s from "../Analytics.module.scss";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import LoaderOverlay from "../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";

const LangPurchasesChart = ({
  data,
  loading,
}: {
  loading?: boolean;
  data: {
    date: string;
    languages: { language: string; count: number; total_amount: string }[];
  }[];
}) => {
  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate);
    return date.toLocaleDateString("en-US", {
      day: "2-digit",
      month: "short",
    });
  };

  const lineColors: Record<string, string> = {
    EN: "#7fdfd5",
    RU: "#79cee7",
    IT: "#01433d",
    ES: "#90e895",
    PT: "#fe0502",
    AR: "#ffbebf",
  };

  const formattedData = data.map((day) => {
    const obj: Record<string, any> = { date: formatDate(day.date) };
    day.languages.forEach((lang) => {
      obj[lang.language] = lang.count;
      obj[`${lang.language}_amount`] = lang.total_amount;
    });
    return obj;
  });

  const allLanguages = Array.from(
    new Set(data.flatMap((d) => d.languages.map((l) => l.language))),
  );

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className={s.tooltip}>
          <p className={s.tooltip_date}>{label}</p>
          {payload.map((entry: any, index: number) => {
            const lang = entry.dataKey;
            const amount = entry.payload?.[`${lang}_amount`];
            return (
              <p key={index} style={{ color: entry.color }}>
                {lang}: {entry.value} ({amount})
              </p>
            );
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={s.chart_container}>
      {loading && <LoaderOverlay />}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={formattedData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis allowDecimals={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          {allLanguages.map((lang) => (
            <Line
              key={lang}
              type="monotone"
              dataKey={lang}
              stroke={lineColors[lang] || "#000"}
              name={lang}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LangPurchasesChart;
