import { useState } from "react";
import axios from "axios";

export default function FeedbackModal({ isOpen, onClose }) {
  const [rating, setRating] = useState(5);
  const [category, setCategory] = useState("Suggestion");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!comment.trim()) {
      alert("Please enter feedback");
      return;
    }

    try {
      setLoading(true);

     await axios.post("http://127.0.0.1:8000/api/feedback", {
  rating,
  category,
  comment,
  page: window.location.pathname,
});

      alert("Thank you for your feedback!");
      setComment("");
      setCategory("Suggestion");
      setRating(5);
      onClose();
    } catch (err) {
      alert("Failed to submit feedback");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
  <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-50">
    <div className="w-[420px] rounded-2xl bg-white p-6 shadow-2xl space-y-4 border border-gray-200">
      <h2 className="text-2xl font-bold text-gray-900">Help Us Improve</h2>

      <p className="text-sm text-gray-600">
        Tell us what went wrong or what we can improve
      </p>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-800">Rating</label>
        <select
          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          value={rating}
          onChange={(e) => setRating(Number(e.target.value))}
        >
          <option value={5}>5 - Excellent</option>
          <option value={4}>4 - Good</option>
          <option value={3}>3 - Average</option>
          <option value={2}>2 - Poor</option>
          <option value={1}>1 - Very Poor</option>
        </select>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-800">Category</label>
        <select
          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option>Response Quality</option>
          <option>UI/UX</option>
          <option>Bug/Error</option>
          <option>Performance</option>
          <option>News Relevance</option>
          <option>Suggestion</option>
        </select>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-800">Comment</label>
        <textarea
          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder:text-gray-400 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          rows="4"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Write your feedback..."
        />
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <button
          onClick={onClose}
          className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-100"
        >
          Cancel
        </button>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Submitting..." : "Submit"}
        </button>
      </div>
    </div>
  </div>
);
}