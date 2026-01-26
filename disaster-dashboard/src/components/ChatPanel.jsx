// import { useEffect, useMemo, useRef, useState } from "react";
// import { api } from "../api/client";

// const MOCK_MODE = true; // later set false when FastAPI endpoints are ready

// export default function ChatPanel({ selectedDate }) {
//   const [messages, setMessages] = useState([]);
//   const [input, setInput] = useState("");
//   const [loading, setLoading] = useState(false);
//   const bottomRef = useRef(null);

//   const dateKey = useMemo(() => {
//     if (selectedDate) return selectedDate;
//     const d = new Date();
//     return d.toISOString().slice(0, 10); // YYYY-MM-DD
//   }, [selectedDate]);

//   useEffect(() => {
//     // load messages for this date
//     (async () => {
//       if (MOCK_MODE) {
//         setMessages(mockMessages(dateKey));
//         return;
//       }
//       const res = await api.get(`/chats/${dateKey}`);
//       setMessages(res.data.messages || []);
//     })();
//   }, [dateKey]);

//   useEffect(() => {
//     bottomRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [messages, loading]);

//   async function send() {
//     const q = input.trim();
//     if (!q || loading) return;

//     const userMsg = { role: "user", message: q, created_at: new Date().toISOString() };
//     setMessages((m) => [...m, userMsg]);
//     setInput("");
//     setLoading(true);

//     try {
//       if (MOCK_MODE) {
//         const assistantMsg = {
//           role: "assistant",
//           message: `Mock answer for: "${q}". (Backend not connected yet)`,
//           meta: { agent_used: ["mock_agent"], citations: [] },
//           created_at: new Date().toISOString(),
//         };
//         setMessages((m) => [...m, assistantMsg]);
//         return;
//       }

//       // backend: POST /chat { question, date_key }
//       const res = await api.post("/chat", { question: q, date_key: dateKey });
//       const assistantMsg = {
//         role: "assistant",
//         message: res.data.answer,
//         meta: res.data.meta,
//         created_at: new Date().toISOString(),
//       };
//       setMessages((m) => [...m, assistantMsg]);
//     } catch (e) {
//       setMessages((m) => [
//         ...m,
//         { role: "assistant", message: "Error talking to backend. Check server.", created_at: new Date().toISOString() },
//       ]);
//     } finally {
//       setLoading(false);
//     }
//   }

//   return (
//     <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
//       <div style={{ padding: 14, borderBottom: "1px solid #eee" }}>
//         <div style={{ fontWeight: 700 }}>Chat</div>
//         <div style={{ color: "#666", fontSize: 13 }}>Saved by date: {dateKey}</div>
//       </div>

//       <div style={{ flex: 1, overflow: "auto", padding: 16, background: "#fafafa" }}>
//         {messages.map((m, idx) => (
//           <MessageBubble key={idx} m={m} />
//         ))}
//         {loading && <div style={{ color: "#666", fontSize: 14 }}>Thinking…</div>}
//         <div ref={bottomRef} />
//       </div>

//       <div style={{ padding: 12, borderTop: "1px solid #eee", display: "flex", gap: 8 }}>
//         <input
//           value={input}
//           onChange={(e) => setInput(e.target.value)}
//           onKeyDown={(e) => (e.key === "Enter" ? send() : null)}
//           placeholder="Ask about recent disasters, flights, weather..."
//           style={{
//             flex: 1,
//             padding: "10px 12px",
//             borderRadius: 12,
//             border: "1px solid #ddd",
//             outline: "none",
//           }}
//         />
//         <button onClick={send} style={sendBtn}>
//           Send
//         </button>
//       </div>
//     </div>
//   );
// }

// function MessageBubble({ m }) {
//   const isUser = m.role === "user";
//   return (
//     <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 10 }}>
//       <div
//         style={{
//           maxWidth: "78%",
//           padding: "10px 12px",
//           borderRadius: 14,
//           background: isUser ? "#111" : "#fff",
//           color: isUser ? "#fff" : "#111",
//           border: isUser ? "none" : "1px solid #e6e6e6",
//           boxShadow: "0 1px 0 rgba(0,0,0,0.03)",
//           whiteSpace: "pre-wrap",
//         }}
//       >
//         {m.message}
//         {m.meta?.agent_used?.length ? (
//           <div style={{ marginTop: 8, fontSize: 12, color: isUser ? "#ddd" : "#666" }}>
//             Agents: {m.meta.agent_used.join(", ")}
//           </div>
//         ) : null}
//       </div>
//     </div>
//   );
// }

// const sendBtn = {
//   padding: "10px 14px",
//   borderRadius: 12,
//   border: "1px solid #111",
//   background: "#111",
//   color: "#fff",
//   cursor: "pointer",
//   fontWeight: 700,
// };

// function mockMessages(dateKey) {
//   return [
//     { role: "assistant", message: `Hi! This is your dashboard chat for ${dateKey}.`, created_at: new Date().toISOString() },
//   ];
// }

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";

const MOCK_MODE = false;

export default function ChatPanel({ selectedDate }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  const dateKey = useMemo(() => {
    if (selectedDate) return selectedDate;
    const d = new Date();
    return d.toISOString().slice(0, 10);
  }, [selectedDate]);

  useEffect(() => {
    (async () => {
      if (MOCK_MODE) {
        setMessages(mockMessages(dateKey));
        return;
      }
      const res = await api.get(`/chats/${dateKey}`);
      setMessages(res.data.messages || []);
    })();
  }, [dateKey]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send() {
    const q = input.trim();
    if (!q || loading) return;

    const userMsg = { role: "user", message: q, created_at: new Date().toISOString() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      if (MOCK_MODE) {
        const assistantMsg = {
          role: "assistant",
          message: `Mock answer for: "${q}". (Backend not connected yet)`,
          created_at: new Date().toISOString(),
        };
        setMessages((m) => [...m, assistantMsg]);
        return;
      }

      const res = await api.post("/chat", { question: q, date_key: dateKey });
      const assistantMsg = {
        role: "assistant",
        message: res.data.answer,
        meta: res.data.meta,
        created_at: new Date().toISOString(),
      };
      setMessages((m) => [...m, assistantMsg]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", message: "Error talking to backend. Check server.", created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: 14, borderBottom: "1px solid #eee" }}>
        <div style={{ fontWeight: 700 }}>Chat</div>
        <div style={{ color: "#666", fontSize: 13 }}>Saved by date: {dateKey}</div>
      </div>

      <div style={{ flex: 1, overflow: "auto", padding: 16, background: "#fafafa" }}>
        {messages.map((m, idx) => (
          <MessageBubble key={idx} m={m} />
        ))}
        {loading && <div style={{ color: "#666", fontSize: 14 }}>Thinking…</div>}
        <div ref={bottomRef} />
      </div>

      <div style={{ padding: 12, borderTop: "1px solid #eee", display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => (e.key === "Enter" ? send() : null)}
          placeholder="Ask about recent disasters, flights, weather..."
          style={{
            flex: 1,
            padding: "10px 12px",
            borderRadius: 12,
            border: "1px solid #ddd",
            outline: "none",
          }}
        />
        <button onClick={send} style={sendBtn}>Send</button>
      </div>
    </div>
  );
}

function MessageBubble({ m }) {
  const isUser = m.role === "user";
  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 10 }}>
      <div
        style={{
          maxWidth: "78%",
          padding: "10px 12px",
          borderRadius: 14,
          background: isUser ? "#111" : "#fff",
          color: isUser ? "#fff" : "#111",
          border: isUser ? "none" : "1px solid #e6e6e6",
          whiteSpace: "pre-wrap",
        }}
      >
        {m.message}
      </div>
    </div>
  );
}

const sendBtn = {
  padding: "10px 14px",
  borderRadius: 12,
  border: "1px solid #111",
  background: "#111",
  color: "#fff",
  cursor: "pointer",
  fontWeight: 700,
};

function mockMessages(dateKey) {
  return [{ role: "assistant", message: `Hi! This is your dashboard chat for ${dateKey}.`, created_at: new Date().toISOString() }];
}
