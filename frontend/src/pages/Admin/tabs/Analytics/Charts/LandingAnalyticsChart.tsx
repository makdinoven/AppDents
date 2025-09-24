import s from "./../../../pages/landing/LandingAnalytics.module.scss";
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
  visits: "#01433d",
  purchases: "#90e895",
};

type SeriesData = {
  ts: string;
  count: number;
};

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const fullDate = payload[0].payload.fullDate;

  return (
    <div className={s.tooltip}>
      <p className={s.tooltip_date}>{fullDate}</p>
      {payload.map((entry: any) => (
        <p className={s[entry.name]} key={entry.dataKey}>
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  );
};

const LandingAnalyticsChart = ({
  data,
  type,
  loading,
}: {
  loading?: boolean;
  data: Record<string, SeriesData[]>;
  type: "hour" | "day";
}) => {
  const isHour = type === "hour";
  const sources = Object.keys(data);
  const timestamps = data[sources[0]]?.map((s) => s.ts) || [];

  const formattedData = timestamps.map((ts, idx) => {
    const d = new Date(ts);

    const row: Record<string, any> = {
      date: isHour ? d.getHours() + ":00" : formatShortDate(ts),
      fullDate: `${formatShortDate(ts)} ${d.getHours().toString().padStart(2, "0")}:00`,
    };

    sources.forEach((src) => {
      row[src] = data[src][idx]?.count ?? 0;
    });

    return row;
  });

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
          {sources.map((src) => (
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

export default LandingAnalyticsChart;
