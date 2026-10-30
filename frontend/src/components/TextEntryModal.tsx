import React, { useState } from "react";
import { X, Sparkles, PenTool } from "lucide-react";
import { api } from "../services/api";
import { DiaryEntry } from "../types";

interface TextEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEntryCreated: (entry: DiaryEntry) => void;
}

export const TextEntryModal: React.FC<TextEntryModalProps> = ({
  isOpen,
  onClose,
  onEntryCreated
}) => {
  if (!isOpen) return null;

  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const entry = await api.submitText(text, title || undefined);
      onEntryCreated(entry);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit entry");
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillExample = () => {
    setText("Had a productive morning session with the project team. We finalized the architecture and agreed to share the revised proposal by Friday.");
    setTitle("Project Planning & Architecture Review");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-[#fbf7ee] border-2 border-[#cbb79a] rounded-2xl p-6 w-full max-w-lg shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#8a6e50] hover:text-[#3d2714] p-1"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-lg bg-[#ebdcc4] text-[#543820]">
            <PenTool className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#3d2817] font-serif-title">
              Write a Memory
            </h3>
            <p className="text-xs text-[#7d654c]">
              Capture your day in words. AI will extract your commitments, people, and places.
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-4 p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800">
            {errorMsg}
          </div>
        )}

        <div className="space-y-3 mb-5">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title (optional)..."
            className="w-full px-3.5 py-2.5 bg-white border border-[#d8c5aa] rounded-xl text-sm font-semibold text-[#3d2714] placeholder-[#a6927d] focus:outline-none focus:border-[#543820]"
          />

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            placeholder="What happened today? Who did you meet, where did you go, or what's on your mind?..."
            className="w-full px-3.5 py-2.5 bg-white border border-[#d8c5aa] rounded-xl text-sm text-[#3d2714] placeholder-[#a6927d] leading-relaxed font-serif-title focus:outline-none focus:border-[#543820]"
          />
        </div>

        <div className="flex items-center justify-between">
          <button
            onClick={fillExample}
            className="text-xs font-semibold text-emerald-800 hover:text-emerald-950 underline"
          >
            Try an example prompt
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-[#7d654c] hover:bg-[#ebdcc4]"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !text.trim()}
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-[#543820] hover:bg-[#3d2714] shadow-md transition-all active:scale-95 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>{isSubmitting ? "Saving & Analyzing..." : "Understand with AI"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
