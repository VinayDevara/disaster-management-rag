// export default function TopBar({ active, onChange }) {
//   return (
//     <div style={styles.bar}>
//       <div style={styles.left} />

//       <div style={styles.title}>VIDYA</div>

//       <div style={styles.actions}>
//         <button
//           type="button"
//           onClick={() => onChange("chatbot")}
//           style={btn(active === "chatbot")}
//         >
//           Chatbot
//         </button>

//         <button
//           type="button"
//           onClick={() => onChange("visualization")}
//           style={btn(active === "visualization")}
//         >
//           Visualization
//         </button>
//       </div>
//     </div>
//   );
// }

// const styles = {
//   bar: {
//     height: 56,
//     background: "#000",
//     color: "#fff",
//     display: "flex",
//     alignItems: "center",
//     padding: "0 16px",
//   },
//   left: { flex: 1 },
//   title: { flex: 1, textAlign: "center", fontSize: 20, fontWeight: 900 },
//   actions: { flex: 1, display: "flex", justifyContent: "flex-end", gap: 10 },
// };

// const btn = (active) => ({
//   padding: "8px 14px",
//   borderRadius: 10,
//   border: "1px solid #fff",
//   background: active ? "#fff" : "#000",
//   color: active ? "#000" : "#fff",
//   cursor: "pointer",
//   fontWeight: 800,
// });

export default function TopBar({ active, onChange }) {
  return (
    <div style={styles.bar}>
      <div style={styles.left} />

      <div style={styles.title}>VIDYA</div>

      <div style={styles.actions}>
        <button
          type="button"
          onClick={() => onChange("chatbot")}
          style={btn(active === "chatbot")}
        >
          Chatbot
        </button>

        <button
          type="button"
          onClick={() => onChange("visualization")}
          style={btn(active === "visualization")}
        >
          Visualization
        </button>
      </div>
    </div>
  );
}

const styles = {
  bar: {
    height: 96,                 // 🔥 increased
    background: "#000",
    color: "#fff",
    display: "flex",
    alignItems: "center",
    padding: "0 24px",          // 🔥 more breathing room
    flexShrink: 0,
  },
  left: {
    flex: 1,
  },
  title: {
    flex: 1,
    textAlign: "center",
    fontSize: 36,               // 🔥 bigger VIDYA
    fontWeight: 900,
    letterSpacing: 1,
  },
  actions: {
    flex: 1,
    display: "flex",
    justifyContent: "flex-end",
    gap: 12,                    // 🔥 slightly more spacing
  },
};

const btn = (active) => ({
  padding: "10px 18px",         // 🔥 taller buttons
  borderRadius: 12,
  border: "1px solid #fff",
  background: active ? "#fff" : "#000",
  color: active ? "#000" : "#fff",
  cursor: "pointer",
  fontWeight: 800,
});
