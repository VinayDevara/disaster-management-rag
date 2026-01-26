// import { useMemo } from "react";

// export default function sidebarhistory({ selectedDate, onSelectDate }) {
//   const last7 = useMemo(() => {
//     const arr = [];
//     const now = new Date();
//     for (let i = 0; i < 7; i++) {
//       const d = new Date(now);
//       d.setDate(now.getDate() - i);
//       arr.push(d.toISOString().slice(0, 10));
//     }
//     return arr;
//   }, []);

//   return (
//     <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
//       <div style={{ padding: 14, borderBottom: "1px solid #eee" }}>
//         <div style={{ fontWeight: 800 }}>History</div>
//         <div style={{ fontSize: 13, color: "#666" }}>Click a day to open chats</div>
//       </div>

//       <div style={{ padding: 12, overflow: "auto" }}>
//         {last7.map((d) => (
//           <button
//             key={d}
//             onClick={() => onSelectDate(d)}
//             style={{
//               width: "100%",
//               textAlign: "left",
//               padding: "10px 12px",
//               borderRadius: 12,
//               border: "1px solid #e6e6e6",
//               background: selectedDate === d ? "#111" : "#fff",
//               color: selectedDate === d ? "#fff" : "#111",
//               cursor: "pointer",
//               marginBottom: 10,
//               fontWeight: 700,
//             }}
//           >
//             {d}
//           </button>
//         ))}
//       </div>
//     </div>
//   );
// }

import { useMemo } from "react";

export default function sidebarhistory({ selectedDate, onSelectDate }) {
  const last7 = useMemo(() => {
    const arr = [];
    const now = new Date();
    for (let i = 0; i < 7; i++) {
      const d = new Date(now);
      d.setDate(now.getDate() - i);
      arr.push(d.toISOString().slice(0, 10));
    }
    return arr;
  }, []);

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: 14, borderBottom: "1px solid #eee" }}>
      </div>

      <div style={{ padding: 12, overflow: "auto" }}>
        {last7.map((d) => (
          <button
            key={d}
            onClick={() => onSelectDate(d)}
            style={{
              width: "100%",
              textAlign: "left",
              padding: "10px 12px",
              borderRadius: 12,
              border: "1px solid #e6e6e6",
              background: selectedDate === d ? "#111" : "#fff",
              color: selectedDate === d ? "#fff" : "#111",
              cursor: "pointer",
              marginBottom: 10,
              fontWeight: 700,
            }}
          >
            {d}
          </button>
        ))}
      </div>
    </div>
  );
}
