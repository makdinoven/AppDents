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

const UserGrowthChart = ({
  data,
}: {
  data: { date: string; new_users: number; total_users: number }[];
}) => {
  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate);
    return date.toLocaleDateString("en-US", {
      day: "2-digit",
      month: "short",
    });
  };

  const formattedData = data.map((item) => ({
    ...item,
    date: formatDate(item.date),
  }));

  return (
    <div className={s.chart_container}>
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
          {/*<Line*/}
          {/*  type="monotone"*/}
          {/*  dataKey="total_users"*/}
          {/*  stroke="#79cee7"*/}
          {/*  name="Total users"*/}
          {/*/>*/}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default UserGrowthChart;
