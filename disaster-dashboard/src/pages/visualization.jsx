// import { useEffect, useState } from "react";
// import { api } from "../api/client";
// import EventsChart from "../components/EventsChart";
// import FlightsChart from "../components/FlightsChart";

// export default function Visualization() {
//   const [tab, setTab] = useState("events");
//   const [eventsData, setEventsData] = useState([]);
//   const [flightsData, setFlightsData] = useState([]);
//   const [loading, setLoading] = useState(false);

//   useEffect(() => {
//     (async () => {
//       setLoading(true);
//       try {
//         const [ev, fl] = await Promise.all([
//           api.get("/viz/events/summary"),
//           api.get("/viz/flights/top-flights"),
// ,
//         ]);
//         setEventsData(ev.data);
//         setFlightsData(fl.data);
//       } finally {
//         setLoading(false);
//       }
//     })();
//   }, []);

//   return (
//     <div style={{ padding: 20 }}>
//       <h2 style={{ margin: 0 }}>Visualization</h2>

//       <div style={{ display: "flex", gap: 10, margin: "12px 0" }}>
//         <button onClick={() => setTab("events")}>Events</button>
//         <button onClick={() => setTab("flights")}>Flights</button>
//       </div>

//       {loading ? (
//         <div>Loading…</div>
//       ) : tab === "events" ? (
//         <EventsChart data={eventsData} />
//       ) : (
//         <FlightsChart data={flightsData} />
//       )}
//     </div>
//   );
// }

import { useEffect, useState } from "react";
import { api } from "../api/client";
import EventsChart from "../components/EventsChart";
import FlightsChart from "../components/FlightsChart";

export default function Visualization() {
  const [tab, setTab] = useState("events");
  const [eventsData, setEventsData] = useState([]);
  const [flightsData, setFlightsData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [ev, fl] = await Promise.all([
          api.get("/viz/events/summary"),
          api.get("/viz/flights/top-flights"), // ✅ FIXED
          
        ]);
        setEventsData(ev.data);
        setFlightsData(fl.data);

      } catch (e) {
        console.error("Visualization fetch error:", e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h2 style={{ margin: 0 }}>Visualization</h2>

      <div style={{ display: "flex", gap: 10, margin: "12px 0" }}>
        <button onClick={() => setTab("events")}>Events</button>
        <button onClick={() => setTab("flights")}>Flights</button>
      </div>

      {loading ? (
        <div>Loading…</div>
      ) : tab === "events" ? (
        <EventsChart data={eventsData} />
      ) : (
        <FlightsChart data={flightsData} />
      )}
    </div>
  );
}
