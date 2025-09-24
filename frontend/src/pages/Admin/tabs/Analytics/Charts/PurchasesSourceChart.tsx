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
import { formatShortDate } from "../../../../../common/helpers/helpers.ts";
import LoaderOverlay from "../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";

const lineColors: Record<string, string> = {
  CABINET_OFFER: "#01433d",
  CART: "#90e895",
  COURSES_PAGE: "#5b6968",
  HOMEPAGE: "#ffbebf",
  LANDING: "#7fdfd5",
  PROFESSOR_PAGE: "#79cee7",
  CABINET_FREE: "#fe0502",
  LANDING_OFFER: "#017f74",
  SPECIAL_OFFER: "#e8db90",
};

const PurchasesSourceChart = ({
  data,
  type,
  loading,
}: {
  loading?: boolean;
  data: any[];
  type: "amount" | "count";
}) => {
  const isAmount = type === "amount";

  const formattedData = data.map((item) => {
    const seriesObject = item.series.reduce((acc: any, s: any) => {
      acc[s.source] = s.value;
      return acc;
    }, {});

    return {
      date: formatShortDate(item.date),
      ...seriesObject,
    };
  });

  const allSources = data[0]?.series.map((s: any) => s.source) || [];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className={s.tooltip}>
          <p className={s.tooltip_date}>{label}</p>
          {payload.map((entry: any, index: number) => {
            const src = entry.dataKey;
            return (
              <p key={index} style={{ color: entry.color }}>
                {src}: {entry.value.toFixed(2)} {isAmount && "$"}
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
          {allSources.map((src: any) => (
            <Line
              key={src}
              type="monotone"
              dataKey={src}
              stroke={lineColors[src] || "#000"}
              name={src}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PurchasesSourceChart;
