import { useState } from "react";
import FeedbackModal from "./FeedbackModal";

export default function HelpUsImproveButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 bg-blue-600 text-white px-5 py-3 rounded-full shadow-lg hover:bg-blue-700 transition"
      >
        Help Us Improve
      </button>

      <FeedbackModal isOpen={open} onClose={() => setOpen(false)} />
    </>
  );
}