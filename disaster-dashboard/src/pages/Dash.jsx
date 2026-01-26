// import { useState } from "react";
// import ChatPanel from "../components/ChatPanel";
// import SidebarHistory from "../components/sidebarhistory";

// export default function Chatbot() {
//   const [selectedDate, setSelectedDate] = useState(null);
//   const [historyOpen, setHistoryOpen] = useState(true);

//   const SIDEBAR_W = 320;

//   return (
//     <div
//       style={{
//         display: "flex",
//         height: "100%",
//         position: "relative",
//         overflow: "hidden",
//         background: "#fff",
//       }}
//     >
//       {/* SHOW BUTTON (only when history is hidden) */}
//       {!historyOpen && (
//         <button
//           onClick={() => setHistoryOpen(true)}
//           style={{
//             position: "absolute",
//             top: 90, // below TopBar
//             left: 16,
//             zIndex: 50,
//             padding: "8px 12px",
//             borderRadius: 10,
//             border: "1px solid #ddd",
//             background: "#111",
//             color: "#fff",
//             cursor: "pointer",
//             fontWeight: 700,
//           }}
//         >
//           Show History
//         </button>
//       )}

//       {/* LEFT: Sliding History */}
//       <div
//         style={{
//           width: SIDEBAR_W,
//           flexShrink: 0,
//           borderRight: "1px solid #eee",
//           background: "#fff",
//           transform: historyOpen
//             ? "translateX(0)"
//             : `translateX(-${SIDEBAR_W}px)`,
//           transition: "transform 0.25s ease",
//         }}
//       >
//         <div
//           style={{
//             width: SIDEBAR_W,
//             height: "100%",
//             display: "flex",
//             flexDirection: "column",
//           }}
//         >
//           {/* History header */}
//           <div
//             style={{
//               padding: 12,
//               borderBottom: "1px solid #eee",
//               display: "flex",
//               alignItems: "center",
//               justifyContent: "space-between",
//               gap: 10,
//             }}
//           >
//             <div>
//               <div style={{ fontWeight: 900, fontSize: 18 }}>
//                 History
//               </div>
//               <div style={{ fontSize: 12, color: "#666" }}>
//                 Click a day to open chats
//               </div>
//             </div>

//             <button
//               onClick={() => setHistoryOpen(false)}
//               style={{
//                 padding: "8px 10px",
//                 borderRadius: 10,
//                 border: "1px solid #ddd",
//                 background: "#111",
//                 color: "#fff",
//                 cursor: "pointer",
//                 fontWeight: 700,
//               }}
//             >
//               Hide
//             </button>
//           </div>

//           {/* History list */}
//           <div style={{ flex: 1, overflow: "auto" }}>
//             <SidebarHistory
//               selectedDate={selectedDate}
//               onSelectDate={setSelectedDate}
//             />
//           </div>
//         </div>
//       </div>

//       {/* CHAT PANEL */}
//       <div
//         style={{
//           flex: 1,
//           minWidth: 0,
//           height: "100%",
//           marginLeft: historyOpen ? 0 : -SIDEBAR_W,
//           transition: "margin-left 0.25s ease",
//         }}
//       >
//         <ChatPanel selectedDate={selectedDate} />
//       </div>
//     </div>
//   );
// }

import { useState } from "react";
import ChatPanel from "../components/ChatPanel";
import SidebarHistory from "../components/sidebarhistory";
import FlightsMap from "../components/FlightsMap"; // ✅ adjust path if needed

export default function Chatbot() {
  const [selectedDate, setSelectedDate] = useState(null);
  const [historyOpen, setHistoryOpen] = useState(true);

  const SIDEBAR_W = 320;
  const MAP_W = 420; // ✅ map width on right

  return (
    <div
      style={{
        display: "flex",
        height: "100%",
        position: "relative",
        overflow: "hidden",
        background: "#fff",
      }}
    >
      {/* ✅ SHOW BUTTON (only when history is hidden) */}
      {!historyOpen && (
        <button
          onClick={() => setHistoryOpen(true)}
          style={{
            position: "absolute",
            top: 90, // below TopBar
            left: 16,
            zIndex: 50,
            padding: "8px 12px",
            borderRadius: 10,
            border: "1px solid #ddd",
            background: "#111",
            color: "#fff",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          Show History
        </button>
      )}

      {/* ✅ LEFT: Sliding History */}
      <div
        style={{
          width: SIDEBAR_W,
          flexShrink: 0,
          borderRight: "1px solid #eee",
          background: "#fff",
          transform: historyOpen
            ? "translateX(0)"
            : `translateX(-${SIDEBAR_W}px)`,
          transition: "transform 0.25s ease",
        }}
      >
        <div
          style={{
            width: SIDEBAR_W,
            height: "100%",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* ✅ History header */}
          <div
            style={{
              padding: 12,
              borderBottom: "1px solid #eee",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 10,
            }}
          >
            <div>
              <div style={{ fontWeight: 900, fontSize: 18 }}>History</div>
              <div style={{ fontSize: 12, color: "#666" }}>
                Click a day to open chats
              </div>
            </div>

            <button
              onClick={() => setHistoryOpen(false)}
              style={{
                padding: "8px 10px",
                borderRadius: 10,
                border: "1px solid #ddd",
                background: "#111",
                color: "#fff",
                cursor: "pointer",
                fontWeight: 700,
              }}
            >
              Hide
            </button>
          </div>

          {/* ✅ History list */}
          <div style={{ flex: 1, minHeight: 0, overflow: "auto" }}>
            <SidebarHistory
              selectedDate={selectedDate}
              onSelectDate={setSelectedDate}
            />
          </div>
        </div>
      </div>

      {/* ✅ RIGHT AREA: Chat + Map */}
      <div
        style={{
          display: "flex",
          flex: 1,
          minWidth: 0,
          height: "100%",
          marginLeft: historyOpen ? 0 : -SIDEBAR_W, // remove gap when sidebar hidden
          transition: "margin-left 0.25s ease",
        }}
      >
        {/* ✅ Middle: Chat */}
        <div style={{ flex: 1, minWidth: 0, height: "100%" }}>
          <ChatPanel selectedDate={selectedDate} />
        </div>

        {/* ✅ Right: Map */}
        <div
          style={{
            width: MAP_W,
            flexShrink: 0,
            borderLeft: "1px solid #eee",
            background: "#fff",
            height: "100%",
          }}
        >
          {/* Optional header */}
          <div
            style={{
              padding: 12,
              borderBottom: "1px solid #eee",
              fontWeight: 900,
              fontSize: 16,
            }}
          >
            Live Flights
          </div>

          <div style={{ height: `calc(100% - 49px)` }}>
            <FlightsMap
              center={{ lat: 12.9141, lon: 74.856 }} // Mangalore
              radiusKm={150}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
