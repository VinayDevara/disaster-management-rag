// // import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

// // export default function FlightsChart() {
// //   const data = [
// //     { route: "BLR → HYD", flights: 18 },
// //     { route: "DEL → BOM", flights: 14 },
// //     { route: "MAA → BLR", flights: 11 },
// //     { route: "HYD → DEL", flights: 9 },
// //   ];

// //   return (
// //     <div>
// //       <h3 style={{ margin: "6px 0 10px" }}>Flight Data</h3>
// //       <div style={{ height: 260 }}>
// //         <ResponsiveContainer width="100%" height="100%">
// //           <BarChart data={data}>
// //             <XAxis dataKey="route" tick={{ fontSize: 12 }} />
// //             <YAxis allowDecimals={false} />
// //             <Tooltip />
// //             <Bar dataKey="flights" />
// //           </BarChart>
// //         </ResponsiveContainer>
// //       </div>
// //     </div>
// //   );
// // }

// import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

// export default function FlightsChart({ data = [] }) {
//   return (
//     <div>
//       <h3 style={{ margin: "6px 0 10px" }}>Flight Data</h3>
//       <div style={{ height: 260 }}>
//         <ResponsiveContainer width="100%" height="100%">
//           <BarChart data={data}>
//             <XAxis dataKey="route" tick={{ fontSize: 12 }} />
//             <YAxis allowDecimals={false} />
//             <Tooltip />
//             <Bar dataKey="flights" />
//           </BarChart>
//         </ResponsiveContainer>
//       </div>
//     </div>
//   );
// }

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export default function FlightsChart({ data = [] }) {
  // quick debug
  console.log("FlightsChart data:", data);

  return (
    <div style={{ marginTop: 16 }}>
      <h3 style={{ margin: "10px 0" }}>Flight Data</h3>

      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
