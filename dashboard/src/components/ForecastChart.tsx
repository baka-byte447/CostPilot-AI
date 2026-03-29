

import { LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";

export default function ForecastChart({ data }: any) {

  return (
    <LineChart width={600} height={300} data={data}>
      <XAxis dataKey="timestamp" />
      <YAxis />
      <Tooltip />
      <Line type="monotone" dataKey="prediction" stroke="#ff7300" />
    </LineChart>
  );
}

