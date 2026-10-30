import React, { useState } from "react";
import confetti from "canvas-confetti";
import { Check, Edit2, RotateCcw, X, Sparkles, MapPin, User, Briefcase, Calendar } from "lucide-react";
import { DiaryEntry } from "../types";
import { api } from "../services/api";

interface DraftReviewModalProps {
  entry: DiaryEntry | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirmed: (updated: DiaryEntry) => void;
}

export const DraftReviewModal: React.FC<DraftReviewModalProps> = ({
  entry,
  isOpen,
  onClose,
  onConfirmed
}) => {
  if (!isOpen || !entry) return null;

  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(entry.title || "Memories of Today");
  const [content, setContent] = useState(entry.generated_content || entry.raw_text || "");
  const [selectedDisambig, setSelectedDisambig] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [selectedTone, setSelectedTone] = useState("reflective");

  const entities = (entry as any)?.entities || {};
  const people = entities.people?.length > 0 ? entities.people.join(", ") : "None detected";
  const places = entities.places?.length > 0 ? entities.places.join(", ") : "None detected";
  const project = entities.projects?.length > 0 ? entities.projects.join(", ") : (entry.category || "General");
  const commitment = entities.commitments?.length > 0
    ? entities.commitments.map((c: any) => typeof c === 'string' ? c : c.description).join(", ")
    : "None detected";

  const handleRegenerate = async (tone = selectedTone) => {
    if (!entry) return;
    setIsRegenerating(true);
    try {
      const regenerated = await api.regenerateEntry(entry.id, tone);
      if (regenerated.title) setTitle(regenerated.title);
      if (regenerated.generated_content) setContent(regenerated.generated_content);
    } catch (err) {
      console.error("Failed to regenerate entry:", err);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleConfirm = async () => {
    setIsSubmitting(true);
    try {
      const resolution = selectedDisambig && entry.disambiguation
        ? { [entry.disambiguation.entity]: selectedDisambig }
        : undefined;

      const confirmed = await api.confirmEntry(entry.id, title, content, resolution);

      // Trigger celebratory confetti on memory persistence
      try {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 }
        });
      } catch {}

      onConfirmed(confirmed);
      onClose();
    } catch (err) {
      console.error("Confirmation error:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="bg-[#fbf7ee] border-2 border-[#cbb79a] rounded-2xl p-6 w-full max-w-2xl shadow-2xl relative my-8">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#8a6e50] hover:text-[#3d2714] p-1"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-lg bg-amber-100 text-amber-800">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#3d2817] font-serif-title">
              Review AI Memory Draft
            </h3>
            <p className="text-xs text-[#7d654c]">
              Verify and polish before connecting to your Personal Life Graph.
            </p>
          </div>
        </div>

        {/* Generated Diary Card */}
        <div className="bg-[#f5ecda] border border-[#d9c7ab] rounded-xl p-5 mb-5 shadow-inner">
          <div className="flex items-center justify-between mb-3 border-b border-[#e5d5be] pb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#705439]">
                Generated Diary
              </span>
              {entry.mood && (
                <span className="px-2 py-0.5 rounded-md bg-emerald-100/90 text-emerald-800 text-[10px] font-bold uppercase tracking-wider border border-emerald-300/60">
                  Tone: {entry.mood}
                </span>
              )}
            </div>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="flex items-center gap-1 text-xs text-[#705439] hover:text-[#3d2714] font-medium"
            >
              <Edit2 className="w-3.5 h-3.5" />
              <span>{isEditing ? "Done Editing" : "Edit Narrative"}</span>
            </button>
          </div>

          {isEditing ? (
            <div className="space-y-3">
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 bg-white border border-[#d5c2a7] rounded-lg text-sm font-semibold text-[#3d2714]"
                placeholder="Entry Title..."
              />
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={5}
                className="w-full px-3 py-2 bg-white border border-[#d5c2a7] rounded-lg text-sm text-[#473322] leading-relaxed font-serif-title"
                placeholder="Diary narrative..."
              />
            </div>
          ) : (
            <div>
              <h4 className="text-base font-bold text-[#3d2714] mb-2 font-serif-title">
                {title}
              </h4>
              <p className="text-sm text-[#473322] leading-relaxed font-serif-title whitespace-pre-wrap">
                {content}
              </p>
            </div>
          )}
        </div>

        {/* Low-Confidence Disambiguation Query */}
        {entry.disambiguation && (
          <div className="mb-5 p-4 rounded-xl bg-amber-50 border border-amber-300">
            <p className="text-xs font-bold text-amber-900 mb-2">
              ?? Clarification Required: {entry.disambiguation.question}
            </p>
            <div className="flex flex-wrap gap-2">
              {entry.disambiguation.options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => setSelectedDisambig(opt)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    selectedDisambig === opt
                      ? "bg-amber-700 text-white border-amber-800 shadow-xs"
                      : "bg-white text-amber-900 border-amber-300 hover:bg-amber-100"
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Extracted Entities Grid */}
        <div className="mb-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 bg-[#ede0cb] rounded-lg border border-[#dbc7ad]">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[#573d23] mb-1">
              <User className="w-3.5 h-3.5 text-blue-700" />
              <span>People</span>
            </div>
            <p className="text-xs text-[#3a2817] truncate" title={people}>{people}</p>
          </div>

          <div className="p-3 bg-[#ede0cb] rounded-lg border border-[#dbc7ad]">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[#573d23] mb-1">
              <MapPin className="w-3.5 h-3.5 text-emerald-700" />
              <span>Places</span>
            </div>
            <p className="text-xs text-[#3a2817] truncate" title={places}>{places}</p>
          </div>

          <div className="p-3 bg-[#ede0cb] rounded-lg border border-[#dbc7ad]">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[#573d23] mb-1">
              <Briefcase className="w-3.5 h-3.5 text-purple-700" />
              <span>Category / Project</span>
            </div>
            <p className="text-xs text-[#3a2817] truncate" title={project}>{project}</p>
          </div>

          <div className="p-3 bg-[#ede0cb] rounded-lg border border-[#dbc7ad]">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[#573d23] mb-1">
              <Calendar className="w-3.5 h-3.5 text-red-700" />
              <span>Commitment</span>
            </div>
            <p className="text-xs text-[#3a2817] truncate" title={commitment}>{commitment}</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 border-t border-[#e5d5be] pt-4">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-[#7d654c] hover:bg-[#ebdcc4] transition-colors"
          >
            Cancel
          </button>

          <div className="hidden sm:flex items-center gap-1 bg-[#ede1ce] p-1 rounded-xl">
            {[
              { id: "reflective", label: "Reflective" },
              { id: "poetic", label: "Poetic" },
              { id: "concise", label: "Concise" },
              { id: "detailed", label: "Detailed" }
            ].map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => {
                  setSelectedTone(t.id);
                  handleRegenerate(t.id);
                }}
                disabled={isRegenerating}
                className={`px-2 py-1 rounded-lg text-[11px] font-medium transition-colors ${
                  selectedTone === t.id
                    ? "bg-[#3d2714] text-white shadow-xs"
                    : "text-[#5c3e21] hover:bg-[#dfcbb2]"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <button
            onClick={() => handleRegenerate(selectedTone)}
            disabled={isRegenerating}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-[#5c3e21] bg-[#eadecb] hover:bg-[#dfcbb2] transition-colors disabled:opacity-50 cursor-pointer"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isRegenerating ? "animate-spin text-amber-700" : ""}`} />
            <span>{isRegenerating ? "Rewriting AI..." : "Regenerate"}</span>
          </button>

          <button
            onClick={handleConfirm}
            disabled={isSubmitting}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 shadow-md transition-all active:scale-95 disabled:opacity-50"
          >
            <Check className="w-4 h-4" />
            <span>{isSubmitting ? "Connecting to Life Graph..." : "Confirm & Save Memory"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
