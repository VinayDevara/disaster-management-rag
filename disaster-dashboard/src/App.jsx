// import Dashboard from "./pages/Dash.jsx";

// export default function App() {
//   return <Dashboard />;
// }

// import { useState } from "react";
// import TopBar from "./components/TopBar";
// import Dash from "./pages/Dash";
// import Visualization from "./pages/visualization";

// export default function App() {
//   const [activePage, setActivePage] = useState("chatbot"); // "chatbot" | "viz"

//   return (
//     <div style={{ minHeight: "100vh", background: "#f6f6f6" }}>
//       <TopBar activePage={activePage} setActivePage={setActivePage} />

//       {activePage === "chatbot" ? <Dash /> : <Visualization />}
//     </div>
//   );
// }
import { useState } from "react";
import TopBar from "./components/TopBar";
import Chatbot from "./pages/Dash";
import Visualization from "./pages/visualization";

export default function App() {
  const [view, setView] = useState("chatbot");
  const [active, setActive] = useState("chatbot"); // chatbot | visualization

  return (
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column" }}>
      <TopBar active={active} onChange={setActive} />

      {/* Page Area */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {active === "chatbot" ? <Chatbot /> : <Visualization />}
      </div>
    </div>
  );
}
