// import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

// export default function eventschart() {
//   const data = [
//     { name: "Wildfires", count: 7 },
//     { name: "Storms", count: 4 },
//     { name: "Volcanoes", count: 2 },
//     { name: "Floods", count: 3 },
//   ];

//   return (
//     <div>
//       <h3 style={{ margin: "6px 0 10px" }}>Recent Disaster Events</h3>
//       <div style={{ height: 260 }}>
//         <ResponsiveContainer width="100%" height="100%">
//           <BarChart data={data}>
//             <XAxis dataKey="name" tick={{ fontSize: 12 }} />
//             <YAxis allowDecimals={false} />
//             <Tooltip />
//             <Bar dataKey="count" />
//           </BarChart>
//         </ResponsiveContainer>
//       </div>
//     </div>
//   );
// }

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function EventsChart({ data = [] }) {
  return (
    <div>
      <h3 style={{ margin: "6px 0 10px" }}>Recent Disaster Events</h3>
      <div style={{ height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
