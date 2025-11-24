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
import { formatShortDate } from "../../../../../shared/common/helpers/helpers.ts";
import LoaderOverlay from "../../../../../shared/components/ui/LoaderOverlay/LoaderOverlay.tsx";

const UserGrowthChart = ({
  loading,
  data,
}: {
  loading?: boolean;
  data: { date: string; new_users: number; total_users: number }[];
}) => {
  const formattedData = data.map((item) => ({
    ...item,
    date: formatShortDate(item.date),
  }));

  return (
    <div className={s.chart_container}>
      {loading && <LoaderOverlay />}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={formattedData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="new_users"
            stroke="#7fdfd5"
            name="New users"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default UserGrowthChart;
